"""
Supervisor / Orchestrator Agent
---------------------------------
Analyzes user intent and routes to the appropriate specialized agent.
This is the entry point of the multi-agent workflow.
"""

import json
import re
from langchain_core.messages import AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.agents.state import AgentState
from app.config import MODEL_NAME, GOOGLE_API_KEY

SUPERVISOR_SYSTEM_PROMPT = """You are the **Supervisor Agent** of an intelligent banking assistant system called NexusBank AI.

Your job is to analyze the customer's request and route it to the correct specialized agent. You do NOT answer banking queries yourself — you only decide which agent should handle the request.

## Available Specialized Agents

1. **customer_agent** — Handles:
   - Customer profile / account information lookups
   - Account balance inquiries
   - Transaction history queries
   - Searching customers by name
   - General account-related questions

2. **risk_agent** — Handles:
   - Fraud detection and analysis
   - Suspicious transaction investigation
   - Customer risk assessment and scoring
   - Reporting fraudulent activity
   - Security-related inquiries

3. **credit_agent** — Handles:
   - Loan eligibility checks
   - Loan status inquiries
   - Loan product information
   - EMI calculations
   - Credit-related questions

## Routing Rules

- If the query is about account balances, profiles, or transactions → **customer_agent**
- If the query mentions fraud, suspicious activity, risk, or security → **risk_agent**
- If the query is about loans, EMI, credit, eligibility, or borrowing → **credit_agent**
- If the query is ambiguous, pick the most relevant agent
- If the query is a general greeting, thank you, or goodbye → **FINISH**
- If the query is completely unrelated to banking → **FINISH**

## Response Format

Respond ONLY with a valid JSON object. No markdown code blocks. No extra text.

{"next": "customer_agent", "reasoning": "User wants to check their account balance"}

For FINISH (greetings/general):
{"next": "FINISH", "reasoning": "User is greeting", "response": "Hello! Welcome to NexusBank AI. I can help you with account information, fraud detection, and loan services. How can I assist you today?"}

## Available Test Customers (mention these if the user asks who they can look up):
- CUST001: Rajesh Kumar
- CUST002: Priya Sharma
- CUST003: Amit Patel (has suspicious transactions)
- CUST004: Sneha Reddy
- CUST005: Vikram Singh
"""


def _normalize_content(content) -> str:
    """Normalize LLM response content — handles both str and list formats."""
    if isinstance(content, list):
        # Extract text from content parts
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                parts.append(part["text"])
        return " ".join(parts) if parts else ""
    return content if isinstance(content, str) else str(content)


def _parse_routing(content) -> dict:
    """Parse the supervisor's JSON routing decision from LLM output."""
    content = _normalize_content(content).strip()

    # Remove markdown code block wrappers if present
    if content.startswith("```"):
        content = re.sub(r"```(?:json)?\s*", "", content)
        content = content.rstrip("`").strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Try to find JSON object in the response
        match = re.search(r"\{[^{}]*\}", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

    # Fallback: try keyword detection
    content_lower = content.lower()
    if any(word in content_lower for word in ["fraud", "risk", "suspicious"]):
        return {"next": "risk_agent", "reasoning": "Detected risk/fraud keywords"}
    elif any(word in content_lower for word in ["loan", "emi", "credit", "eligib"]):
        return {"next": "credit_agent", "reasoning": "Detected loan/credit keywords"}
    elif any(word in content_lower for word in ["account", "balance", "transaction", "profile"]):
        return {"next": "customer_agent", "reasoning": "Detected customer/account keywords"}
    else:
        return {
            "next": "FINISH",
            "reasoning": "Could not determine intent",
            "response": "I'm sorry, I couldn't understand your request. I can help you with:\n\n• **Account Information** — Check balances, view transactions\n• **Fraud Detection** — Analyze suspicious activity\n• **Loan Services** — Check eligibility, calculate EMI\n\nPlease try rephrasing your question.",
        }


async def supervisor_node(state: AgentState) -> dict:
    """Supervisor node: classifies intent and sets routing target."""
    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=GOOGLE_API_KEY,
        temperature=0,
    )

    messages = [SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT)] + state["messages"]

    response = await llm.ainvoke(messages)
    routing = _parse_routing(response.content)

    next_agent = routing.get("next", "FINISH")
    reasoning = routing.get("reasoning", "")

    # If FINISH, add the direct response to messages
    if next_agent == "FINISH":
        direct_response = routing.get(
            "response",
            "Hello! Welcome to NexusBank AI. I can help you with account inquiries, "
            "fraud detection, and loan services. How can I assist you today?",
        )
        return {
            "next": "FINISH",
            "routing_reasoning": reasoning,
            "messages": [AIMessage(content=direct_response, name="supervisor")],
        }

    return {
        "next": next_agent,
        "routing_reasoning": reasoning,
    }
