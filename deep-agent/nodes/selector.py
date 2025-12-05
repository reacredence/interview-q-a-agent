import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from state import AgentState
from utils.logger import get_logger

logger = get_logger(__name__)

def selector_node(state: AgentState):
    papers = state["papers"]
    topic = state["topic"]
    
    paper_count = len(papers) if papers else 0
    logger.info("Selecting paper", topic=topic, paper_count=paper_count)
    
    if not papers:
        logger.warning("No papers found, cannot select")
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
        logger.info("Successfully selected paper", title=selected_paper.get('title', 'Unknown'))
        return {"selected_paper": selected_paper}
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse JSON, falling back to first paper", error=str(e), content_preview=content[:500])
        # Fallback to first paper
        if papers:
            logger.info("Using fallback paper", title=papers[0].get('title', 'Unknown'))
            return {"selected_paper": papers[0]}
        return {"selected_paper": None}
