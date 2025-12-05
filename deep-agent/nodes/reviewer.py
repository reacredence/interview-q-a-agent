from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from state import AgentState
from utils.logger import get_logger

logger = get_logger(__name__)

def reviewer_node(state: AgentState):
    question = state["generated_question"]
    
    if not question:
        return {"feedback": "Failed to generate question."}
        
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    system_prompt = """You are a Bar Raiser at a top tech company reviewing an interview question.
    Critique the following question for depth, clarity, and correctness.
    
    Is it a "Senior/Staff" level question?
    Does the "Common Wrong Answer" sound realistic?
    Is the "How It Actually Works" section technically accurate based on general knowledge?
    
    If it is good, return "APPROVE".
    If it needs improvement, provide specific feedback on what to change.
    """
    
    q_str = f"""
    Question: {question['question']}
    Wrong Answer: {question['wrong_answer']}
    Explanation: {question['explanation']}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", q_str)
    ])
    
    chain = prompt | llm
    
    feedback = chain.invoke({}).content
    
    # Increment iteration (ensure it's an integer)
    current_iteration = state.get("iteration", 0)
    if not isinstance(current_iteration, int):
        current_iteration = 0
    
    new_iteration = current_iteration + 1
    logger.info("Review complete", 
                current_iteration=current_iteration, 
                new_iteration=new_iteration,
                feedback_preview=feedback[:200] if feedback else None)
    
    return {"feedback": feedback, "iteration": new_iteration}
