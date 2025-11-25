from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from state import AgentState

def linkedin_node(state: AgentState):
    question = state.get("generated_question")
    
    if not question:
        return {"linkedin_post": None}
        
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    
    system_prompt = """You are a viral tech influencer on LinkedIn.
    Create a LinkedIn post based on the following interview question.
    
    The post MUST follow this specific structure:
    1.  **Hook**: A catchy opening line setting the scene (e.g., "You're in an ML Engineer interview at OpenAI...").
    2.  **The Scenario**: Briefly state the interview question.
    3.  **The Trap**: "Don't answer: [Common Wrong Answer]". Explain why it's shallow.
    4.  **The Insight**: "The real bottleneck is..." or "Here's the deep dive...". Explain the core tradeoff or mechanism.
    5.  **The Hired Answer**: "The answer that gets you hired: [The Solution]".
    
    Keep it punchy, use bolding for key terms (like **Recall**, **Precision**), and use emojis sparingly but effectively.
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
    
    post_content = chain.invoke({}).content
    
    return {"linkedin_post": post_content}
