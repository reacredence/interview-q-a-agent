from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import CommaSeparatedListOutputParser
from state import AgentState

def planner_node(state: AgentState):
    topic = state["topic"]
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    system_prompt = """You are a senior technical interviewer planning to create a deep dive interview question.
    Given a high-level topic, generate 3 specific search queries to find recent (2023-2025) research papers 
    that discuss system design patterns, failure modes, or architectural choices related to that topic.
    Focus on "Deep Learning", "LLM Systems", "Generative AI Infrastructure".
    Return only the queries, separated by commas."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Topic: {topic}")
    ])
    
    chain = prompt | llm | CommaSeparatedListOutputParser()
    
    queries = chain.invoke({"topic": topic})
    
    return {"research_queries": queries}
