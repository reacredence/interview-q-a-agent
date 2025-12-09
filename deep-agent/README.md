# Deep Agent - Interview Q&A Agent

A LangGraph-based AI agent that generates high-quality interview questions from academic research papers. This agent implements **JSON-RPC 2.0 protocol** and is designed to integrate seamlessly with LangChain/LangGraph agent routers.

## 🎯 Overview

The Deep Agent uses a multi-stage LangGraph workflow to:
1. Plan research queries based on a given topic
2. Research and fetch relevant academic papers
3. Select the most suitable paper
4. Generate interview questions with wrong answers and explanations
5. Review and refine questions through an iterative feedback loop
6. Format output for LinkedIn sharing

## 🔌 JSON-RPC 2.0 Protocol Compliance

This agent implements the **JSON-RPC 2.0 Protocol**, making it compatible with any LangChain/LangGraph agent router. It exposes standardized JSON-RPC endpoints for seamless integration.

### ✅ JSON-RPC 2.0 Requirements Met

- **✅ JSON-RPC 2.0 Standard**: Full compliance with JSON-RPC 2.0 specification
- **✅ POST `/`**: Single JSON-RPC endpoint for all method calls
- **✅ Method Routing**: Supports `agent.chat` method
- **✅ Standard Error Codes**: JSON-RPC error codes (-32601, -32602, -32603, etc.)
- **✅ GET `/health`**: Health check endpoint for monitoring
- **✅ Async Operations**: Non-blocking FastAPI implementation
- **✅ Structured Logging**: Context-aware logging with structlog
- **✅ PDF Generation**: Automatically generates and uploads PDFs to S3

## 🏗️ Architecture

### LangGraph Workflow

```
┌─────────┐     ┌────────────┐     ┌──────────┐     ┌───────────┐
│ Planner │────▶│ Researcher │────▶│ Selector │────▶│ Generator │
└─────────┘     └────────────┘     └──────────┘     └─────┬─────┘
                                                            │
                                                            ▼
┌──────────┐                                         ┌──────────┐
│ LinkedIn │◀────────────────────────────────────────│ Reviewer │
└──────────┘                                         └────┬─────┘
                                                          │
                                                          │ (refinement)
                                                          └───────────┐
                                                                      │
                                                          ┌───────────▼─┐
                                                          │  Generator  │
                                                          └─────────────┘
```

### Node Functions

- **Planner**: Generates research queries from the topic
- **Researcher**: Fetches academic papers using SerpAPI
- **Selector**: Chooses the most relevant paper
- **Generator**: Creates interview questions with explanations
- **Reviewer**: Provides feedback and approves/rejects questions
- **LinkedIn**: Formats final output for sharing

## 📡 API Endpoints

### 1. POST `/api/v1/agent` (JSON-RPC 2.0 Endpoint)

Primary endpoint for JSON-RPC 2.0 method calls. Supports the `agent.chat` method for generating interview questions and PDFs.

#### Request Schema

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

**Fields:**
- `jsonrpc` (string, required): Must be `"2.0"`
- `method` (string, required): Method name - currently supports `"agent.chat"`
- `params` (object, required): Method parameters
  - `conversation_id` (string, required): Unique identifier for the conversation session
  - `message` (string, required): The topic for interview question generation
  - `metadata` (object, optional): Additional context
    - `source_interface` (string, optional): Source of the request
    - `user_id` (string, optional): User identifier
- `id` (int|string, required): Request ID for correlation

#### Success Response Schema

```json
{
  "jsonrpc": "2.0",
  "result": {
    "response": "PDF generated successfully: https://bucket.s3.amazonaws.com/interview_machine_learning_20240115.pdf",
    "status": "success",
    "metadata": {
      "pdf_url": "https://bucket.s3.amazonaws.com/interview_machine_learning_20240115.pdf",
      "topic": "machine learning",
      "question_preview": "What is the attention mechanism in transformers?",
      "conversation_id": "string"
    }
  },
  "id": 1
}
```

