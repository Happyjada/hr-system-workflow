#!/usr/bin/env python3
"""
Web server wrapper for the HR MCP Server to enable Railway deployment
"""
import asyncio
import json
import os
import sys
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import httpx
import re
from datetime import datetime

# Import the MCP server components
from simple_hr_server import EnhancedHRServer

app = FastAPI(title="HR System Workflow API", version="1.0.0")

# Initialize the HR server
hr_server = EnhancedHRServer()

@app.get("/")
async def health_check():
    """Health check endpoint for Railway deployment"""
    return {
        "status": "healthy",
        "service": "HR System Workflow",
        "version": "1.0.0",
        "message": "HR system is running and ready to process requests"
    }

@app.get("/process")
async def process_request_get(query: str = "", message: str = "", employee_id: str = "UNKNOWN"):
    """Process HR requests via GET method (for Allmate and other GET-based integrations)"""
    try:
        # Determine the message from query parameters
        request_message = query or message
        
        if not request_message:
            return JSONResponse(content={
                "status": "error",
                "message": "No message provided. Use ?query=your_message or ?message=your_message",
                "example": "/process?query=I need vacation next week&employee_id=EMP123",
                "available_endpoints": {
                    "GET /process": "Process requests via GET with query parameters",
                    "POST /": "Process requests via POST with JSON body",
                    "POST /copilot": "Dedicated Copilot Studio endpoint"
                }
            })
        
        print(f"📝 GET request processing: '{request_message}' for employee: {employee_id}")
        
        # Process the request using the MCP server
        result = await hr_server.process_natural_language_request({
            "message": request_message,
            "employee_id": employee_id
        })
        
        response_text = result[0].text
        response_data = json.loads(response_text)
        
        print(f"✅ GET response generated: {response_data.get('status', 'unknown')}")
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        print(f"❌ Error in GET endpoint: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Error processing GET request: {str(e)}",
                "request_message": query or message
            }
        )

@app.get("/simple")
async def simple_get_endpoint(q: str = ""):
    """Simple GET endpoint for basic integrations that just need a query parameter"""
    try:
        if not q:
            return JSONResponse(content={
                "status": "error",
                "message": "No query provided. Use ?q=your_message",
                "example": "/simple?q=I need vacation next week"
            })
        
        print(f"🔍 Simple GET request: '{q}'")
        
        # Process the request
        result = await hr_server.process_natural_language_request({
            "message": q,
            "employee_id": "UNKNOWN"
        })
        
        response_text = result[0].text
        response_data = json.loads(response_text)
        
        print(f"✅ Simple response: {response_data.get('status', 'unknown')}")
        
        # Return a simplified response for basic integrations
        return JSONResponse(content={
            "result": response_data.get("message", "Request processed"),
            "status": response_data.get("status", "unknown"),
            "details": response_data.get("details", ""),
            "type": response_data.get("type", "unknown")
        })
        
    except Exception as e:
        print(f"❌ Error in simple endpoint: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Error: {str(e)}"
            }
        )

@app.post("/")
async def process_request_root(request: Dict[str, Any]):
    """Process HR requests sent to root endpoint (for Copilot Studio integration)"""
    try:
        # Handle different request formats from Copilot Studio
        message = None
        employee_id = "UNKNOWN"
        
        # Check if it's a direct message field
        if "message" in request:
            message = request.get("message")
            employee_id = request.get("employee_id", "UNKNOWN")
        # Check if it's nested in a query or text field (common in Copilot Studio)
        elif "query" in request:
            message = request.get("query")
            employee_id = request.get("employee_id", "UNKNOWN")
        elif "text" in request:
            message = request.get("text")
            employee_id = request.get("employee_id", "UNKNOWN")
        # Check if it's a simple string request
        elif isinstance(request, str):
            message = request
        # Check if it's in a nested structure
        elif "input" in request:
            input_data = request["input"]
            if isinstance(input_data, dict):
                message = input_data.get("message") or input_data.get("text") or input_data.get("query")
                employee_id = input_data.get("employee_id", "UNKNOWN")
            elif isinstance(input_data, str):
                message = input_data
        
        if not message:
            # If we can't find a message, return available endpoints
            return JSONResponse(content={
                "status": "error",
                "message": "No message found in request. Please provide 'message', 'query', or 'text' field.",
                "available_endpoints": {
                    "POST /": "Process natural language HR requests",
                    "POST /process-request": "Process natural language HR requests", 
                    "POST /leave-request": "Submit leave requests",
                    "POST /expense-request": "Submit expense requests",
                    "GET /health": "Health check",
                    "GET /status": "Service status"
                },
                "example_request": {
                    "message": "I need to take 3 days off next week",
                    "employee_id": "EMP123"
                }
            })
        
        # Use the MCP server's processing method
        result = await hr_server.process_natural_language_request({
            "message": message,
            "employee_id": employee_id
        })
        
        # Extract the JSON response from the MCP server result
        response_text = result[0].text
        response_data = json.loads(response_text)
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Error processing request: {str(e)}",
                "request_received": request
            }
        )

