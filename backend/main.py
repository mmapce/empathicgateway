import asyncio
import uuid
import joblib
import logging
import re
import os
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException, status, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from contextlib import asynccontextmanager
from .models import ChatRequest, ChatResponse
from .worker import simulate_llm_processing
from transformers import pipeline
from huggingface_hub import hf_hub_download

# Import Custom Transformer Class to ensure Pickle can find it
# Hack to make the class available in __main__ scope if pickle needs it,
# although importing it from module is safer. Better to ensure train_model is available.
# Actually, joblib needs the class definition available.

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ARCHITECTURE CONSTANTS (Mutable) ---
LANE_CONFIG = {"fast_limit": 10, "normal_limit": 2}

# Lane Counters
lane_state = {"fast_active": 0, "normal_active": 0}
state_lock = asyncio.Lock()

# --- SECURITY ---
API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("API_KEY", "empathic-secret-key")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API Key"
    )


# Guardrails: PII MASKING (Hybrid: Regex + NER)
# Global State
model = None
ner_pipeline = None
executor = ThreadPoolExecutor(max_workers=1)


def get_ner_pipeline():
    global ner_pipeline
    if ner_pipeline is None:
        logger.info("⏳ Lazy Loading NER Pipeline...")
        try:
            ner_pipeline = pipeline(
                "ner", model="dslim/bert-base-NER", aggregation_strategy="simple"
            )
            logger.info("✅ NER Pipeline Loaded.")
        except Exception as e:
            logger.error(f"❌ Failed to load NER: {e}")
    return ner_pipeline


def mask_pii(text: str):
    """
    Returns: (masked_text, pii_types_list)
    """
    pii_types = []
    masked = text

    # 1. Regex-based (Structured PII)
    if re.search(r"[\w\.-]+@[\w\.-]+\.\w+", masked):
        pii_types.append("EMAIL")
        masked = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL]", masked)
    
    # Improved Credit Card: Catch 10-19 digits (allowing spaces/dashes)
    # This covers "12312 12312" (10 digits)
    if re.search(r"\b(?:\d[ -]*?){10,19}\b", masked):
        pii_types.append("CREDIT_CARD")
        masked = re.sub(r"\b(?:\d[ -]*?){10,19}\b", "[CREDIT_CARD]", masked)

    if re.search(r"\b\d{7,11}\b", masked):
        pii_types.append("ID_NUMBER")
        masked = re.sub(r"\b\d{7,11}\b", "[ID_NUMBER]", masked)

    # Improved Phone: Supports 3-4-4 (555-0199-8888) and Context-Aware
    phone_pattern = r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
    # Context-Aware Phone: "phone: 123456"
    context_phone = r"(?i)\b(?:phone|call|mobile|cell|contact)[\s\W]{0,5}(\d{6,})\b"

    if re.search(phone_pattern, masked):
        pii_types.append("PHONE")
        masked = re.sub(phone_pattern, "[PHONE]", masked)
    elif re.search(context_phone, masked):
        pii_types.append("PHONE")
        masked = re.sub(context_phone, r"\1 [PHONE]", masked) # Keep context word? No, usually redacting the number is enough.
        # Actually, let's just redact the capture group
        def repl(m): return m.group(0).replace(m.group(1), "[PHONE]")
        masked = re.sub(context_phone, repl, masked)

    # 2. NER-based (Unstructured PII: Names, Locations, Orgs)
    # Lazy Load if needed (for Notebook usage)
    nlp = get_ner_pipeline()

    if nlp:
        try:
            # CRITICAL FIX: Run NER on 'masked' (current state), not 'text' (original)
            # This prevents index misalignment if regex replacements occurred earlier.
            entities = nlp(masked)
            # Sort by start position in reverse to avoid index shifting during replacement
            entities_sorted = sorted(entities, key=lambda x: x["start"], reverse=True)

            for ent in entities_sorted:
                entity_type = (
                    ent.get("entity_group", ent.get("entity", ""))
                    .replace("B-", "")
                    .replace("I-", "")
                )
                start, end = ent["start"], ent["end"]

                # Check if we are overwriting an existing mask (heuristic)
                segment = masked[start:end]
                if "[" in segment and "]" in segment:
                    continue

                if entity_type == "PER":
                    if "PERSON" not in pii_types:
                        pii_types.append("PERSON")
                    masked = masked[:start] + "[PERSON]" + masked[end:]
                elif entity_type == "LOC":
                    if "LOCATION" not in pii_types:
                        pii_types.append("LOCATION")
                    masked = masked[:start] + "[LOCATION]" + masked[end:]
                elif entity_type == "ORG":
                    if "ORGANIZATION" not in pii_types:
                        pii_types.append("ORGANIZATION")
                    masked = masked[:start] + "[ORG]" + masked[end:]
        except Exception as e:
            logger.warning(f"NER failed: {e}")
        except Exception as e:
            logger.warning(f"NER failed: {e}")

    return masked, pii_types


