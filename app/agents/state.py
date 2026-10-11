"""
Shared Agent State
-------------------
Defines the state schema used across all nodes in the LangGraph workflow.
"""

from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State that flows through the multi-agent banking workflow.

    Attributes:
        messages: Conversation message history (auto-accumulated via add_messages).
        next: The name of the next agent to route to (set by supervisor).
        routing_reasoning: Supervisor's reasoning for the routing decision.
    """

    messages: Annotated[list, add_messages]
    next: str
    routing_reasoning: str