@app.get("/health")
async def detailed_health():
    """Detailed health check with system information"""
    return {
        "status": "healthy",
        "service": "HR System Workflow API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "POST /process-request - Process natural language HR requests",
            "POST /leave-request - Submit leave requests", 
            "POST /expense-request - Submit expense requests",
            "GET /health - Detailed health information"
        ],
        "capabilities": [
            "Leave request processing",
            "Expense claim processing", 
            "Employee onboarding",
            "Pulse check surveys",
            "Natural language request classification"
        ]
    }

@app.post("/process-request")
async def process_natural_language_request(request: Dict[str, Any]):
    """Process any HR request in natural language"""
    try:
        # Extract message and employee_id from request
        message = request.get("message", "")
        employee_id = request.get("employee_id", "UNKNOWN")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Use the MCP server's processing method
        result = await hr_server.process_natural_language_request({
            "message": message,
            "employee_id": employee_id
        })
        
        # Extract the JSON response from the MCP server result
        response_text = result[0].text
        response_data = json.loads(response_text)
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/copilot")
async def copilot_studio_endpoint(request: Dict[str, Any]):
    """Specialized endpoint for Copilot Studio integration with flexible request handling"""
    try:
        print(f"🤖 Copilot Studio request received: {request}")
        
        # Handle various Copilot Studio request formats
        message = None
        employee_id = "UNKNOWN"
        
        # Common Copilot Studio patterns
        if "query" in request:
            message = request["query"]
            employee_id = request.get("employee_id", "UNKNOWN")
        elif "text" in request:
            message = request["text"]
            employee_id = request.get("employee_id", "UNKNOWN")
        elif "message" in request:
            message = request["message"]
            employee_id = request.get("employee_id", "UNKNOWN")
        elif "input" in request:
            if isinstance(request["input"], dict):
                message = (request["input"].get("message") or 
                          request["input"].get("text") or 
                          request["input"].get("query"))
                employee_id = request["input"].get("employee_id", "UNKNOWN")
            elif isinstance(request["input"], str):
                message = request["input"]
        elif "user_input" in request:
            message = request["user_input"]
            employee_id = request.get("employee_id", "UNKNOWN")
        
        if not message:
            return JSONResponse(content={
                "status": "error",
                "message": "No valid message found in request",
                "received_fields": list(request.keys()),
                "expected_fields": ["message", "query", "text", "input", "user_input"],
                "example": {
                    "message": "I need to take vacation next week",
                    "employee_id": "EMP123"
                }
            })
        
        print(f"📝 Processing message: '{message}' for employee: {employee_id}")
        
        # Process the request
        result = await hr_server.process_natural_language_request({
            "message": message,
            "employee_id": employee_id
        })
        
        response_text = result[0].text
        response_data = json.loads(response_text)
        
        print(f"✅ Response generated: {response_data.get('status', 'unknown')}")
        
        # Enhance the response for Copilot Studio to make it clear what action was taken
        enhanced_response = {
            **response_data,
            "copilot_response": {
                "action_taken": True,
                "executed": True,
                "conversation_flow": "completed",
                "next_step": "none" if response_data.get("status") == "success" else "retry"
            }
        }
        
        # Add a clear summary for Copilot Studio
        if response_data.get("status") == "success":
            enhanced_response["summary"] = f"✅ Action completed successfully: {response_data.get('message', 'Request processed')}"
        else:
            enhanced_response["summary"] = f"⚠️ Action encountered an issue: {response_data.get('message', 'Request could not be processed')}"
        
        return JSONResponse(content=enhanced_response)
        
    except Exception as e:
        print(f"❌ Error in Copilot Studio endpoint: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Error processing Copilot Studio request: {str(e)}",
                "request_received": request,
                "copilot_response": {
                    "action_taken": False,
                    "executed": False,
                    "conversation_flow": "error",
                    "next_step": "retry"
                }
            }
        )

