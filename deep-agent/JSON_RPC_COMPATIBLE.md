# Deep Agent - JSON-RPC 2.0 Compatible Agent

## Overview

The **Deep Agent** (Interview Q&A Agent) implements **JSON-RPC 2.0 Protocol**, designed to seamlessly integrate with LangChain/LangGraph agent routers. This document explains how to use it as a JSON-RPC 2.0 compatible agent.

## What is JSON-RPC 2.0?

JSON-RPC 2.0 is a stateless, light-weight remote procedure call (RPC) protocol. It uses JSON for data exchange and defines a standardized request/response format for method calls.

## JSON-RPC 2.0 Compliance ✅

The Deep Agent implements all required JSON-RPC 2.0 protocol features:

### ✅ Required Endpoints

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/agent` | POST | JSON-RPC 2.0 endpoint | ✅ Implemented |
| `/health` | GET | Health check | ✅ Implemented |

### ✅ Standard Request/Response Format

**Request Schema:**
```json
{
  "jsonrpc": "2.0",
  "method": "agent.chat",
  "params": {
    "conversation_id": "string",
    "message": "machine learning",
    "metadata": {
      "source_interface": "string",
      "user_id": "string (optional)"
    }
  },
  "id": 1
}
```

**Success Response Schema:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "response": "PDF generated successfully: https://...",
    "status": "success",
    "metadata": {
      "pdf_url": "https://...",
      "topic": "machine learning",
      "question_preview": "...",
      "conversation_id": "string"
    }
  },
  "id": 1
}
```

**Error Response Schema:**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "detail": "Missing required field: message"
    }
  },
  "id": 1
}
```

## Supported Methods

### `agent.chat`

Generates an interview question from a topic, creates a PDF, uploads it to S3, and returns the PDF URL.

**Parameters:**
- `conversation_id` (string, required): Unique identifier for the conversation session
- `message` (string, required): The topic for interview question generation
- `metadata` (object, optional): Additional context
  - `source_interface` (string, optional): Source of the request
  - `user_id` (string, optional): User identifier

**Response:**
- Returns PDF URL in `result.metadata.pdf_url`
- Includes question preview in `result.metadata.question_preview`

## Error Codes

| Code | Message | Description |
|------|---------|-------------|
| -32600 | Invalid Request | The JSON sent is not a valid Request object |
| -32601 | Method not found | The method does not exist / is not available |
| -32602 | Invalid params | Invalid method parameter(s) |
| -32603 | Internal error | Internal JSON-RPC error |
| -32700 | Parse error | Invalid JSON was received |

## Quick Start

### 1. Install and Run

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=your_key
export SERPAPI_API_KEY=your_key
export S3_ENDPOINT_URL=your_s3_endpoint
export S3_ACCESS_KEY_ID=your_access_key
export S3_SECRET_ACCESS_KEY=your_secret_key
export S3_BUCKET_NAME=your_bucket_name
export S3_REGION_NAME=your_region

# Run the agent
python api.py
```

Agent runs on `http://localhost:8000`

### 2. Test JSON-RPC Request

```bash
curl -X POST http://localhost:8000/api/v1/agent \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "agent.chat",
    "params": {
      "conversation_id": "test-123",
      "message": "machine learning",
      "metadata": {
        "source_interface": "postman",
        "user_id": "test_user"
      }
    },
    "id": 1
  }'
```

**Expected Response (takes ~60-120 seconds):**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "response": "PDF generated successfully: https://bucket.s3.amazonaws.com/interview_machine_learning_20240115_123456.pdf",
    "status": "success",
    "metadata": {
      "pdf_url": "https://bucket.s3.amazonaws.com/interview_machine_learning_20240115_123456.pdf",
      "topic": "machine learning",
      "question_preview": "What is the attention mechanism in transformers?",
      "conversation_id": "test-123"
    }
  },
  "id": 1
}
```

## Integration with Agent Router

### Step 1: Configure Router

Add the agent to your router's configuration:

```yaml
agents:
  interview:
    name: "Interview Q&A Agent"
    description: "Generate interview questions and PDFs"
    endpoint: "${INTERVIEW_AGENT_ENDPOINT}"  # http://localhost:8000
    protocol: "jsonrpc2.0"
    method: "agent.chat"
    timeout: 120
    enabled: true
```

### Step 2: Router Code

Example router implementation:

```python
import httpx
from typing import Dict, Any

