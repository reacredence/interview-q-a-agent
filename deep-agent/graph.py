from langgraph.graph import StateGraph, END
from state import AgentState
from nodes.planner import planner_node
from nodes.researcher import researcher_node
from nodes.selector import selector_node
from nodes.generator import generator_node
from nodes.reviewer import reviewer_node

from nodes.linkedin import linkedin_node

def should_continue(state: AgentState):
    feedback = state.get("feedback")
    iteration = state.get("iteration", 0)
    
    if feedback == "APPROVE" or iteration >= 3:
        return "linkedin"
    else:
        return "generator"

def create_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("selector", selector_node)
    workflow.add_node("generator", generator_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("linkedin", linkedin_node)
    
    workflow.set_entry_point("planner")
    
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "selector")
    workflow.add_edge("selector", "generator")
    workflow.add_edge("generator", "reviewer")
    
    workflow.add_conditional_edges(
        "reviewer",
        should_continue,
        {
            "linkedin": "linkedin",
            "generator": "generator"
        }
    )
    
    workflow.add_edge("linkedin", END)
    
    return workflow.compile()
