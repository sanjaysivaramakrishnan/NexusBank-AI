"""
Customer Agent
----------------
Handles customer profile lookups, account balance inquiries,
transaction history, and general account questions.
"""

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.agents.state import AgentState
from app.config import MODEL_NAME, GOOGLE_API_KEY
from app.tools import CUSTOMER_TOOLS


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


CUSTOMER_SYSTEM_PROMPT = """You are the **Customer Agent** of NexusBank AI — a specialized banking assistant that handles customer profiles, account information, and transaction history.

## Your Capabilities (Tools)
- **get_customer_profile**: Look up customer details by customer ID
- **get_account_balance**: Check balance for a specific account
- **get_account_details**: Get full details of a bank account
- **get_transaction_history**: View recent transactions for an account
- **search_customer_by_name**: Find customers by name (when ID is unknown)

## Instructions
1. Use the available tools to fetch real data before responding.
2. ALWAYS use tools — never make up account numbers, balances, or transaction data.
3. If the user provides a customer name instead of ID, use `search_customer_by_name` first.
4. Present financial data clearly with proper formatting.
5. Be helpful, professional, and concise.
6. If a customer has multiple accounts, mention all of them.
7. Format currency amounts in Indian Rupees (₹) with commas.

## Available Test Customers
- CUST001: Rajesh Kumar (Accounts: ACC001, ACC002)
- CUST002: Priya Sharma (Account: ACC003)
- CUST003: Amit Patel (Accounts: ACC004, ACC005)
- CUST004: Sneha Reddy (Account: ACC006)
- CUST005: Vikram Singh (Account: ACC007)
"""

MAX_TOOL_ITERATIONS = 6


async def customer_agent_node(state: AgentState) -> dict:
    """Customer agent node: handles account/profile/transaction queries using tools."""
    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.1,
    )
    llm_with_tools = llm.bind_tools(CUSTOMER_TOOLS)

    # Build message list with system prompt
    messages = [SystemMessage(content=CUSTOMER_SYSTEM_PROMPT)] + list(state["messages"])

    # Tool map for execution
    tool_map = {t.name: t for t in CUSTOMER_TOOLS}

    # ReAct-style tool calling loop
    for _ in range(MAX_TOOL_ITERATIONS):
        response = await llm_with_tools.ainvoke(messages)

        # If no tool calls, we have the final answer
        if not response.tool_calls:
            break

        # Execute each tool call
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

    final_content = _normalize_content(response.content) or "I couldn't retrieve the requested information. Please try again."
    return {
        "messages": [
            AIMessage(content=final_content, name="customer_agent")
        ],
    }