**Fields:**
- `jsonrpc` (string): Always `"2.0"`
- `result` (object): Result object
  - `response` (string): Text response message
  - `status` (string): Always `"success"`
  - `metadata` (object): Additional data
    - `pdf_url` (string): URL to the generated PDF
    - `topic` (string): Original topic
    - `question_preview` (string): Preview of the generated question
    - `conversation_id` (string): Conversation identifier
- `id` (int|string): Request ID from the request

#### Error Response Schema

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

**Error Codes:**
- `-32600`: Invalid Request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error
- `-32700`: Parse error

### 2. GET `/health`

Health check endpoint for agent availability monitoring.

#### Response Schema

```json
{
  "status": "healthy",
  "service": "interview-q-a-agent"
}
```

**Status Values:**
- `healthy`: Agent is fully operational
- `degraded`: Agent is running but missing optional features
- `unhealthy`: Agent is not operational

### 3. GET `/` (Service Info)

Root endpoint providing service information.

#### Response

```json
{
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
```

## 🔗 Integration with Agent Router

### Step 1: Configure Agent Router

Add the agent to your agent router configuration (e.g., `agents.yml`):

```yaml
agents:
  interview:
    name: "Interview Q&A Agent"
    description: "Generate interview questions and PDFs from academic research"
    endpoint: "${INTERVIEW_AGENT_ENDPOINT}"
    protocol: "jsonrpc2.0"
    method: "agent.chat"
    timeout: 120  # Longer timeout for LLM operations + PDF generation
    enabled: true
```

### Step 2: Router Implementation

Example router code using LangChain/LangGraph:

```python
import httpx
from typing import Dict, Any

async def route_to_agent(conversation_id: str, message: str, metadata: Dict[str, Any] = None):
    """Route command to the appropriate agent using JSON-RPC 2.0."""
    
    # Get agent endpoint from config
    endpoint = get_agent_endpoint("interview")
    
    # Prepare JSON-RPC 2.0 payload
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
    
    # Make async request
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{endpoint}/api/v1/agent",
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": {"detail": f"Agent returned status {response.status_code}"}
                },
                "id": 1
            }
```

### Step 3: Health Check Integration

Implement periodic health checks:

```python
async def check_agent_health(endpoint: str) -> bool:
    """Check if agent is healthy."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{endpoint}/health")
            data = response.json()
            return data.get("status") == "healthy"
    except Exception:
        return False
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API Key
- SerpAPI Key (for research papers)

### Installation

1. Clone the repository:
```bash
cd deep-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
# Create .env file
cat > .env << EOF
OPENAI_API_KEY=your_openai_key
SERPAPI_API_KEY=your_serpapi_key
PORT=8000
ENVIRONMENT=dev
EOF
```

### Running Locally

#### Development Mode

```bash
python api.py
```

The API will be available at `http://localhost:8000`

#### Production Mode with Uvicorn

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

### Running with Docker

#### Build Image

```bash
docker build -t interview-qa-agent .
```

#### Run Container

```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -e SERPAPI_API_KEY=your_key \
  interview-qa-agent
```

## 📝 Usage Examples

### Example 1: Basic JSON-RPC Request

```bash
curl -X POST http://localhost:8000/api/v1/agent \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "agent.chat",
    "params": {
      "conversation_id": "test-123",
      "message": "transformers in NLP",
      "metadata": {
        "source_interface": "curl",
        "user_id": "user123"
      }
    },
    "id": 1
  }'
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "response": "PDF generated successfully: https://bucket.s3.amazonaws.com/interview_transformers_in_NLP_20240115_123456.pdf",
    "status": "success",
    "metadata": {
      "pdf_url": "https://bucket.s3.amazonaws.com/interview_transformers_in_NLP_20240115_123456.pdf",
      "topic": "transformers in NLP",
      "question_preview": "What is the attention mechanism in transformers?",
      "conversation_id": "test-123"
    }
  },
  "id": 1
}
```

