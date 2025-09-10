#!/usr/bin/env python3
import asyncio
import json
import httpx
import re
from typing import Any, Dict, List
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

class NotificationOptions:
    def __init__(self):
        self.tools_changed = None

class EnhancedHRServer:
    def __init__(self):
        self.server = Server("enhanced-hr")
        self.setup_tools()
        
    def setup_tools(self):
        """Define what tools Claude can use"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            return [
                types.Tool(
                    name="submit_leave_request",
                    description="Submit a leave request to the HR system",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Natural language leave request"
                            },
                            "employee_id": {
                                "type": "string", 
                                "description": "Employee ID (optional)"
                            }
                        },
                        "required": ["message"]
                    }
                ),
                types.Tool(
                    name="submit_expense_request",
                    description="Submit an expense request to the HR system",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Natural language expense request (e.g., 'I spent $50 on lunch yesterday')"
                            },
                            "employee_id": {
                                "type": "string",
                                "description": "Employee ID (optional)"
                            },
                            "receipt_url": {
                                "type": "string",
                                "description": "URL to receipt image (optional)"
                            }
                        },
                        "required": ["message"]
                    }
                ),
                types.Tool(
                    name="process_natural_language_request",
                    description="Process any HR request in natural language - handles onboarding, pulse check, leave, expenses automatically",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Natural language HR request of any type"
                            },
                            "employee_id": {
                                "type": "string",
                                "description": "Employee ID (optional)"
                            }
                        },
                        "required": ["message"]
                    }
                ),
                types.Tool(
                    name="classify_hr_request",
                    description="Automatically classify if a request is for leave, expenses, onboarding, pulse check, or other HR matters",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Natural language HR request"
                            }
                        },
                        "required": ["message"]
                    }
                ),
                types.Tool(
                    name="get_expense_status",
                    description="Check the status of expense requests",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "employee_id": {
                                "type": "string",
                                "description": "Employee ID to check expenses for"
                            }
                        },
                        "required": ["employee_id"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            print(f"🔧 MCP Server: Calling tool '{name}' with args: {arguments}")
            
            if name == "process_natural_language_request":
                return await self.process_natural_language_request(arguments)
            elif name == "submit_leave_request":
                return await self.submit_leave_request(arguments)
            elif name == "submit_expense_request":
                return await self.submit_expense_request(arguments)
            elif name == "submit_onboarding_request":
                return await self.submit_onboarding_request(arguments)
            elif name == "submit_pulse_response":
                return await self.submit_pulse_response(arguments)
            elif name == "classify_hr_request":
                return await self.classify_hr_request(arguments)
            elif name == "get_expense_status":
                return await self.get_expense_status(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

    async def process_natural_language_request(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Process any HR request in natural language with intelligent parsing"""
        message = arguments.get("message", "")
        employee_id = arguments.get("employee_id", "UNKNOWN")
        
        print(f"🤖 Processing natural language request: '{message}'")
        
        # First classify the request type
        classification = await self.classify_hr_request({"message": message})
        classification_data = json.loads(classification[0].text)
        request_type = classification_data["request_type"]
        
        print(f"🔍 Classified as: {request_type}")
        
        if request_type == "leave":
            return await self.submit_leave_request({"message": message, "employee_id": employee_id})
        
        elif request_type == "expense":
            return await self.submit_expense_request({"message": message, "employee_id": employee_id})
        
        elif request_type == "onboarding":
            # Extract onboarding details from natural language
            onboarding_data = await self.extract_onboarding_info(message, employee_id)
            return await self.submit_onboarding_request(onboarding_data)
        
        elif request_type == "pulse":
            # Extract pulse check details from natural language
            pulse_data = await self.extract_pulse_info(message, employee_id)
            return await self.submit_pulse_response(pulse_data)
        
        else:
            # Return classification result if unclear
            return classification

    async def extract_onboarding_info(self, message: str, employee_id: str) -> Dict[str, Any]:
        """Extract onboarding information from natural language"""
        
        # Use regex and keyword matching to extract information
        import re
        from datetime import datetime, timedelta
        
        # Extract names
        name_match = re.search(r'(?:hire|employee|person|candidate)\s+(?:named\s+)?([A-Z][a-z]+\s+[A-Z][a-z]+)', message, re.IGNORECASE)
        full_name = name_match.group(1) if name_match else "New Employee"
        
        name_parts = full_name.split()
        first_name = name_parts[0] if name_parts else "New"
        last_name = name_parts[-1] if len(name_parts) > 1 else "Employee"
        
        # Extract email
        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', message)
        email = email_match.group(1) if email_match else f"{first_name.lower()}.{last_name.lower()}@company.com"
        
        # Extract role/position
        role_keywords = ['as', 'for the position of', 'as a', 'as an', 'role:', 'position:']
        role = "New Employee"
        for keyword in role_keywords:
            if keyword in message.lower():
                role_match = re.search(rf'{keyword}\s+([^,.\n]+)', message, re.IGNORECASE)
                if role_match:
                    role = role_match.group(1).strip()
                    break
        
        # Extract department
        dept_keywords = ['department', 'team', 'division', 'in']
        department = "General"
        for keyword in dept_keywords:
            if f'{keyword}:' in message.lower() or f'in {keyword}' in message.lower():
                dept_match = re.search(rf'{keyword}:?\s+([^,.\n]+)', message, re.IGNORECASE)
                if dept_match:
                    department = dept_match.group(1).strip()
                    break
        
        # Extract start date
        today = datetime.now()
        start_date = (today + timedelta(days=7)).strftime('%Y-%m-%d')  # Default to next week
        
        date_patterns = [
            r'start(?:ing)?\s+on\s+([^,.\n]+)',
            r'begins?\s+([^,.\n]+)',
            r'starting\s+([^,.\n]+)',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{2}[/-]\d{2}[/-]\d{4})'
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, message, re.IGNORECASE)
            if date_match:
                try:
                    date_str = date_match.group(1).strip()
                    # Try to parse common date formats
                    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                        start_date = date_str
                    break
                except:
                    pass
        
        # Extract manager email
        manager_match = re.search(r'manager:?\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', message, re.IGNORECASE)
        manager_email = manager_match.group(1) if manager_match else "manager@company.com"
        
        # Generate employee ID if not provided
        if employee_id == "UNKNOWN":
            employee_id = f"EMP{datetime.now().strftime('%Y%m%d%H%M')}"
        
        return {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "role": role,
            "department": department,
            "start_date": start_date,
            "manager_email": manager_email,
            "employee_id": employee_id
        }

    async def extract_pulse_info(self, message: str, employee_id: str) -> Dict[str, Any]:
        """Extract pulse check information from natural language"""
        
        import re
        
        # Extract rating from message
        rating = 5  # default
        rating_patterns = [
            r'(?:rate|rating|score).*?(\d+)(?:/10|out of 10)?',
            r'(\d+)(?:/10|out of 10)',
            r'(\d+)\s*(?:stars?|points?)',
            r'feeling\s+(\d+)'
        ]
        
        for pattern in rating_patterns:
            rating_match = re.search(pattern, message, re.IGNORECASE)
            if rating_match:
                try:
                    rating = min(10, max(1, int(rating_match.group(1))))
                    break
                except:
                    pass
        
        # Extract name from context or use employee ID
        name_match = re.search(r'I\'?m\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', message)
        employee_name = name_match.group(1) if name_match else f"Employee {employee_id}"
        
        # Extract email if mentioned
        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', message)
        email = email_match.group(1) if email_match else f"employee{employee_id}@company.com"
        
        # Clean up feedback (remove rating references for cleaner feedback)
        feedback = message
        for pattern in rating_patterns:
            feedback = re.sub(pattern, '', feedback, flags=re.IGNORECASE)
        
        # Remove common pulse check prefixes/suffixes
        cleanup_patterns = [
            r'(?:submit|give|provide)\s+(?:a\s+)?(?:pulse\s+)?(?:check\s+)?(?:response|feedback|survey)',
            r'(?:pulse\s+check|survey|feedback)\s*:?',
            r'my\s+(?:rating|score|feedback)\s+is',
            r'I\s+(?:want\s+to\s+)?(?:submit|give|provide)'
        ]
        
        for pattern in cleanup_patterns:
            feedback = re.sub(pattern, '', feedback, flags=re.IGNORECASE)
        
        feedback = feedback.strip().strip(',.:!')
        if not feedback:
            feedback = "Pulse check response submitted"
        
        return {
            "employee_name": employee_name,
            "email": email,
            "feedback": feedback,
            "rating": rating
        }

    async def classify_hr_request(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Classify HR request type"""
        message = arguments.get("message", "").lower()
        
        # Keywords for different request types
        leave_keywords = ["leave", "vacation", "time off", "sick", "pto", "holiday", "absent", "days off"]
        expense_keywords = ["expense", "spent", "cost", "receipt", "claim", "reimburse", "lunch", "dinner", "travel", "hotel", "flight", "$", "dollars"]
        onboarding_keywords = ["onboarding", "new employee", "new hire", "start date", "welcome", "first day", "joining", "orientation"]
        pulse_keywords = ["pulse", "feedback", "survey", "how are you", "satisfaction", "mood", "feeling", "team morale", "check-in"]
        
        leave_score = sum(1 for keyword in leave_keywords if keyword in message)
        expense_score = sum(1 for keyword in expense_keywords if keyword in message)
        onboarding_score = sum(1 for keyword in onboarding_keywords if keyword in message)
        pulse_score = sum(1 for keyword in pulse_keywords if keyword in message)
        
        scores = {
            "leave": leave_score,
            "expense": expense_score, 
            "onboarding": onboarding_score,
            "pulse": pulse_score
        }
        
        # Find the highest scoring category
        max_score = max(scores.values())
        
        if max_score == 0:
            request_type = "unclear"
            confidence = 0.3
        else:
            request_type = max(scores, key=scores.get)
            confidence = min(0.95, 0.6 + (max_score * 0.1))
        
        result = {
            "request_type": request_type,
            "confidence": confidence,
            "suggestion": f"This appears to be a {request_type} request",
            "scores": scores
        }
        
        print(f"🔍 Classification result: {result}")
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def submit_leave_request(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Send leave request to n8n workflow"""
        message = arguments.get("message", "")
        employee_id = arguments.get("employee_id", "UNKNOWN")
        
        # Your existing leave workflow URL
        webhook_url = "https://bat-adjusted-anemone.ngrok-free.app/webhook/leave-request"
        
        payload = {
            "query": message,
            "employee_id": employee_id,
            "request_type": "leave"
        }
        
        print(f"🏖️ Sending leave request to n8n: {message}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = {
                        "status": "success",
                        "type": "leave_request",
                        "message": "✅ Leave request submitted successfully!",
                        "details": f"Your request: '{message}' has been sent for manager approval.",
                        "next_steps": "You'll receive an email once your manager reviews the request."
                    }
                    print(f"✅ Leave request successful: {response.status_code}")
                else:
                    result = {
                        "status": "error",
                        "type": "leave_request",
                        "message": f"❌ Failed to submit leave request. Status: {response.status_code}"
                    }
                    print(f"❌ Leave request failed: {response.status_code}")
        except Exception as e:
            result = {
                "status": "error",
                "type": "leave_request", 
                "message": f"❌ Error: {str(e)}"
            }
            print(f"❌ Leave request error: {e}")
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def submit_expense_request(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Send expense request to n8n workflow"""
        message = arguments.get("message", "")
        employee_id = arguments.get("employee_id", "UNKNOWN")
        receipt_url = arguments.get("receipt_url", "")
        
        # Your expense workflow URL
        webhook_url = "https://bat-adjusted-anemone.ngrok-free.app/webhook/expense-request"
        
        # Extract amount using regex
        amount_match = re.search(r'\$?(\d+(?:\.\d{2})?)', message)
        amount = amount_match.group(1) if amount_match else "0"
        
        payload = {
            "query": message,
            "employee_id": employee_id,
            "amount": amount,
            "receipt_url": receipt_url,
            "request_type": "expense"
        }
        
        print(f"💰 Sending expense request to n8n: {message}")
        print(f"💵 Extracted amount: ${amount}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = {
                        "status": "success",
                        "type": "expense_request",
                        "message": "✅ Expense request submitted successfully!",
                        "details": f"Expense: ${amount} - '{message}' submitted for approval.",
                        "next_steps": "You'll receive an email once your manager reviews the expense."
                    }
                    print(f"✅ Expense request successful: {response.status_code}")
                else:
                    result = {
                        "status": "error",
                        "type": "expense_request",
                        "message": f"❌ Failed to submit expense request. Status: {response.status_code}",
                        "note": "Make sure your expense workflow is active in n8n"
                    }
                    print(f"❌ Expense request failed: {response.status_code}")
        except Exception as e:
            result = {
                "status": "error",
                "type": "expense_request",
                "message": f"❌ Error submitting expense: {str(e)}"
            }
            print(f"❌ Expense request error: {e}")
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def submit_onboarding_request(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Send onboarding request to n8n workflow"""
        first_name = arguments.get("first_name", "")
        last_name = arguments.get("last_name", "")
        email = arguments.get("email", "")
        role = arguments.get("role", "")
        department = arguments.get("department", "")
        start_date = arguments.get("start_date", "")
        manager_email = arguments.get("manager_email", "")
        employee_id = arguments.get("employee_id", "")
        
        # Your onboarding workflow URL
        webhook_url = "https://starfish-special-bulldog.ngrok-free.app/webhook/onboarding"
        
        payload = {
            "First Name": first_name,
            "Last Name": last_name,
            "Email Address": email,
            "Role": role,
            "Department": department,
            "Start Date": start_date,
            "Manager's Email Address": manager_email,
            "EmployeeID": employee_id
        }
        
        print(f"👋 Starting onboarding for: {first_name} {last_name} ({role})")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = {
                        "status": "success",
                        "type": "onboarding_request",
                        "message": "✅ Onboarding process started successfully!",
                        "details": f"Welcome email sent to {first_name} {last_name} at {email}",
                        "next_steps": f"Employee will receive onboarding instructions and document upload link. Manager {manager_email} has been notified."
                    }
                    print(f"✅ Onboarding started successfully: {response.status_code}")
                else:
                    result = {
                        "status": "error",
                        "type": "onboarding_request",
                        "message": f"❌ Failed to start onboarding. Status: {response.status_code}"
                    }
                    print(f"❌ Onboarding failed: {response.status_code}")
        except Exception as e:
            result = {
                "status": "error",
                "type": "onboarding_request",
                "message": f"❌ Error starting onboarding: {str(e)}"
            }
            print(f"❌ Onboarding error: {e}")
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def submit_pulse_response(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Send pulse check response to n8n workflow"""
        employee_name = arguments.get("employee_name", "")
        email = arguments.get("email", "")
        feedback = arguments.get("feedback", "")
        rating = arguments.get("rating", 5)
        
        # Your pulse check workflow URL
        webhook_url = "https://starfish-special-bulldog.ngrok-free.app/webhook/pulse-check"
        
        # Format payload as array to match your workflow expectation
        payload = {
            "body": [
                {
                    "name": employee_name,
                    "email": email,
                    "answer": feedback,
                    "rating": int(rating)
                }
            ]
        }
        
        print(f"📊 Submitting pulse response from: {employee_name} (Rating: {rating})")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = {
                        "status": "success",
                        "type": "pulse_response",
                        "message": "✅ Pulse check response submitted successfully!",
                        "details": f"Thank you {employee_name}! Your feedback (rating: {rating}/10) has been recorded.",
                        "next_steps": "Your response will be analyzed for sentiment and included in team insights."
                    }
                    print(f"✅ Pulse response successful: {response.status_code}")
                else:
                    result = {
                        "status": "error",
                        "type": "pulse_response",
                        "message": f"❌ Failed to submit pulse response. Status: {response.status_code}"
                    }
                    print(f"❌ Pulse response failed: {response.status_code}")
        except Exception as e:
            result = {
                "status": "error",
                "type": "pulse_response",
                "message": f"❌ Error submitting pulse response: {str(e)}"
            }
            print(f"❌ Pulse response error: {e}")
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def get_expense_status(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get expense status (placeholder - would query database)"""
        employee_id = arguments.get("employee_id", "")
        
        # This would typically query your database
        result = {
            "status": "info",
            "message": "📊 Expense status checking not yet implemented",
            "details": "This would query your expense database for pending/approved expenses",
            "employee_id": employee_id
        }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def run(self):
        """Start the MCP server"""
        print("🌟 Starting Enhanced HR MCP Server...")
        print("💼 Supports: Leave Requests & Expense Claims")
        print("👋 Supports: Employee Onboarding")
        print("📊 Supports: Pulse Check Surveys")
        print("🤖 With intelligent request classification")
        print("🔗 Connected to n8n workflows")
        
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="enhanced-hr",
                    server_version="2.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities=None
                    ),
                ),
            )

async def main():
    server = EnhancedHRServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())