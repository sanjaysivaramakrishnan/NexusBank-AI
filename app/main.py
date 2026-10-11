"""
FastAPI Application
--------------------
REST API server for the multi-agent banking system.
Serves the chat endpoint and static frontend files.
"""

import logging
from uuid import uuid4
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

from app.graph.workflow import get_workflow

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory session store  (maps session_id → list of messages)
# ---------------------------------------------------------------------------
sessions: dict[str, list] = {}

# ---------------------------------------------------------------------------
# Lifespan — warm up the workflow on startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing LangGraph banking workflow...")
    get_workflow()
    logger.info("Workflow ready. NexusBank AI is online.")
    yield
    logger.info("Shutting down NexusBank AI.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="NexusBank AI — Multi-Agent Banking System",
    description="A simulated real-time banking assistant powered by multiple AI agents.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The user's message")
    session_id: str | None = Field(None, description="Session ID for conversation continuity")


class ChatResponse(BaseModel):
    session_id: str
    response: str
    agent: str
    routing_reasoning: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a user message through the multi-agent banking workflow."""
    try:
        session_id = request.session_id or str(uuid4())

        # Retrieve or initialise conversation history
        if session_id not in sessions:
            sessions[session_id] = []

        # Add user message
        sessions[session_id].append(HumanMessage(content=request.message))

        logger.info(f"[{session_id[:8]}] User: {request.message}")

        # Run the LangGraph workflow
        workflow = get_workflow()
        result = await workflow.ainvoke(
            {
                "messages": sessions[session_id],
                "next": "",
                "routing_reasoning": "",
            }
        )

        # Extract the last AI message
        all_messages = result.get("messages", [])
        ai_messages = [m for m in all_messages if hasattr(m, "name") or (hasattr(m, "type") and m.type == "ai")]

        if ai_messages:
            last_msg = ai_messages[-1]
            response_text = last_msg.content
            agent_name = getattr(last_msg, "name", None) or "supervisor"
        else:
            response_text = "I apologize, but I couldn't process your request. Please try again."
            agent_name = "supervisor"

        routing_reasoning = result.get("routing_reasoning", "")

        # Update session with the final response
        sessions[session_id] = all_messages

        logger.info(f"[{session_id[:8]}] Agent: {agent_name} | Reasoning: {routing_reasoning}")

        return ChatResponse(
            session_id=session_id,
            response=response_text,
            agent=agent_name,
            routing_reasoning=routing_reasoning,
        )

    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/api/reset")
async def reset_session(session_id: str | None = None):
    """Reset a conversation session or all sessions."""
    if session_id and session_id in sessions:
        del sessions[session_id]
        return {"message": f"Session {session_id} cleared."}
    elif session_id is None:
        sessions.clear()
        return {"message": "All sessions cleared."}
    else:
        return {"message": "Session not found."}


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "NexusBank AI",
        "agents": ["supervisor", "customer_agent", "risk_agent", "credit_agent"],
    }


# ---------------------------------------------------------------------------
# Serve static frontend
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")
