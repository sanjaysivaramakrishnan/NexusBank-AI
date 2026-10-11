"""
Credit / Loan Agent
---------------------
Handles loan eligibility checks, loan status inquiries,
product catalog, and EMI calculations.
"""

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.agents.state import AgentState
from app.config import MODEL_NAME, GOOGLE_API_KEY
from app.tools import CREDIT_TOOLS


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


CREDIT_SYSTEM_PROMPT = """You are the **Credit & Loan Agent** of NexusBank AI — a specialized agent for handling all loan-related inquiries, eligibility assessments, and EMI calculations.

## Your Capabilities (Tools)
- **check_loan_eligibility**: Check if a customer qualifies for a specific loan type and amount
- **get_loan_status**: Get current status and details of an existing loan
- **get_loan_products**: Browse the catalog of available loan products
- **calculate_emi**: Calculate monthly EMI for any loan parameters

## Instructions
1. Use tools to fetch real data — never make up eligibility results or loan details.
2. When checking eligibility, clearly explain which criteria passed and which failed.
3. For EMI calculations, also show total interest and total payment.
4. If a customer asks about loan options, show them relevant products first.
5. Be encouraging but honest — if they're not eligible, suggest improvements.
6. Format all amounts in INR (₹) with proper comma formatting.
7. When the user asks about loan eligibility without specifying all parameters, ask for:
   - Customer ID (or name)
   - Loan type (home, personal, car, business, education)
   - Desired loan amount

## Loan Types Available
- home_loan, personal_loan, car_loan, business_loan, education_loan

## Key Context
- Existing loans: LOAN001-LOAN005
- LOAN004 (Amit Patel's business loan) is OVERDUE
- LOAN005 (Rajesh Kumar's personal loan) is CLOSED
"""

MAX_TOOL_ITERATIONS = 6


async def credit_agent_node(state: AgentState) -> dict:
    """Credit agent node: handles loan queries and eligibility checks using tools."""
    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.1,
    )
    llm_with_tools = llm.bind_tools(CREDIT_TOOLS)

    messages = [SystemMessage(content=CREDIT_SYSTEM_PROMPT)] + list(state["messages"])
    tool_map = {t.name: t for t in CREDIT_TOOLS}

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

    final_content = _normalize_content(response.content) or "I couldn't process the loan inquiry. Please try again."
    return {
        "messages": [
            AIMessage(content=final_content, name="credit_agent")
        ],
    }