@app.post("/leave-request")
async def submit_leave_request(request: Dict[str, Any]):
    """Submit a leave request"""
    try:
        message = request.get("message", "")
        employee_id = request.get("employee_id", "UNKNOWN")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        result = await hr_server.submit_leave_request({
            "message": message,
            "employee_id": employee_id
        })
        
        response_text = result[0].text
        response_data = json.loads(response_text)
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting leave request: {str(e)}")

@app.post("/expense-request")
async def submit_expense_request(request: Dict[str, Any]):
    """Submit an expense request"""
    try:
        message = request.get("message", "")
        employee_id = request.get("employee_id", "UNKNOWN")
        receipt_url = request.get("receipt_url", "")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        result = await hr_server.submit_expense_request({
            "message": message,
            "employee_id": employee_id,
            "receipt_url": receipt_url
        })
        
        response_text = result[0].text
        response_data = json.loads(response_text)
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting expense request: {str(e)}")

@app.post("/classify-request")
async def classify_hr_request(request: Dict[str, Any]):
    """Classify the type of HR request"""
    try:
        message = request.get("message", "")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        result = await hr_server.classify_hr_request({"message": message})
        
        response_text = result[0].text
        response_data = json.loads(response_text)
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error classifying request: {str(e)}")

@app.get("/status")
async def get_service_status():
    """Get current service status and configuration"""
    return {
        "status": "operational",
        "service": "HR System Workflow",
        "timestamp": datetime.now().isoformat(),
        "api_endpoints": {
            "GET /": "Health check",
            "GET /process": "Process HR requests via GET (?query=message)",
            "GET /simple": "Simple GET endpoint (?q=message)",
            "POST /": "Process HR requests (Copilot Studio compatible)",
            "POST /copilot": "Dedicated Copilot Studio endpoint",
            "POST /process-request": "Process natural language HR requests",
            "POST /leave-request": "Submit leave requests",
            "POST /expense-request": "Submit expense requests",
            "POST /classify-request": "Classify request types",
            "GET /health": "Detailed health information",
            "GET /status": "Service status"
        },
        "webhook_endpoints": {
            "leave": "https://bat-adjusted-anemone.ngrok-free.app/webhook/leave-request",
            "expense": "https://bat-adjusted-anemone.ngrok-free.app/webhook/expense-request", 
            "onboarding": "https://starfish-special-bulldog.ngrok-free.app/webhook/onboarding",
            "pulse_check": "https://starfish-special-bulldog.ngrok-free.app/webhook/pulse-check"
        },
        "copilot_studio_integration": {
            "supported_formats": ["message", "query", "text", "input", "user_input"],
            "example_request": {
                "message": "I need to take 3 days off next week",
                "employee_id": "EMP123"
            },
            "primary_endpoint": "POST /copilot",
            "fallback_endpoint": "POST /"
        },
        "get_endpoints": {
            "for_allmate": "GET /process?query=your_message",
            "simple_get": "GET /simple?q=your_message",
            "example": "/process?query=I need vacation next week&employee_id=EMP123"
        },
        "features": {
            "natural_language_processing": True,
            "leave_requests": True,
            "expense_claims": True,
            "employee_onboarding": True,
            "pulse_surveys": True,
            "request_classification": True,
            "copilot_studio_compatible": True
        }
    }

if __name__ == "__main__":
    # Get port from environment variable (Railway sets this)
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🌟 Starting HR System Workflow API on port {port}")
    print("💼 Available endpoints:")
    print("  GET  / - Health check")
    print("  GET  /health - Detailed health info")
    print("  POST /process-request - Process natural language requests")
    print("  POST /leave-request - Submit leave requests")
    print("  POST /expense-request - Submit expense requests")
    print("  POST /classify-request - Classify request types")
    print("  GET  /status - Service status")
    
    uvicorn.run(
        "web_server:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
