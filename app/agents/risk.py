"""
Risk / Fraud Detection Agent
-------------------------------
Handles fraud analysis, risk scoring, suspicious transaction investigation,
and fraud reporting.
"""

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.agents.state import AgentState
from app.config import MODEL_NAME, GOOGLE_API_KEY
from app.tools import RISK_TOOLS


def _normalize_content(content) -> str:
    """Normalize LLM response content — handles both str and list formats."""
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                parts.append(part["text"])
        return " ".join(parts) if parts else ""
    return content if isinstance(content, str) else str(content)


RISK_SYSTEM_PROMPT = """You are the **Risk & Fraud Detection Agent** of NexusBank AI — a specialized agent for analyzing fraud, assessing risk, and investigating suspicious banking activity.

## Your Capabilities (Tools)
- **analyze_transaction_fraud**: Deep-dive fraud analysis on a specific transaction
- **get_customer_risk_score**: Calculate overall risk score for a customer
- **get_suspicious_transactions**: List flagged/suspicious transactions for an account
- **report_suspicious_activity**: File a fraud report for a transaction

## Instructions
1. Use the available tools to perform analysis — never fabricate fraud scores or risk assessments.
2. When analyzing fraud, provide clear explanations of the risk indicators found.
3. Use severity levels: CRITICAL, HIGH, MEDIUM, LOW when reporting risks.
4. Always recommend concrete next steps (e.g., block card, contact customer, escalate).
5. Be thorough but concise. Fraud analysis requires clarity and urgency.
6. If the user asks about a customer's overall risk, use `get_customer_risk_score`.
7. If asked about suspicious transactions, use `get_suspicious_transactions` with the relevant account.

## Risk Thresholds
- Fraud Score >= 0.8 → CRITICAL (immediate action required)
- Fraud Score >= 0.5 → HIGH (manual review needed)
- Fraud Score >= 0.3 → MEDIUM (enhanced monitoring)
- Fraud Score < 0.3 → LOW (normal)

## Key Context
- Customer CUST003 (Amit Patel) has several flagged transactions across ACC004 and ACC005
- Transactions from unusual locations (Nigeria, Cayman Islands, Dubai) are high-risk
- Late-night transactions (midnight to 5 AM) carry elevated risk
"""

MAX_TOOL_ITERATIONS = 6


async def risk_agent_node(state: AgentState) -> dict:
    """Risk agent node: handles fraud detection and risk analysis using tools."""
    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.1,
    )
    llm_with_tools = llm.bind_tools(RISK_TOOLS)

    messages = [SystemMessage(content=RISK_SYSTEM_PROMPT)] + list(state["messages"])
    tool_map = {t.name: t for t in RISK_TOOLS}

    # ReAct-style tool calling loop
    for _ in range(MAX_TOOL_ITERATIONS):
        response = await llm_with_tools.ainvoke(messages)

        if not response.tool_calls:
            break

        messages.append(response)
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            if tool_name in tool_map:
                try:
                    result = tool_map[tool_name].invoke(tool_args)
                except Exception as e:
                    result = f"Error executing {tool_name}: {str(e)}"
            else:
                result = f"Unknown tool: {tool_name}"

            messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"],
                )
            )

    final_content = _normalize_content(response.content) or "I couldn't complete the risk analysis. Please try again."
    return {
        "messages": [
            AIMessage(content=final_content, name="risk_agent")
        ],
    }
