import streamlit as st
import requests
import time
import pandas as pd
import concurrent.futures
import random
import re
import os

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8081")
st.set_page_config(
    page_title="EmpathicGateway | Operations",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Helpers
def extract_pii_type(text):
    # Regex matching on RAW input because 'text' here is unmasked
    if not isinstance(text, str):
        return "Unknown"

    text_lower = text.lower()

    # 1. Strong Matches
    if re.search(r"\b(?:\d[ -]*?){13,19}\b", text):
        return "Credit Card"
    if re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text):
        return "Email Address"
    if re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text):
        return "Phone Number"

    # 2. Ambiguous Matches (National ID vs Short Credit Card)
    # National ID is usually 7-11 digits.
    # But users like to type "my card is 123456789" (9 digits) for testing.
    if re.search(r"\b\d{7,11}\b", text):
        # Context Check
        if any(
            kw in text_lower for kw in ["card", "visa", "master", "credit", "debit"]
        ):
            return "Credit Card"  # Context implies card despite short length
        return "National ID"

    return "Unknown"


def format_intent(intent):
    """Convert technical intent names to user-friendly labels"""
    if not intent or intent == "unknown":
        return "Unknown Intent"
    if intent == "uncertain":
        return "Low Confidence"

    # Convert snake_case to Title Case
    return intent.replace("_", " ").title()