class AgentRouter:
    def __init__(self, agent_endpoint: str):
        self.endpoint = agent_endpoint
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def route_command(
        self,
        conversation_id: str,
        message: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Route command to deep agent using JSON-RPC 2.0."""
        
        # Prepare JSON-RPC 2.0 request
        payload = {
            "jsonrpc": "2.0",
            "method": "agent.chat",
            "params": {
                "conversation_id": conversation_id,
                "message": message,
                "metadata": metadata or {}
            },
            "id": 1
        }
        
        try:
            response = await self.client.post(
                f"{self.endpoint}/api/v1/agent",
                json=payload
            )
            return response.json()
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": {"detail": str(e)}
                },
                "id": 1
            }
    
    async def close(self):
        await self.client.aclose()


# Usage
async def main():
    router = AgentRouter("http://localhost:8000")
    
    result = await router.route_command(
        conversation_id="conv-123",
        message="neural networks",
        metadata={"user_id": "user123", "source_interface": "teams"}
    )
    
    if "result" in result:
        print("PDF URL:", result["result"]["metadata"]["pdf_url"])
    else:
        print("Error:", result["error"]["message"])
    
    await router.close()
```

### Step 3: LangGraph Integration

For LangGraph-based routers:

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END
import httpx

class RouterState(TypedDict):
    conversation_id: str
    message: str
    metadata: dict
    result: dict

async def call_interview_agent(state: RouterState) -> RouterState:
    """Node that calls the deep agent via JSON-RPC 2.0."""
    endpoint = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "agent.chat",
            "params": {
                "conversation_id": state["conversation_id"],
                "message": state["message"],
                "metadata": state["metadata"]
            },
            "id": 1
        }
        
        response = await client.post(f"{endpoint}/api/v1/agent", json=payload)
        state["result"] = response.json()
    
    return state

# Add to your LangGraph workflow
workflow = StateGraph(RouterState)
workflow.add_node("interview_agent", call_interview_agent)
workflow.add_edge("interview_agent", END)
```

## PDF Generation Flow

When a topic is received:

1. **LangGraph Workflow**: Generates interview question using multi-stage workflow
2. **PDF Generation**: Creates PDF from the generated question
3. **S3 Upload**: Uploads PDF to S3 and gets public URL
4. **Response**: Returns JSON-RPC response with PDF URL

The PDF includes:
- Topic
- Interview question
- Common wrong answer
- Correct explanation
- Citation to research paper

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for LLM operations |
| `SERPAPI_API_KEY` | Yes | - | SerpAPI key for research paper search |
| `S3_ENDPOINT_URL` | Yes | - | S3 endpoint URL |
| `S3_ACCESS_KEY_ID` | Yes | - | S3 access key |
| `S3_SECRET_ACCESS_KEY` | Yes | - | S3 secret key |
| `S3_BUCKET_NAME` | Yes | - | S3 bucket name |
| `S3_REGION_NAME` | No | nyc3 | S3 region name |
| `PORT` | No | 8000 | Server port |
| `ENVIRONMENT` | No | dev | Environment (dev/production) |

### Timeouts

Recommended timeout settings:

- **Health Check**: 5 seconds
- **Question Generation + PDF**: 120 seconds (2 minutes)
- **Router → Agent**: 120 seconds

## Testing JSON-RPC Compliance

### Basic Test Script

```python
import httpx
import asyncio

async def test_jsonrpc_compliance():
    endpoint = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # Test 1: Valid request
        print("Testing agent.chat method...")
        result = await client.post(
            f"{endpoint}/api/v1/agent",
            json={
                "jsonrpc": "2.0",
                "method": "agent.chat",
                "params": {
                    "conversation_id": "test",
                    "message": "test topic",
                    "metadata": {}
                },
                "id": 1
            },
            timeout=120.0
        )
        data = result.json()
        
        assert "jsonrpc" in data
        assert data["jsonrpc"] == "2.0"
        
        if "result" in data:
            assert "response" in data["result"]
            assert "status" in data["result"]
            assert "metadata" in data["result"]
            assert "pdf_url" in data["result"]["metadata"]
            print("✅ PASSED: Valid request")
        elif "error" in data:
            assert "code" in data["error"]
            assert "message" in data["error"]
            print(f"⚠️  Error: {data['error']['message']}")
        
        # Test 2: Invalid method
        print("\nTesting invalid method...")
        result = await client.post(
            f"{endpoint}/api/v1/agent",
            json={
                "jsonrpc": "2.0",
                "method": "invalid.method",
                "params": {},
                "id": 2
            }
        )
        data = result.json()
        assert data["error"]["code"] == -32601
        print("✅ PASSED: Invalid method handled")
        
        # Test 3: Missing params
        print("\nTesting missing params...")
        result = await client.post(
            f"{endpoint}/api/v1/agent",
            json={
                "jsonrpc": "2.0",
                "method": "agent.chat",
                "params": {},
                "id": 3
            }
        )
        data = result.json()
        assert data["error"]["code"] == -32602
        print("✅ PASSED: Missing params handled")
        
        print("\n🎉 Agent is JSON-RPC 2.0 compliant!")

asyncio.run(test_jsonrpc_compliance())
```

## Production Considerations

### Health Monitoring

```python
async def monitor_agent_health(endpoint: str):
    """Monitor agent health periodically."""
    while True:
        try:
            response = await client.get(f"{endpoint}/health", timeout=5.0)
            status = response.json().get("status")
            
            if status != "healthy":
                logger.warning(f"Agent unhealthy: {status}")
                # Alert or failover logic here
        except Exception as e:
            logger.error(f"Health check failed: {e}")
        
        await asyncio.sleep(60)  # Check every minute
```

### Retry Logic

```python
async def call_with_retry(endpoint: str, payload: dict, max_retries: int = 3):
    """Call agent with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            response = await client.post(
                f"{endpoint}/api/v1/agent",
                json=payload,
                timeout=120.0
            )
            data = response.json()
            
            # Check for JSON-RPC error
            if "error" in data:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    return data
            
            return data
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            await asyncio.sleep(wait_time)
```

## Summary

The Deep Agent is **production-ready** and **fully JSON-RPC 2.0 compatible**:

✅ JSON-RPC 2.0 standard protocol  
✅ Pydantic request/response validation  
✅ Standard error codes  
✅ Health check monitoring  
✅ LangGraph workflow orchestration  
✅ Async/non-blocking operations  
✅ Structured logging  
✅ Automatic PDF generation and S3 upload  
✅ Docker deployment ready  

**Ready to integrate with any LangChain/LangGraph agent router!**

---

## Quick Links

- **API Docs**: `http://localhost:8000/docs` (when running)
- **Health Check**: `http://localhost:8000/health`
- **Source Code**: `api.py` (FastAPI), `graph.py` (LangGraph)
- **Dockerfile**: For containerized deployment

## Support

For issues or questions:
1. Check agent logs for errors
2. Verify environment variables are set
3. Test health endpoint
4. Check API key quotas
5. Verify S3 configuration

**Built with**: LangGraph • FastAPI • OpenAI • SerpAPI • JSON-RPC 2.0

