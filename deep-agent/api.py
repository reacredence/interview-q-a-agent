"""FastAPI application for the Interview Q&A Agent."""

import os
import asyncio
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import structlog
from dotenv import load_dotenv

from graph import create_graph
from state import AgentState

# Load environment variables
load_dotenv()

# Configure structured logging
from utils.logger import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

# Global graph instance
graph_app = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    global graph_app
    # Startup: Initialize graph
    logger.info("Initializing LangGraph application")
    graph_app = create_graph()
    logger.info("LangGraph application initialized")
    yield
    # Shutdown: Cleanup if needed
    logger.info("Shutting down")


# Create FastAPI app
app = FastAPI(
    title="Interview Q&A Agent API",
    description="API for generating interview questions using LangGraph",
    version="1.0.0",
    lifespan=lifespan
)


# Request/Response Models
class ProcessRequest(BaseModel):
    """Request model for /agent/process endpoint."""
    command: str = Field(..., description="Command name (e.g., 'interview')")
    params: Dict[str, Any] = Field(default_factory=dict, description="Command parameters")
    user_context: Dict[str, Any] = Field(default_factory=dict, description="User context information")


class ProcessResponse(BaseModel):
    """Response model for /agent/process endpoint."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    format_type: str = "interview_qa"


class HealthResponse(BaseModel):
    """Response model for /health endpoint."""
    status: str
    service: str = "interview-q-a-agent"


def _create_initial_state(topic: str) -> AgentState:
    """Create initial state for the LangGraph workflow."""
    return {
        "topic": topic,
        "iteration": 0,
        "research_queries": [],
        "papers": [],
        "selected_paper": None,
        "generated_question": None,
        "linkedin_post": None,
        "feedback": None
    }


def _format_question_response(final_state: AgentState) -> Dict[str, Any]:
    """Format the final state into the expected response format."""
    question = final_state.get("generated_question")
    
    if not question:
        return None
    
    return {
        "question": question.get("question", ""),
        "wrong_answer": question.get("wrong_answer", ""),
        "explanation": question.get("explanation", ""),
        "citation": question.get("citation", ""),
        "topic": final_state.get("topic", "")
    }


@app.post("/agent/process", response_model=ProcessResponse)
async def process_command(request: ProcessRequest):
    """
    Process a command to generate interview questions.
    
    Expected request format:
    {
        "command": "interview",
        "params": {"topic": "machine learning"},
        "user_context": {...}
    }
    """
    try:
        # Validate command
        if request.command not in ["interview", "question"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown command: {request.command}. Supported commands: interview, question"
            )
        
        # Extract topic from params
        topic = request.params.get("topic", "").strip()
        if not topic:
            raise HTTPException(
                status_code=400,
                detail="Missing required parameter: 'topic' in params"
            )
        
        logger.info(
            "Processing interview question request",
            command=request.command,
            topic=topic,
            user_id=request.user_context.get("user_id", "unknown")
        )
        
        # Check if graph is initialized
        if graph_app is None:
            logger.error("Graph application not initialized")
            raise HTTPException(
                status_code=503,
                detail="Service not ready. Graph application not initialized."
            )
        
        # Create initial state
        initial_state = _create_initial_state(topic)
        
        # Configure recursion limit (default is 25, increase for review loops)
        # Also set max iterations as a safety measure
        config = {"recursion_limit": 100}
        
        # Run the graph workflow in a thread pool to avoid blocking
        # LangGraph's invoke is synchronous, so we need to run it in executor
        loop = asyncio.get_event_loop()
        final_state = await loop.run_in_executor(
            None,
            lambda: graph_app.invoke(initial_state, config=config)
        )
        
        # Format response
        question_data = _format_question_response(final_state)
        
        if not question_data:
            # Check why it failed
            papers = final_state.get("papers", [])
            selected_paper = final_state.get("selected_paper")
            generated_question = final_state.get("generated_question")
            
            if not papers:
                error_msg = "No research papers found. Please check SERPAPI_API_KEY configuration and try again."
            elif not selected_paper:
                error_msg = "Failed to select a suitable research paper. Please try a different topic."
            elif not generated_question:
                error_msg = "Failed to generate interview question from the selected paper. Please try again."
            else:
                error_msg = "Failed to generate interview question. Please try again with a different topic."
            
            logger.warning(
                "Failed to generate question",
                topic=topic,
                papers_count=len(papers),
                has_selected_paper=bool(selected_paper),
                has_generated_question=bool(generated_question)
            )
            return ProcessResponse(
                success=False,
                error=error_msg,
                format_type="interview_qa"
            )
        
        logger.info(
            "Successfully generated interview question",
            topic=topic,
            has_question=bool(question_data.get("question"))
        )
        
        return ProcessResponse(
            success=True,
            data=question_data,
            format_type="interview_qa"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error processing command",
            error=str(e),
            exc_info=True,
            command=request.command if hasattr(request, 'command') else 'unknown'
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Check if graph is initialized
        if graph_app is None:
            return HealthResponse(
                status="unhealthy",
                service="interview-q-a-agent"
            )
        
        # Check required environment variables
        required_vars = ["OPENAI_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.warning("Missing required environment variables", missing=missing_vars)
            return HealthResponse(
                status="degraded",
                service="interview-q-a-agent"
            )
        
        return HealthResponse(
            status="healthy",
            service="interview-q-a-agent"
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthResponse(
            status="unhealthy",
            service="interview-q-a-agent"
        )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "interview-q-a-agent",
        "version": "1.0.0",
        "endpoints": {
            "process": "/agent/process",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
