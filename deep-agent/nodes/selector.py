import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from state import AgentState

def selector_node(state: AgentState):
    papers = state["papers"]
    topic = state["topic"]
    
    if not papers:
        # Fallback if no papers found
        return {"selected_paper": None}

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    system_prompt = """You are an expert researcher selecting a key paper for a technical interview question.
    Review the following list of search results (papers/articles).
    Select the one that is most suitable for creating a "Senior/Staff" level system design interview question.
    The paper should ideally discuss a specific failure mode, optimization technique, or architectural pattern.
    
    Return the output as a JSON object with the following keys:
    - title: The title of the paper/article
    - authors: The authors (if available in the summary, otherwise "Unknown")
    - summary: A brief summary of the key technical insight
    - url: The URL
    - reason: Why you selected this paper
    """
    
    papers_str = "\n\n".join([f"Title: {p['title']}\nURL: {p['url']}\nSummary: {p['summary']}" for p in papers])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", f"Topic: {topic}\n\nPapers:\n{papers_str}")
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({})
    content = response.content.strip()
    
    # Clean up markdown code blocks if present
    if content.startswith("```json"):
        content = content[7:-3]
    elif content.startswith("```"):
        content = content[3:-3]
        
    try:
        selected_paper = json.loads(content)
        return {"selected_paper": selected_paper}
    except json.JSONDecodeError:
        print(f"Failed to parse selector output: {content}")
        # Fallback to first paper
        return {"selected_paper": papers[0] if papers else None}