# Guardrails: Prompt Injection Detection
def detect_prompt_injection(text: str) -> bool:
    """
    Heuristic check for common jailbreak patterns.
    """
    patterns = [
        r"ignore previous",
        r"ignore all",
        r"ignore.*instructions",
        r"ignore.*rules",
        r"system prompt",
        r"you are now DAN",
        r"do anything now",
        r"browse the web",
        r"delete your data",
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


# Guardrails: Output Filtering
def validate_output(text: str) -> bool:
    """
    Ensures the model/agent response is safe.
    """
    blocked_patterns = [r"hashed_password", r"private_key", r"internal_server_error"]
    for pattern in blocked_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    return True


# Global State
model = None
ner_pipeline = None
# executor is defined in global scope above, no need to redefine if not moved,
# but my previous edit put it in the block. Let's make sure it's cleaning up correctly.


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load Models
    global model, ner_pipeline

    # 1. Load Urgency Model
    logger.info("Loading Urgency Model...")
    try:
        import sys
        import backend.train_model

        sys.modules["__main__"].BertEmbedder = backend.train_model.BertEmbedder

        # Try local model first (for development)
        local_path = "backend/urgency_model.joblib"
        if os.path.exists(local_path):
            model = joblib.load(local_path)
            logger.info(f"✅ Urgency Model loaded from local file: {local_path}")
        else:
            # Fallback to Hugging Face Hub (for Cloud Run)
            logger.info(
                "📥 Local model not found, downloading from Hugging Face Hub..."
            )
            MODEL_REPO = "mmapce/empathicgateway-intent-classifier"
            MODEL_FILENAME = "urgency_model.joblib"
            CACHE_DIR = "/tmp/model_cache"
            model_path = hf_hub_download(
                repo_id=MODEL_REPO, filename=MODEL_FILENAME, cache_dir=CACHE_DIR
            )
            model = joblib.load(model_path)
            logger.info(f"✅ Urgency Model loaded from HF Hub: {model_path}")
    except Exception as e:
        logger.error(f"❌ Failed to load urgency model: {e}")

    # 2. Load NER Pipeline for PII Detection
    logger.info("Loading NER Pipeline for PII...")
    try:
        ner_pipeline = pipeline(
            "ner", model="dslim/bert-base-NER", aggregation_strategy="simple"
        )
        logger.info("✅ NER Pipeline Loaded Successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to load NER: {e}")

    yield
    executor.shutdown()


app = FastAPI(title="EmpathicGateway API", lifespan=lifespan)


# Health check endpoint for deployment
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "ner_loaded": ner_pipeline is not None,
    }


@app.post("/config", dependencies=[Depends(get_api_key)])
async def update_config(config: dict):
    # Expects {"fast_limit": 10, "normal_limit": 5}
    global LANE_CONFIG
    if "fast_limit" in config:
        LANE_CONFIG["fast_limit"] = config["fast_limit"]
    if "normal_limit" in config:
        LANE_CONFIG["normal_limit"] = config["normal_limit"]
    return {"status": "updated", "config": LANE_CONFIG}


# --- PRIORITY MAPPING ---
def map_priority(intent):
    # CRITICAL: Money related, complaints
    if intent in [
        "payment_issue",
        "get_refund",
        "track_refund",
        "complaint",
        "check_cancellation_fee",
        "fraud_report",
    ]:
        return 1
    # HIGH: Order changes, shipping, delivery
    elif intent in [
        "cancel_order",
        "change_order",
        "change_shipping_address",
        "place_order",
        "track_order",
        "delivery_options",
        "delivery_period",
    ]:
        return 2
    # NORMAL: Info, account, newsletter
    else:
        return 3


