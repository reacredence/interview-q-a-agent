from langchain_community.utilities import SerpAPIWrapper
from state import AgentState
from utils.logger import get_logger
import os

logger = get_logger(__name__)

def researcher_node(state: AgentState):
    queries = state["research_queries"]
    all_papers = []
    seen_urls = set()
    
    logger.info("Starting research", query_count=len(queries), queries=queries)
    
    # Check if SerpAPI key is configured
    serpapi_key = os.getenv("SERPAPI_API_KEY")
    if not serpapi_key:
        logger.error("SERPAPI_API_KEY not configured")
        return {"papers": []}
    
    # Initialize SerpAPIWrapper with explicit API key
    try:
        search = SerpAPIWrapper(serpapi_api_key=serpapi_key)
        logger.info("SerpAPIWrapper initialized", key_length=len(serpapi_key) if serpapi_key else 0)
    except Exception as e:
        logger.error("Failed to initialize SerpAPIWrapper", error=str(e), exc_info=True)
        return {"papers": []}
    
    for query in queries:
        try:
            # Strip quotes from query if present
            clean_query = query.strip().strip('"').strip("'")
            logger.info("Searching for query", query=clean_query, original=query)
            
            results = search.results(clean_query)
            
            # Debug: Log results structure
            if isinstance(results, dict):
                logger.debug("SerpAPI results structure", keys=list(results.keys()))
                # Check for error messages
                if "error" in results:
                    logger.error("SerpAPI returned error", error=results.get('error'))
                # Check for different result formats
                if "answer_box" in results:
                    logger.debug("Found answer_box in results")
                if "knowledge_graph" in results:
                    logger.debug("Found knowledge_graph in results")
            
            # Extract organic results
            organic_results = results.get("organic_results", [])
            logger.info("SerpAPI search results", query=clean_query, result_count=len(organic_results))
            
            # If no organic results, try alternative result formats
            if not organic_results and isinstance(results, dict):
                # Try other result types
                if "answer_box" in results:
                    answer = results.get("answer_box", {})
                    if answer:
                        logger.debug("Found answer_box result")
                if "knowledge_graph" in results:
                    kg = results.get("knowledge_graph", {})
                    if kg:
                        logger.debug("Found knowledge_graph result")
            
            for result in organic_results[:3]: # Limit to top 3 per query
                url = result.get("link")
                if url and url not in seen_urls:
                    all_papers.append({
                        "title": result.get("title", "No Title"),
                        "url": url,
                        "summary": result.get("snippet", "No summary available.")
                    })
                    seen_urls.add(url)
                    logger.debug("Added paper", title=result.get('title', 'No Title'), url=url)
                    
        except Exception as e:
            logger.error("Error searching for query", query=query, error=str(e), exc_info=True)
    
    logger.info("Research complete", total_papers=len(all_papers))
    return {"papers": all_papers}
