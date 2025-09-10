#!/usr/bin/env python3
"""
Debug script to test MCP server directly
"""

import asyncio
import json
import sys

async def test_mcp_server():
    """Test the MCP server with proper protocol"""
    
    # Start MCP server process
    process = await asyncio.create_subprocess_exec(
        sys.executable, 'simple_hr_server.py',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    try:
        print("🔧 Testing MCP Server Protocol...")
        
        # Step 1: Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "debug-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("📤 Sending initialization...")
        process.stdin.write((json.dumps(init_request) + "\n").encode())
        await process.stdin.drain()
        
        # Read init response
        init_line = await asyncio.wait_for(process.stdout.readline(), timeout=10)
        init_response = json.loads(init_line.decode().strip())
        print(f"📥 Init response: {json.dumps(init_response, indent=2)}")
        
        # Step 2: List tools (optional but helpful for debugging)
        list_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        print("📤 Listing tools...")
        process.stdin.write((json.dumps(list_request) + "\n").encode())
        await process.stdin.drain()
        
        # Read list response
        list_line = await asyncio.wait_for(process.stdout.readline(), timeout=10)
        list_response = json.loads(list_line.decode().strip())
        print(f"📥 Tools list: {json.dumps(list_response, indent=2)}")
        
        # Step 3: Call a tool
        tool_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "classify_hr_request",
                "arguments": {
                    "message": "I need vacation days"
                }
            }
        }
        
        print("📤 Calling classify_hr_request tool...")
        process.stdin.write((json.dumps(tool_request) + "\n").encode())
        await process.stdin.drain()
        
        # Read tool response
        tool_line = await asyncio.wait_for(process.stdout.readline(), timeout=10)
        tool_response = json.loads(tool_line.decode().strip())
        print(f"📥 Tool response: {json.dumps(tool_response, indent=2)}")
        
        # Test another tool
        leave_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "submit_leave_request",
                "arguments": {
                    "message": "I need 2 days off next week",
                    "employee_id": "1"
                }
            }
        }
        
        print("📤 Calling submit_leave_request tool...")
        process.stdin.write((json.dumps(leave_request) + "\n").encode())
        await process.stdin.drain()
        
        # Read leave response
        leave_line = await asyncio.wait_for(process.stdout.readline(), timeout=30)
        leave_response = json.loads(leave_line.decode().strip())
        print(f"📥 Leave response: {json.dumps(leave_response, indent=2)}")
        
        print("✅ MCP Server test completed!")
        
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        # Print stderr for more details
        stderr_data = await process.stderr.read()
        if stderr_data:
            print(f"🔍 MCP Server stderr: {stderr_data.decode()}")
    finally:
        process.terminate()
        await process.wait()

if __name__ == "__main__":
    asyncio.run(test_mcp_server())