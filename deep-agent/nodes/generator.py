import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from state import AgentState
from utils.logger import get_logger

logger = get_logger(__name__)

def generator_node(state: AgentState):
    paper = state["selected_paper"]
    topic = state["topic"]
    
    logger.info("Starting question generation", topic=topic, has_paper=paper is not None)
    
    if not paper:
        logger.warning("No paper selected, cannot generate question")
        return {"generated_question": None}
    
    logger.debug("Generator state", 
                 paper_title=paper.get('title', 'Unknown'),
                 has_feedback=bool(state.get('feedback')),
                 has_existing_question=bool(state.get('generated_question')))
        
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    
    
    if state.get("feedback") and state.get("generated_question"):
        # Refinement mode
        system_prompt = """You are a Staff GenAI Engineer refining an interview question based on feedback.
        
        Original Question: {question}
        Original Wrong Answer: {wrong_answer}
        Original Explanation: {explanation}
        
        Feedback: {feedback}
        
        Refine the question to address the feedback while maintaining the required format.
        Return the output as a JSON object with keys: "question", "wrong_answer", "explanation", "citation".
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Refine the question.")
        ])
        
        chain = prompt | llm
        input_vars = {
            "question": state["generated_question"]["question"],
            "wrong_answer": state["generated_question"]["wrong_answer"],
            "explanation": state["generated_question"]["explanation"],
            "feedback": state["feedback"]
        }
    else:
        # Creation mode
        system_prompt = """You are a Staff GenAI Engineer creating a system design interview question.
        Based on the provided research paper, create a question in the following specific format:
        
        1. **The Interview Question**: A scenario-based question that tests deep understanding.
        2. **The Common Wrong Answer**: A plausible but flawed response that strong engineers might give.
        3. **How It Actually Works**: A concise technical breakdown of the solution based on the paper.
        4. **Key Paper**: The citation for the paper.
        
        The question should be difficult and reveal whether the candidate understands the nuances of the topic.
        
        Return the output as a JSON object with keys: "question", "wrong_answer", "explanation", "citation".
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", f"Topic: {topic}\n\nPaper Title: {paper['title']}\nSummary: {paper['summary']}\nURL: {paper['url']}")
        ])
        
        chain = prompt | llm
        input_vars = {}
    
    response = chain.invoke(input_vars)
    content = response.content.strip()
    
    # Clean up markdown code blocks
    if content.startswith("```json"):
        content = content[7:-3]
    elif content.startswith("```"):
        content = content[3:-3]
        
    try:
        generated_question = json.loads(content)
        logger.info("Successfully parsed JSON", has_question=bool(generated_question.get('question')))
        
        # Ensure citation includes the URL
        citation = generated_question.get('citation') or ''
        if paper['url'] not in citation:
            generated_question['citation'] = f"{paper['title']} - {paper.get('authors', 'Unknown')} ({paper['url']})"
            
        return {"generated_question": generated_question}
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON", error=str(e), content_preview=content[:500])
        return {"generated_question": None}
    except Exception as e:
        logger.error("Exception in generator", error=str(e), exc_info=True)
        return {"generated_question": None}
