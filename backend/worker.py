import asyncio
import logging

logger = logging.getLogger(__name__)

async def simulate_llm_processing(text: str, ticket_id: str):
    """
    Simulates calling an external LLM (e.g. OpenAI/Gemini).
    This is an I/O bound operation, so asyncio.sleep is appropriate.
    """
    logger.info(f"🤖 [Ticket {ticket_id}] Sending to LLM...")
    
    # Simulate network latency and processing time
    # In a real app, this would be: response = await client.post(...)
    await asyncio.sleep(2.5) 
    
    return f"Response to: {text[:20]}..."
