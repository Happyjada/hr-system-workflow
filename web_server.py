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
        "webhook_endpoints": {
            "leave": "https://bat-adjusted-anemone.ngrok-free.app/webhook/leave-request",
            "expense": "https://bat-adjusted-anemone.ngrok-free.app/webhook/expense-request", 
            "onboarding": "https://starfish-special-bulldog.ngrok-free.app/webhook/onboarding",
            "pulse_check": "https://starfish-special-bulldog.ngrok-free.app/webhook/pulse-check"
        },
        "features": {
            "natural_language_processing": True,
            "leave_requests": True,
            "expense_claims": True,
            "employee_onboarding": True,
            "pulse_surveys": True,
            "request_classification": True
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
