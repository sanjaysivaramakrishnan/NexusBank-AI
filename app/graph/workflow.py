"""
LangGraph Workflow
-------------------
Defines the multi-agent banking workflow using LangGraph's StateGraph.

Flow:
  START → Supervisor → (route) → Customer Agent / Risk Agent / Credit Agent → END
                     → (FINISH) → END
"""

from langgraph.graph import StateGraph, END, START
from app.agents.state import AgentState
from app.agents.supervisor import supervisor_node
from app.agents.customer import customer_agent_node
from app.agents.risk import risk_agent_node
from app.agents.credit import credit_agent_node

# Singleton compiled workflow
_workflow = None


def _route_to_agent(state: AgentState) -> str:
    """Conditional edge function: reads the 'next' field set by the supervisor
    and returns the name of the node to route to."""
    return state.get("next", "FINISH")


def create_banking_workflow():
    """Build and compile the multi-agent banking LangGraph workflow.

    Graph structure:
        ┌─────────────────────────────────────────────┐
        │                  START                       │
        └──────────────────┬──────────────────────────┘
                           │
                           ▼
        ┌─────────────────────────────────────────────┐
        │            SUPERVISOR NODE                   │
        │   (Intent classification & routing)          │
        └──────┬──────────┬──────────┬───────┬────────┘
               │          │          │       │
          customer    risk_agent  credit   FINISH
          _agent                  _agent     │
               │          │          │       │
               ▼          ▼          ▼       ▼
        ┌─────────────────────────────────────────────┐
        │                   END                        │
        └─────────────────────────────────────────────┘
    """
    workflow = StateGraph(AgentState)

    # --- Add nodes ---
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("customer_agent", customer_agent_node)
    workflow.add_node("risk_agent", risk_agent_node)
    workflow.add_node("credit_agent", credit_agent_node)

    # --- Entry point ---
    workflow.add_edge(START, "supervisor")

    # --- Conditional routing from supervisor ---
    workflow.add_conditional_edges(
        "supervisor",
        _route_to_agent,
        {
            "customer_agent": "customer_agent",
            "risk_agent": "risk_agent",
            "credit_agent": "credit_agent",
            "FINISH": END,
        },
    )

    # --- All agents terminate after responding ---
    workflow.add_edge("customer_agent", END)
    workflow.add_edge("risk_agent", END)
    workflow.add_edge("credit_agent", END)

    return workflow.compile()


def get_workflow():
    """Get or create the singleton compiled workflow instance."""
    global _workflow
    if _workflow is None:
        _workflow = create_banking_workflow()
    return _workflow