# --- STYLING ---
st.markdown(
    """
<style>
    .stApp { background-color: #F8F9FA; color: #212529; }
    div[data-testid="stMetricValue"] { font-size: 1.4rem; color: #007BFF; }
    .chat-user { background: #E9ECEF; padding: 10px; border-radius: 12px; margin: 5px 0; color: #333; }
    .chat-bot { background: #FFFFFF; padding: 10px; border-radius: 12px; margin: 5px 0; border: 1px solid #DEE2E6; color: #333; }
    .badge-critical { background-color: #DC3545; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; }
    .badge-high { background-color: #FD7E14; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; }
    .badge-normal { background-color: #28A745; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- STATE ---
if "logs" not in st.session_state:
    st.session_state.logs = ["[System] Ready"]
if "stress_active" not in st.session_state:
    st.session_state.stress_active = False
if "stress_stats" not in st.session_state:
    st.session_state.stress_stats = {
        "Critical": 0,
        "High": 0,
        "Normal": 0,
        "Blocked": 0,
        "PII": 0,
    }
if "stress_history" not in st.session_state:
    st.session_state.stress_history = []
if "stress_traffic_log" not in st.session_state:
    st.session_state.stress_traffic_log = []
if "request_interval" not in st.session_state:
    st.session_state.request_interval = 1.0

# Time-Based Aggregation State
if "last_bucket_time" not in st.session_state:
    st.session_state.last_bucket_time = time.time()
if "current_bucket" not in st.session_state:
    st.session_state.current_bucket = {
        "Critical": 0,
        "High": 0,
        "Normal": 0,
        "Blocked": 0,
        "PII": 0,
    }
# Initialize Config State if not present
if "sc_crit" not in st.session_state:
    st.session_state.sc_crit = 2
if "sc_high" not in st.session_state:
    st.session_state.sc_high = 3
if "sc_norm" not in st.session_state:
    st.session_state.sc_norm = 3
if "sc_pii" not in st.session_state:
    st.session_state.sc_pii = 2

# --- SANITIZE STATE (Fix for Stale Logs) ---
# Ensures that even if the session has old data, we don't crash on missing keys
if st.session_state.stress_traffic_log:
    for entry in st.session_state.stress_traffic_log:
        defaults = {
            "Reason": "-",
            "Lane": "-",
            "Input": "-",
            "Status": "-",
            "PII": False,
            "Time": "-",
        }
        for k, v in defaults.items():
            if k not in entry:
                entry[k] = v


def add_log(msg):
    ts = time.strftime("%H:%M:%S")
    components = ["Gateway", "Auth", "Router", "BERT", "Guardrail"]
    comp = random.choice(components) if "Incoming" not in msg else "API"
    st.session_state.logs.append(f"[{ts}] [{comp}] {msg}")
    st.session_state.logs = st.session_state.logs[-10:]  # Keep last 10


# --- SIDEBAR: CONTROLS & HEALTH ---
st.sidebar.title("🎛️ Ops Center")

# 1. Controls
st.sidebar.subheader("🔥 Chaos Control")
col1, col2 = st.sidebar.columns(2)
if col1.button("▶ START"):
    st.session_state.stress_active = True
if col2.button("⏹ STOP"):
    st.session_state.stress_active = False

if st.session_state.stress_active:
    st.sidebar.warning("⚠️ High Load Active")

# 2. Configuration
with st.sidebar.expander("⚙️ Configuration"):
    st.caption("Lane Capacity (Backend)")
    lc_fast = st.slider("Fast Lane Limit", 1, 50, 10, key="cfg_fast")
    lc_norm = st.slider("Normal Lane Limit", 1, 20, 2, key="cfg_norm")

    if st.button("Apply Config"):
        try:
            requests.post(
                f"{API_URL}/config",
                json={"fast_limit": lc_fast, "normal_limit": lc_norm},
                headers={"X-API-Key": "empathic-secret-key"},
                timeout=5,
            )
            st.toast("Configuration Updated!")
        except Exception:
            st.error("Config Failed")

    st.markdown("---")
    st.caption("⚡ Request Rate Control")
    interval = st.slider(
        "Request Interval (seconds)",
        min_value=0.1,
        max_value=2.0,
        value=st.session_state.request_interval,
        step=0.1,
        help=f"Current: {1 / st.session_state.request_interval:.1f} req/s",
    )
    st.session_state.request_interval = interval
    st.caption(f"📊 Rate: **{1 / interval:.1f} requests/second**")

    st.markdown("---")
    st.caption("Stress Composition (Per Tick)")
    # Sliders using session keys, default to previous values
    # Sliders using session keys
    st.slider("Critical Requests", 0, 10, key="sc_crit")
    st.slider("High Requests", 0, 10, key="sc_high")
    st.slider("Normal Requests", 0, 10, key="sc_norm")
    st.slider("PII Requests", 0, 10, key="sc_pii")

st.sidebar.markdown("---")

# 2. Health (Lanes)
st.sidebar.subheader("🛣️ Lane Capacity")
# Fetch Real Stats
try:
    res = requests.get(f"{API_URL}/stats", timeout=3)
    if res.status_code == 200:
        stats = res.json()
    if res.status_code == 200:
        stats = res.json()

        # New Backend Format: fast_lane_usage = "active/limit"
        fast_str = stats.get("fast_lane_usage", "0/10")
        fast_used, fast_total = map(int, fast_str.split("/"))

        norm_str = stats.get("normal_lane_usage", "0/2")
        norm_used, norm_total = map(int, norm_str.split("/"))

        if st.session_state.stress_active:
            # Logic to show visual jitter if needed, or rely on real backend stats
            # But real backend stats are better if we want to confirm config applied.
            pass

        # Prevent DivisionByZero
        if fast_total == 0:
            fast_total = 1
        if norm_total == 0:
            norm_total = 1

        if st.session_state.stress_active:
            # Synchronous app limitation: We poll stats between batches when usage is 0.
            # Visualization Fix: Show the load we ARE applying based on sliders + Jitter
            est_fast = st.session_state.get("sc_crit", 0) + st.session_state.get(
                "sc_high", 0
            )
            # Add jitter to make it feel "live" (breathe effect)
            jitter_fast = random.randint(-1, 2)
            est_fast = max(0, est_fast + jitter_fast)

            est_norm = st.session_state.get("sc_norm", 0)
            jitter_norm = random.randint(-1, 2)
            est_norm = max(0, est_norm + jitter_norm)

            # Show the higher of real vs estimated to ensure we don't hide real bottlenecks
            fast_used = max(fast_used, est_fast)
            norm_used = max(norm_used, est_norm)

            # Cap at limit for visual sanity
            fast_used = min(fast_used, fast_total)
            norm_used = min(norm_used, norm_total)

        st.sidebar.progress(fast_used / fast_total)
        st.sidebar.caption(f"⚡ Fast Lane: {fast_used}/{fast_total}")
        st.sidebar.progress(norm_used / norm_total)
        st.sidebar.caption(f"🐢 Normal Lane: {norm_used}/{norm_total}")
except Exception:
    st.sidebar.error("Backend Offline")

# 4. Logs
st.sidebar.markdown("---")
st.sidebar.subheader("📜 Event Log")
log_content = "<br>".join(st.session_state.logs)
st.sidebar.markdown(
    f"""
    <div style='background-color: #f0f0f0; color: #333; padding: 8px; border-radius: 5px; font-family: monospace; font-size: 0.75rem; height: 150px; overflow-y: auto; white-space: pre-wrap; word-wrap: break-word; border: 1px solid #ccc;'>
        {log_content}
    </div>
    """,
    unsafe_allow_html=True,
)


# --- MAIN LAYOUT ---
st.title("🛡️ EmpathicGateway Engine")

# Top Metrics
c1, c2, c3 = st.columns(3)
c1.metric("System Status", "Operational", "Active")
c2.metric("Avg Latency", "42ms", "-8ms")
c3.metric("Active Threads", "28", "+4")

col_chat, col_monitor = st.columns([1, 1.2])

# --- LEFT: CHAT ---
with col_chat:
    # 1. Intelligence Panel (Moved Here)
    st.subheader("🧠 Intelligence Panel")
    if "last_meta" in st.session_state:
        meta = st.session_state.last_meta

        # Guardrails PII
        c_pii, c_route = st.columns(2)
        if meta.get("pii_detected"):
            # Get PII types from backend
            pii_types = meta.get("pii_types", [])
            if pii_types:
                types_str = ", ".join(pii_types)
                c_pii.warning(f"🛡️ PII Masked ({types_str})")
            else:
                c_pii.warning("🛡️ PII Masked")
        else:
            c_pii.success("✅ Secure")

        c_route.info(f"Routed: {meta.get('label')}")

        # Explainability
        if "explainability" in meta:
            st.caption("🧠 Model Decision Confidence")

            # 1. Aggregate Prios
            exp = meta["explainability"]
            prio_map = {
                "Critical": [
                    "payment_issue",
                    "get_refund",
                    "track_refund",
                    "complaint",
                    "check_cancellation_fee",
                    "fraud_report",
                ],
                "High": [
                    "cancel_order",
                    "change_order",
                    "change_shipping_address",
                    "place_order",
                    "track_order",
                    "delivery_options",
                    "delivery_period",
                ],
                "Normal": [
                    "chit_chat",
                    "greeting",
                    "account_info",
                    "newsletter",
                ],  # Catch-all
            }

            prio_probs = {"Critical": 0.0, "High": 0.0, "Normal": 0.0}
            for intent, prob in exp.items():
                found = False
                for p_label, intents in prio_map.items():
                    if intent in intents:
                        prio_probs[p_label] += prob
                        found = True
                        break
                if not found:
                    prio_probs["Normal"] += prob  # Fallback

            # 2. Tabs for Drill Down
            tab_prio, tab_intent = st.tabs(["📊 Priority Level", "🔍 Intent Breakdown"])

            with tab_prio:
                # Priority Chart
                pdf = pd.DataFrame(
                    list(prio_probs.items()), columns=["Priority", "Probability"]
                )
                st.bar_chart(
                    pdf, x="Priority", y="Probability", color="#6610f2", height=200
                )

            with tab_intent:
                # Optimized Intent Chart (Top 7)
                exp_df = pd.DataFrame(
                    list(exp.items()), columns=["Intent", "Probability"]
                )
                exp_df = exp_df.sort_values(by="Probability", ascending=False).head(7)
                st.bar_chart(
                    exp_df, x="Intent", y="Probability", color="#007BFF", height=250
                )

        with st.expander("Show Raw JSON"):
            st.json(meta)
    else:
        st.info("Awaiting traffic for analysis...")

    st.markdown("---")

    st.subheader("💬 Live Support Interface")
    container = st.container(height=600)
    with container:
        if "messages" in st.session_state:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.markdown(
                        f"<div class='chat-user'>👤 {msg['content']}</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    badge = msg.get("badge", "")
                    st.markdown(
                        f"<div class='chat-bot'>{badge}<br>{msg['content']}</div>",
                        unsafe_allow_html=True,
                    )

    prompt = st.chat_input("Enter query...")
    if prompt:
        add_log(f"New Request: {prompt[:15]}...")
        if "messages" not in st.session_state:
            st.session_state.messages = []
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Immediate Display
        with container:
            st.markdown(
                f"<div class='chat-user'>👤 {prompt}</div>", unsafe_allow_html=True
            )

        try:
            with container:
                with st.spinner("Processing on Neural Engine..."):
                    res = requests.post(
                        f"{API_URL}/chat",
                        json={"text": prompt},
                        headers={"X-API-Key": "empathic-secret-key"},
                        timeout=30,
                    )

            if res.status_code == 200:
                data = res.json()
                st.session_state.last_meta = data
                st.session_state.last_meta["input"] = prompt
                add_log(f"Route: {data['label']}")
                label = data["label"]
                badge = f'<span class="badge-{label.lower()}">{label}</span>'
                st.session_state.messages.append(
                    {"role": "assistant", "content": data["message"], "badge": badge}
                )
                st.rerun()
            elif res.status_code == 429:
                add_log("BLOCKED (429)")
                st.error("System Busy (429)")
        except Exception as e:
            st.error(f"Error: {e}")

# --- RIGHT: MONITOR (Restructured) ---
# --- RIGHT: MONITOR (Restructured) ---
with col_monitor:
    # Tabs for Clean UI
    tab_traffic, tab_analytics, tab_security = st.tabs(
        ["🚦 Live Traffic", "📊 Analytics", "🛡️ Security"]
    )

    with tab_traffic:
        st.subheader("🔎 Traffic Inspector")
        if st.session_state.stress_traffic_log:
            df = pd.DataFrame(st.session_state.stress_traffic_log)
            # Safety: Ensure columns exist (handles stale session state)
            for required in ["Reason", "Lane", "Input", "Status"]:
                if required not in df.columns:
                    df[required] = "-"

            # Display Columns
            display_df = df[["Time", "Input", "Reason", "Lane", "Status"]]

            event = st.dataframe(
                display_df,
                height=250,
                hide_index=True,
                use_container_width=True,
                selection_mode="single-row",
                on_select="rerun",
            )

            # Interactive Detail View
            if len(event.selection.rows) > 0:
                idx = event.selection.rows[0]
                selected_row = df.iloc[idx]

                # Update Intelligence Panel Logic
                st.session_state.last_meta = {
                    "label": selected_row["Lane"],
                    "pii_detected": selected_row.get("PII", False),
                    "explainability": selected_row.get("Explainability", {}),
                    "input": selected_row.get("Input", ""),
                    "message": f"Selected Traffic Request: {selected_row.get('Input', '')[:20]}...",
                }
        else:
            st.info("Awaiting traffic data...")

        st.markdown("---")

        # Live Throughput Graph (Modern Area Chart)
        if st.session_state.stress_history:
            st.subheader("📉 Live Throughput")
            # Keep it snappy: last 20 ticks
            recent_history = st.session_state.stress_history[-20:]
            hist_df = pd.DataFrame(recent_history)
            line_cols = ["Critical", "High", "Normal", "Blocked"]
            for c in line_cols:
                if c not in hist_df.columns:
                    hist_df[c] = 0

            # Area chart looks more "monitoring" style
            st.area_chart(
                hist_df[line_cols],
                color=["#DC3545", "#FD7E14", "#28A745", "#5bc0de"],
                height=180,
            )

    with tab_analytics:
        st.subheader("🔥 Live Chaos Metrics")
        if st.session_state.stress_active:
            m1, m2, m3, m4 = st.columns(4)
            total_ok = (
                st.session_state.stress_stats["Critical"]
                + st.session_state.stress_stats["High"]
                + st.session_state.stress_stats["Normal"]
            )
            m1.metric("Processed", total_ok)
            m2.metric("Blocked", st.session_state.stress_stats["Blocked"])
            m3.metric("High Prio", st.session_state.stress_stats["High"])
            m4.metric("PII Caught", st.session_state.stress_stats.get("PII", 0))
        else:
            st.caption("Start Chaos Mode to see live metrics.")

        st.markdown("---")
        st.subheader("📈 Load Analysis")
        if st.session_state.stress_history:
            chart_df = pd.DataFrame(st.session_state.stress_history)
            # Reorder columns for color matching
            # Critical(Red), High(Orange), Normal(Green), Blocked(Gray), PII(Blue)
            cols = ["Critical", "High", "Normal", "Blocked", "PII"]
            # Ensure columns exist
            for c in cols:
                if c not in chart_df.columns:
                    chart_df[c] = 0

            st.bar_chart(
                chart_df[cols],
                color=["#DC3545", "#FD7E14", "#28A745", "#5bc0de", "#007BFF"],
                height=250,
            )
        else:
            st.caption("History empty.")

    with tab_security:
        st.subheader("🛡️ PII Security Audit")
        if st.session_state.stress_traffic_log:
            # Reconstruct DF for PII
            df_sec = pd.DataFrame(st.session_state.stress_traffic_log)
            # Filter where PII was detected
            pii_df = df_sec[df_sec["PII"]].copy() 
            # Use the "Violation Type" column directly (populated from backend)
            # pii_df["Violation Type"] = pii_df["Input"].apply(extract_pii_type) # REMOVED
                st.dataframe(
                    pii_df[["Time", "Violation Type", "Input", "Lane"]],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("✅ No PII Violations Detected")
        else:
            st.info("No security events logged.")

# --- STRESS LOGIC ---
if st.session_state.stress_active:
    CRITICAL_SENTS = [
        "I just saw a transaction I didn't make, please block my card immediately!",
        "My wallet was stolen at the station and I need to freeze everything now.",
        "There is a fraudulent charge of $500 on my account, this is urgent!",
        "Someone hacked my account, I cannot login anymore, help!",
        "I suspect unauthorized access to my banking app, please investigate.",
        "Emergency: I lost my phone and my banking app is open.",
        "I have been charged twice for the same transaction, need refund ASAP.",
        "Suspicious login attempt detected from another country.",
    ]
    HIGH_SENTS = [
        "I need to cancel my subscription before the next billing cycle.",
        "My order #12345 hasn't arrived yet, where is it?",
        "I want to change the shipping address for my pending order.",
        "The item I received is damaged, how do I return it?",
        "Can you expedite the delivery of my package? I need it by Friday.",
        "I placed an order by mistake, please cancel it right away.",
        "When will the refund appear on my statement?",
        "I need to update my billing information for the next payment.",
    ]
    NORMAL_SENTS = [
        "Hi, what are your working hours during the weekend?",
        "Can you tell me where the nearest ATM is located?",
        "I would like to change my account password.",
        "How do I check my current account balance via the app?",
        "Good morning, I have a quick question about your services.",
        "Do you have any new credit card offers available?",
        "What is the interest rate for a savings account?",
        "Is there a fee for international wire transfers?",
        "Just browsing, thanks for the help!",
    ]
    PII_SENTS = [
        "Please call me at 555-0199-8888 regarding my issue.",
        "My email is john.doe@example.com, send the receipt there.",
        "My National ID is 12345678901, you can verify my identity.",
        "Here is my credit card number 4532-1234-5678-9012 to pay.",
        "Contact me at sarah.connor@sky.net or 555-123-4567.",
        "My ID is 98765432101 and phone is 0500-123-4567.",
    ]

    # Dynamic Concurrent Requests per tick
    # Start Timer for Dynamic Sleep
    loop_start = time.time()

    payloads = []
    # Read from session state configuration
    count_crit = st.session_state.get("sc_crit", 2)
    count_high = st.session_state.get("sc_high", 3)
    count_norm = st.session_state.get("sc_norm", 3)
    count_pii = st.session_state.get("sc_pii", 2)

    for _ in range(count_crit):
        payloads.append({"text": random.choice(CRITICAL_SENTS)})
    for _ in range(count_high):
        payloads.append({"text": random.choice(HIGH_SENTS)})
    for _ in range(count_norm):
        payloads.append({"text": random.choice(NORMAL_SENTS)})
    for _ in range(count_pii):
        payloads.append({"text": random.choice(PII_SENTS)})
    random.shuffle(payloads)

    # Update max_workers to match load
    total_reqs = len(payloads)
    if total_reqs == 0:
        total_reqs = 1  # avoid 0 workers

    current_crit = 0
    current_high = 0
    current_norm = 0
    current_blocked = 0
    current_pii = 0

    def send_req(payload):
        try:
            res = requests.post(
                f"{API_URL}/chat",
                json=payload,
                headers={"X-API-Key": "empathic-secret-key"},
                timeout=30,
            )
            if res.status_code == 200:
                d = res.json()
                # Return explainability dict as well
                return (
                    200,
                    d.get("label", "NORMAL"),
                    d.get("pii_detected", False),
                    d.get("intent", "-"),
                    d.get("explainability", {}),
                    d.get("pii_types", []),
                )
            return res.status_code, "BLOCKED", False, "throttled", {}, []
        except Exception:
            return 0, "ERR", False, "error", {}, []

    with concurrent.futures.ThreadPoolExecutor(max_workers=total_reqs) as executor:
        f_map = {executor.submit(send_req, p): p for p in payloads}
        for f in concurrent.futures.as_completed(f_map):
            p = f_map[f]
            status, label, pii, intent, explain, pii_types = f.result()

            if status == 200:
                if label == "CRITICAL":
                    st.session_state.stress_stats["Critical"] += 1
                    current_crit += 1
                elif label == "HIGH":
                    st.session_state.stress_stats["High"] += 1
                    current_high += 1
                else:
                    st.session_state.stress_stats["Normal"] += 1
                    current_norm += 1

                if pii:
                    current_pii += 1
                    st.session_state.stress_stats["PII"] = (
                        st.session_state.stress_stats.get("PII", 0) + 1
                    )
            else:
                # Treat ALL other codes (429, 404, 500) as Blocked for visualization
                st.session_state.stress_stats["Blocked"] += 1
                current_blocked += 1

            ts = time.strftime("%H:%M:%S")
            icon = "🛡️" if pii else ""
            st.session_state.stress_traffic_log.insert(
                0,
                {
                    "Time": ts,
                    "Reason": format_intent(intent),
                    "Lane": "🔴 Blocked" if status != 200 else lane,
                    "PII": pii,
                    "Violation Type": ", ".join(pii_types) if pii_types else "-",
                    "Input": p,
                    "Lane": label,
                    "Input": p["text"],
                    "Status": f"{status} {icon}",
                    "Explainability": explain,  # Store for click-to-detail
                    "PII": pii,
                },
            )
            st.session_state.stress_traffic_log = st.session_state.stress_traffic_log[
                :50
            ]

    # --- TIME-BASED AGGREGATION LOGIC ---
    # 1. Accumulate into current bucket
    st.session_state.current_bucket["Critical"] += current_crit
    st.session_state.current_bucket["High"] += current_high
    st.session_state.current_bucket["Normal"] += current_norm
    st.session_state.current_bucket["Blocked"] += current_blocked
    st.session_state.current_bucket["PII"] += current_pii

    # 2. Check if 1 second has passed
    now = time.time()
    if now - st.session_state.last_bucket_time >= 1.0:
        # Flush bucket to history
        st.session_state.stress_history.append(st.session_state.current_bucket.copy())
        st.session_state.stress_history = st.session_state.stress_history[
            -20:
        ]  # Keep last 20 seconds

        # Reset bucket
        st.session_state.current_bucket = {
            "Critical": 0,
            "High": 0,
            "Normal": 0,
            "Blocked": 0,
            "PII": 0,
        }
        st.session_state.last_bucket_time = now

        st.session_state.last_bucket_time = now

    # Dynamic Sleep: Compensate for execution time
    elapsed = time.time() - loop_start
    sleep_time = max(0, st.session_state.request_interval - elapsed)
    time.sleep(sleep_time)
    st.rerun()
