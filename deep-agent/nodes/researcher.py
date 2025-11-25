from langchain_community.utilities import SerpAPIWrapper
from state import AgentState

def researcher_node(state: AgentState):
    queries = state["research_queries"]
    all_papers = []
    seen_urls = set()
    
    # Initialize SerpAPIWrapper
    search = SerpAPIWrapper()
    
    for query in queries:
        try:
            # SerpAPIWrapper.run returns a string, but we want structured results if possible.
            # However, the basic run method returns a string summary.
            # To get results, we can use search.results(query) if available or just use the tool interface.
            # Let's use the `results` method if we want structured data, but the wrapper exposes `run`.
            # Actually, `SerpAPIWrapper` has a `results` method that returns a dict.
            
            results = search.results(query)
            
            # Extract organic results
            organic_results = results.get("organic_results", [])
            
            for result in organic_results[:3]: # Limit to top 3 per query
                url = result.get("link")
                if url and url not in seen_urls:
                    all_papers.append({
                        "title": result.get("title", "No Title"),
                        "url": url,
                        "summary": result.get("snippet", "No summary available.")
                    })
                    seen_urls.add(url)
                    
        except Exception as e:
            print(f"Error searching for {query}: {e}")
            
    return {"papers": all_papers}