### Example 2: Python Client

```python
import httpx
import asyncio

async def generate_interview_question(topic: str, conversation_id: str = "demo"):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/agent",
            json={
                "jsonrpc": "2.0",
                "method": "agent.chat",
                "params": {
                    "conversation_id": conversation_id,
                    "message": topic,
                    "metadata": {
                        "source_interface": "python",
                        "user_id": "demo"
                    }
                },
                "id": 1
            },
            timeout=120.0
        )
        return response.json()

# Run
result = asyncio.run(generate_interview_question("machine learning"))
if "result" in result:
    print("PDF URL:", result["result"]["metadata"]["pdf_url"])
else:
    print("Error:", result["error"]["message"])
```

### Example 3: Health Check

```bash
curl http://localhost:8000/health
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for LLM operations |
| `SERPAPI_API_KEY` | Yes | - | SerpAPI key for research paper search |
| `PORT` | No | 8000 | Server port |
| `ENVIRONMENT` | No | dev | Environment (dev/production) |

### Timeouts

The agent supports long-running operations. Recommended timeout settings:

- **Health Check**: 5 seconds
- **Agent Processing**: 120 seconds (2 minutes)
- **Router to Agent**: 120 seconds

## 📊 Response Format Types

The agent uses `format_type` to indicate how responses should be formatted:

| Format Type | Description | Use Case |
|-------------|-------------|----------|
| `interview_qa` | Interview Q&A format | Interview questions with explanations |
| `error` | Error format | Error messages |

## 🐛 Error Handling

The agent provides detailed error messages for common scenarios:

| Error | Cause | Solution |
|-------|-------|----------|
| Missing required parameter: 'topic' | No topic provided | Include topic in params |
| No research papers found | Invalid SerpAPI key or no results | Check API key and try different topic |
| Failed to select a suitable research paper | Papers don't match criteria | Try more specific topic |
| Service not ready | Graph not initialized | Wait for startup or check logs |

## 📈 Monitoring

### Health Check Responses

- **200 OK + "healthy"**: Agent is fully operational
- **200 OK + "degraded"**: Missing optional env vars (e.g., fallback keys)
- **200 OK + "unhealthy"**: Critical failure (graph not initialized)

### Structured Logging

The agent uses `structlog` for structured logging:

```json
{
  "event": "Processing interview question request",
  "command": "interview",
  "topic": "machine learning",
  "user_id": "user123",
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info"
}
```

## 🏗️ Deployment

### Docker Deployment

See `Dockerfile` for containerization details.

### Kubernetes Deployment

Kubernetes manifests are available in the `k8s/` directory:

- `cronjob.yaml`: Scheduled batch processing
- `secret-template.yaml`: Environment secrets

## 🔄 Workflow Details

### Question Generation Flow

1. **Input**: User provides a topic (e.g., "machine learning")
2. **Planning**: Generate 3-5 research queries
3. **Research**: Fetch academic papers from Google Scholar
4. **Selection**: Choose the most relevant paper
5. **Generation**: Create interview question with:
   - Main question
   - Common wrong answer
   - Correct explanation
   - Citation
6. **Review**: LLM reviews quality (max 3 iterations)
7. **Output**: Return formatted question

### Iteration Control

- Maximum iterations: 3
- Review stops when: feedback contains "APPROVE"
- Safety: Prevents infinite loops

## 🤝 Contributing

When extending this agent:

1. Maintain A2A protocol compliance
2. Add new nodes to `nodes/` directory
3. Update `graph.py` for workflow changes
4. Update this README with new features
5. Ensure all tests pass

## 📄 License

[Add your license information here]

## 🆘 Support

For issues or questions:
- Check logs for detailed error messages
- Verify environment variables are set correctly
- Ensure API keys have sufficient quota
- Check health endpoint for service status

---

**Built with**: LangGraph • FastAPI • OpenAI • SerpAPI

**A2A Protocol Compatible** ✅

