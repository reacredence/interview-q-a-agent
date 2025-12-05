from langgraph.graph import StateGraph, END
from state import AgentState
from nodes.planner import planner_node
from nodes.researcher import researcher_node
from nodes.selector import selector_node
from nodes.generator import generator_node
from nodes.reviewer import reviewer_node
from utils.logger import get_logger

from nodes.linkedin import linkedin_node

logger = get_logger(__name__)

def should_continue(state: AgentState):
    feedback = state.get("feedback", "")
    iteration = state.get("iteration", 0)
    
    # Ensure iteration is an integer
    if not isinstance(iteration, int):
        iteration = 0
    
    logger.debug("Checking continuation condition", 
                 iteration=iteration, 
                 feedback_preview=feedback[:100] if feedback else None)
    
    # Safety check: Always stop after max iterations (3)
    # This should prevent infinite loops
    if iteration >= 3:
        logger.info("Max iterations reached, forcing stop", iteration=iteration)
        return "linkedin"
    
    # Check if feedback contains "APPROVE" (case-insensitive, handles variations)
    if feedback:
        feedback_str = str(feedback).upper().strip()
        # Check for explicit approval
        is_approved = (
            feedback_str == "APPROVE" or 
            feedback_str.startswith("APPROVE") or
            "APPROVE" in feedback_str.split()[:2]  # Check first two words
        )
        
        if is_approved:
            logger.info("Question approved, stopping")
            return "linkedin"
    
    # Check if we have a valid question to refine
    if not state.get("generated_question"):
        logger.warning("No question generated, stopping to avoid infinite loop")
        return "linkedin"
    
    # Continue to generator for refinement
    logger.debug("Continuing to generator for refinement", iteration=iteration)
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