def run_inference(text: str):
    """
    CPU-bound blocking inference operation.
    """
    if not model:
        return "unknown", 3, 0.0, {}

    probs = model.predict_proba([text])[0]
    predicted_intent = model.predict([text])[0]
    max_prob = float(max(probs))

    priority = map_priority(predicted_intent)

    classes = model.classes_
    explainability = {c: float(p) for c, p in zip(classes, probs)}

    if max_prob < 0.40:
        return "uncertain", 3, max_prob, explainability

    return predicted_intent, priority, max_prob, explainability


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(get_api_key)])
async def chat_endpoint(request: ChatRequest):
    ticket_id = str(uuid.uuid4())[:8]
    loop = asyncio.get_running_loop()

    # Guardrails 1: Prompt Injection Check
    if detect_prompt_injection(request.text):
        logger.warning(
            f"🚨 [SECURITY_AUDIT] [Ticket {ticket_id}] Prompt Injection Detected! Input: {request.text}"
        )
        return ChatResponse(
            ticket_id=ticket_id,
            priority=0,
            label="BLOCKED",
            wait_time="0.0s",
            message="Request blocked by security policy (Prompt Injection Detected).",
            confidence=1.0,
            pii_detected=False,
            pii_types=[],
            intent="malicious",
            explainability={},
        )

    # Guardrails 2: PII Masking
    safe_text, pii_types = mask_pii(request.text)
    pii_detected = len(pii_types) > 0

    if pii_detected:
        logger.info(
            f"🛡️ [SECURITY_AUDIT] [Ticket {ticket_id}] PII Masked: {safe_text} | Types: {pii_types}"
        )

    # 1. CPU Offloading: Predict
    intent, priority, confidence, explainability = await loop.run_in_executor(
        executor, run_inference, safe_text
    )

    label_map = {1: "CRITICAL", 2: "HIGH", 3: "NORMAL"}
    label = label_map.get(priority, "NORMAL")

    # 2. Routing Logic...
    is_fast_lane = priority in [1, 2]
    lane_limit = (
        LANE_CONFIG["fast_limit"] if is_fast_lane else LANE_CONFIG["normal_limit"]
    )
    lane_key = "fast_active" if is_fast_lane else "normal_active"
    lane_name = "FAST LANE" if is_fast_lane else "NORMAL LANE"

    # Check Capacity (Atomic Check)
    async with state_lock:
        if lane_state[lane_key] >= lane_limit:
            logger.warning(
                f"⛔ [Ticket {ticket_id}] {lane_name} Full! ({lane_state[lane_key]}/{lane_limit})"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"{lane_name} Full",
            )
        lane_state[lane_key] += 1

    try:
        logger.info(
            f"✅ Processing in {lane_name} ({lane_state[lane_key]}/{lane_limit})"
        )
        # Simulate Processing
        llm_response = await simulate_llm_processing(request.text, ticket_id)

        # Guardrails 3: Output Filtering
        if not validate_output(llm_response):
            logger.error(
                f"🚨 [SECURITY_AUDIT] [Ticket {ticket_id}] Unsafe Output Blocked!"
            )
            llm_response = "[Response Redacted by Safety Policy]"

        return ChatResponse(
            ticket_id=ticket_id,
            priority=priority,
            label=label,
            wait_time="0.05s",
            message=f"{llm_response}",
            confidence=confidence,
            pii_detected=pii_detected,
            pii_types=pii_types,
            intent=intent,
            explainability=explainability,
        )

    except Exception as e:
        logger.error(f"Error processing ticket {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        # Release Slot
        async with state_lock:
            # Prevent negative (just in case)
            if lane_state[lane_key] > 0:
                lane_state[lane_key] -= 1


@app.get("/stats")
async def get_stats():
    return {
        "model_loaded": model is not None,
        "fast_lane_usage": f"{lane_state['fast_active']}/{LANE_CONFIG['fast_limit']}",
        "normal_lane_usage": f"{lane_state['normal_active']}/{LANE_CONFIG['normal_limit']}",
        "status": "Operational",
    }
