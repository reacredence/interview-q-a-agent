from typing import List, Dict, TypedDict, Optional

class AgentState(TypedDict):
    topic: str
    research_queries: List[str]
    papers: List[Dict[str, str]]
    selected_paper: Optional[Dict[str, str]]
    generated_question: Optional[Dict[str, str]]
    linkedin_post: Optional[str]
    feedback: Optional[str]
    iteration: int
