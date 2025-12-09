"""FastAPI application for the Interview Q&A Agent - JSON-RPC 2.0 Protocol."""

import os
import asyncio
from typing import Dict, Any, Optional, Union
from contextlib import asynccontextmanager
from datetime import datetime
import re

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
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


# JSON-RPC 2.0 Models
class JsonRpcRequest(BaseModel):
    """JSON-RPC 2.0 Request model."""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    method: str = Field(..., description="Method name (e.g., 'agent.chat')")
    params: Dict[str, Any] = Field(..., description="Method parameters")
    id: Union[int, str] = Field(..., description="Request ID")


class JsonRpcResult(BaseModel):
    """JSON-RPC 2.0 Result model."""
    response: str = Field(..., description="Text response to send back")
    status: str = Field(default="success", description="Status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class JsonRpcResponse(BaseModel):
    """JSON-RPC 2.0 Success Response model."""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    result: JsonRpcResult = Field(..., description="Result object")
    id: Union[int, str] = Field(..., description="Request ID")


class JsonRpcErrorDetail(BaseModel):
    """JSON-RPC 2.0 Error detail model."""
    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional error data")


class JsonRpcErrorResponse(BaseModel):
    """JSON-RPC 2.0 Error Response model."""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    error: JsonRpcErrorDetail = Field(..., description="Error object")
    id: Union[int, str, None] = Field(..., description="Request ID (null for parse errors)")


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


@app.post("/api/v1/agent")
async def handle_jsonrpc(request: JsonRpcRequest):
    """
    JSON-RPC 2.0 endpoint for agent communication.
    
    Expected request format:
    {
        "jsonrpc": "2.0",
        "method": "agent.chat",
        "params": {
            "conversation_id": "string",
            "message": "string",
            "metadata": {
                "source_interface": "string",
                "user_id": "string (optional)"
            }
        },
        "id": 1
    }
    """
    try:
        # Validate JSON-RPC version
        if request.jsonrpc != "2.0":
            return JSONResponse(
                status_code=200,
                content=JsonRpcErrorResponse(
                    jsonrpc="2.0",
                    error=JsonRpcErrorDetail(
                        code=-32600,
                        message="Invalid Request",
                        data={"detail": "jsonrpc must be '2.0'"}
                    ),
                    id=request.id
                ).model_dump()
            )
        
        # Route to method handler
        if request.method == "agent.chat":
            return await _handle_agent_chat(request)
        else:
            return JSONResponse(
                status_code=200,
                content=JsonRpcErrorResponse(
                    jsonrpc="2.0",
                    error=JsonRpcErrorDetail(
                        code=-32601,
                        message="Method not found",
                        data={"method": request.method}
                    ),
                    id=request.id
                ).model_dump()
            )
    
    except Exception as e:
        logger.error(
            "Error handling JSON-RPC request",
            error=str(e),
            exc_info=True,
            method=request.method if hasattr(request, 'method') else 'unknown'
        )
        return JSONResponse(
            status_code=200,
            content=JsonRpcErrorResponse(
                jsonrpc="2.0",
                error=JsonRpcErrorDetail(
                    code=-32603,
                    message="Internal error",
                    data={"detail": str(e)}
                ),
                id=request.id if hasattr(request, 'id') else None
            ).model_dump()
        )


async def _handle_agent_chat(request: JsonRpcRequest) -> JSONResponse:
    """Handle agent.chat method - generate interview question and PDF."""
    try:
        # Extract parameters
        params = request.params
        message = params.get("message", "").strip()
        conversation_id = params.get("conversation_id", "")
        metadata = params.get("metadata", {})
        
        # Validate required parameters
        if not message:
            return JSONResponse(
                status_code=200,
                content=JsonRpcErrorResponse(
                    jsonrpc="2.0",
                    error=JsonRpcErrorDetail(
                        code=-32602,
                        message="Invalid params",
                        data={"detail": "Missing required field: message"}
                    ),
                    id=request.id
                ).model_dump()
            )
        
        topic = message  # Use message as topic
        user_id = metadata.get("user_id", "unknown")
        source_interface = metadata.get("source_interface", "unknown")
        
        logger.info(
            "Processing interview question request",
            method=request.method,
            topic=topic,
            conversation_id=conversation_id,
            user_id=user_id,
            source_interface=source_interface
        )
        
        # Check if graph is initialized
        if graph_app is None:
            logger.error("Graph application not initialized")
            return JSONResponse(
                status_code=200,
                content=JsonRpcErrorResponse(
                    jsonrpc="2.0",
                    error=JsonRpcErrorDetail(
                        code=-32603,
                        message="Internal error",
                        data={"detail": "Service not ready. Graph application not initialized."}
                    ),
                    id=request.id
                ).model_dump()
            )
        
        # Create initial state
        initial_state = _create_initial_state(topic)
        
        # Configure recursion limit
        config = {"recursion_limit": 100}
        
        # Run the graph workflow in a thread pool to avoid blocking
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
            
            return JSONResponse(
                status_code=200,
                content=JsonRpcErrorResponse(
                    jsonrpc="2.0",
                    error=JsonRpcErrorDetail(
                        code=-32603,
                        message="Internal error",
                        data={"detail": error_msg}
                    ),
                    id=request.id
                ).model_dump()
            )
        
        # Generate PDF
        try:
            # Lazy import to avoid startup errors if WeasyPrint dependencies are missing (Windows issue)
            try:
                from utils.pdf_generator import generate_pdf
                from utils.storage import upload_file
            except (ImportError, OSError) as import_error:
                error_msg = f"PDF generation not available: {str(import_error)}"
                logger.error(
                    "Failed to import PDF generation modules",
                    error=error_msg,
                    hint="On Windows, install GTK+ runtime or use Docker. See: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows"
                )
                raise Exception(error_msg)
            
            # Create safe filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            topic_safe = re.sub(r'[^\w\s-]', '', topic).strip().replace(' ', '_')[:50]
            pdf_filename = f"interview_{topic_safe}_{timestamp}.pdf"
            
            # Generate PDF with single question
            generate_pdf([question_data], pdf_filename)
            logger.info(f"PDF generated: {pdf_filename}")
            
            # Upload to S3
            pdf_url = upload_file(pdf_filename)
            
            if pdf_url:
                logger.info(f"PDF uploaded successfully: {pdf_url}")
                
                # Clean up local file
                try:
                    if os.path.exists(pdf_filename):
                        os.remove(pdf_filename)
                except Exception as e:
                    logger.warning(f"Failed to remove local PDF file: {e}")
                
                # Return success response with PDF URL
                response_text = f"PDF generated successfully: {pdf_url}"
                
                return JSONResponse(
                    status_code=200,
                    content=JsonRpcResponse(
                        jsonrpc="2.0",
                        result=JsonRpcResult(
                            response=response_text,
                            status="success",
                            metadata={
                                "pdf_url": pdf_url,
                                "topic": topic,
                                "question_preview": question_data.get("question", "")[:100] + "..." if len(question_data.get("question", "")) > 100 else question_data.get("question", ""),
                                "conversation_id": conversation_id
                            }
                        ),
                        id=request.id
                    ).model_dump()
                )
            else:
                # PDF generation succeeded but upload failed
                logger.warning("PDF generated but upload to S3 failed")
                return JSONResponse(
                    status_code=200,
                    content=JsonRpcErrorResponse(
                        jsonrpc="2.0",
                        error=JsonRpcErrorDetail(
                            code=-32603,
                            message="Internal error",
                            data={"detail": "PDF generated but failed to upload. Please check S3 configuration."}
                        ),
                        id=request.id
                    ).model_dump()
                )
        
        except Exception as pdf_error:
            logger.error(
                "Error generating PDF",
                error=str(pdf_error),
                exc_info=True,
                topic=topic
            )
            return JSONResponse(
                status_code=200,
                content=JsonRpcErrorResponse(
                    jsonrpc="2.0",
                    error=JsonRpcErrorDetail(
                        code=-32603,
                        message="Internal error",
                        data={"detail": f"Failed to generate PDF: {str(pdf_error)}"}
                    ),
                    id=request.id
                ).model_dump()
            )
        
    except Exception as e:
        logger.error(
            "Error in agent.chat handler",
            error=str(e),
            exc_info=True
        )
        return JSONResponse(
            status_code=200,
            content=JsonRpcErrorResponse(
                jsonrpc="2.0",
                error=JsonRpcErrorDetail(
                    code=-32603,
                    message="Internal error",
                    data={"detail": str(e)}
                ),
                id=request.id
            ).model_dump()
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
    """Root endpoint - JSON-RPC 2.0 service info."""
    return {
        "service": "interview-q-a-agent",
        "version": "1.0.0",
        "protocol": "JSON-RPC 2.0",
        "endpoints": {
            "rpc": "POST /api/v1/agent",
            "health": "GET /health"
        },
        "supported_methods": [
            "agent.chat"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
