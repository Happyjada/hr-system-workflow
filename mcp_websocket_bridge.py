#!/usr/bin/env python3
"""
Proper MCP WebSocket Bridge with correct protocol implementation
"""

import asyncio
import json
import websockets
import subprocess
import sys
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProperMCPBridge:
    def __init__(self):
        self.connected_clients = set()

    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool with proper protocol handling"""
        logger.info(f"🔧 Starting MCP process for tool: {tool_name}")
        
        mcp_process = None
        try:
            # Start MCP server process
            mcp_process = await asyncio.create_subprocess_exec(
                sys.executable, 'simple_hr_server.py',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Step 1: Initialize the MCP server
            init_request = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "websocket-bridge",
                        "version": "1.0.0"
                    }
                }
            }
            
            logger.info("📤 Sending MCP initialization...")
            init_message = json.dumps(init_request) + "\n"
            mcp_process.stdin.write(init_message.encode())
            await mcp_process.stdin.drain()
            
            # Read initialization response
            init_line = await asyncio.wait_for(mcp_process.stdout.readline(), timeout=10)
            if not init_line:
                return {"status": "error", "message": "MCP server failed to initialize"}
            
            init_response = json.loads(init_line.decode().strip())
            logger.info(f"📥 MCP initialized: {init_response.get('result', {}).get('serverInfo', {})}")
            
            if "error" in init_response:
                return {"status": "error", "message": f"MCP init error: {init_response['error']['message']}"}
            
            # Step 2: Send initialized notification (required by MCP protocol)
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            
            logger.info("📤 Sending initialized notification...")
            init_notif_message = json.dumps(initialized_notification) + "\n"
            mcp_process.stdin.write(init_notif_message.encode())
            await mcp_process.stdin.drain()
            
            # Small delay to let the server process the notification
            await asyncio.sleep(0.1)
            
            # Step 3: Call the actual tool
            tool_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            logger.info(f"📤 Calling MCP tool: {tool_name}")
            tool_message = json.dumps(tool_request) + "\n"
            mcp_process.stdin.write(tool_message.encode())
            await mcp_process.stdin.drain()
            
            # Read tool response with longer timeout for n8n calls
            tool_line = await asyncio.wait_for(mcp_process.stdout.readline(), timeout=45)
            if not tool_line:
                return {"status": "error", "message": "No response from MCP tool"}
            
            tool_response = json.loads(tool_line.decode().strip())
            logger.info(f"📥 MCP tool response received for {tool_name}")
            
            # Parse the response based on MCP format
            if "result" in tool_response and "content" in tool_response["result"]:
                # Standard MCP response with content
                content = json.loads(tool_response["result"]["content"][0]["text"])
                logger.info(f"✅ MCP tool '{tool_name}' executed successfully")
                return content
            elif "error" in tool_response:
                logger.error(f"❌ MCP tool error: {tool_response['error']}")
                return {"status": "error", "message": tool_response["error"].get("message", "MCP tool error")}
            else:
                logger.warning(f"⚠️ Unexpected MCP response format: {tool_response}")
                return {"status": "error", "message": "Unexpected MCP response format"}
                
        except asyncio.TimeoutError:
            logger.error(f"⏱️ MCP tool '{tool_name}' timed out")
            return {"status": "error", "message": "MCP request timeout"}
        except Exception as e:
            logger.error(f"❌ MCP tool '{tool_name}' failed: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            # Clean up the process
            if mcp_process:
                try:
                    mcp_process.terminate()
                    await asyncio.wait_for(mcp_process.wait(), timeout=5)
                    logger.info(f"🧹 MCP process cleaned up for {tool_name}")
                except:
                    mcp_process.kill()
                    await mcp_process.wait()

    async def handle_client(self, websocket):
        """Handle WebSocket client connections"""
        self.connected_clients.add(websocket)
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        logger.info(f"🌐 Client connected from {client_ip}. Total: {len(self.connected_clients)}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.info(f"📨 Request from {client_ip}: {data.get('tool', 'unknown')} tool")
                    
                    # Extract request information
                    tool_name = data.get("tool")
                    arguments = data.get("arguments", {})
                    request_id = data.get("id", 1)
                    
                    if not tool_name:
                        await websocket.send(json.dumps({
                            "id": request_id,
                            "success": False,
                            "error": "Missing 'tool' parameter"
                        }))
                        continue
                    
                    # Call MCP server
                    result = await self.call_mcp_tool(tool_name, arguments)
                    
                    # Determine success based on result
                    is_success = result.get("status") == "success" or ("error" not in result and "status" not in result)
                    
                    # Send response back to client
                    response = {
                        "id": request_id,
                        "success": is_success,
                        "data": result
                    }
                    
                    logger.info(f"📤 Response to {client_ip}: {'SUCCESS' if is_success else 'ERROR'}")
                    await websocket.send(json.dumps(response))
                    
                except json.JSONDecodeError:
                    logger.error(f"❌ Invalid JSON from {client_ip}")
                    await websocket.send(json.dumps({
                        "error": "Invalid JSON format"
                    }))
                except Exception as e:
                    logger.error(f"❌ Error handling {client_ip}: {e}")
                    await websocket.send(json.dumps({
                        "error": str(e)
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"👋 Client {client_ip} disconnected")
        except Exception as e:
            logger.error(f"❌ Client handler error for {client_ip}: {e}")
        finally:
            self.connected_clients.discard(websocket)

    async def test_mcp_server(self):
        """Test if MCP server can start properly"""
        try:
            test_process = await asyncio.create_subprocess_exec(
                sys.executable, 'simple_hr_server.py',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Quick initialization test
            init_request = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0.0"}
                }
            }
            
            test_process.stdin.write((json.dumps(init_request) + "\n").encode())
            await test_process.stdin.drain()
            
            response = await asyncio.wait_for(test_process.stdout.readline(), timeout=5)
            test_process.terminate()
            await test_process.wait()
            
            if response:
                logger.info("✅ MCP server test: PASSED")
                return True
            else:
                logger.error("❌ MCP server test: FAILED")
                return False
                
        except Exception as e:
            logger.error(f"❌ MCP server test error: {e}")
            return False

    async def start_server(self, host="localhost", port=8765):
        """Start the WebSocket server"""
        logger.info(f"🚀 Starting Proper MCP WebSocket Bridge on ws://{host}:{port}")
        
        # Test MCP server
        if not await self.test_mcp_server():
            logger.error("❌ MCP server test failed. Check simple_hr_server.py")
            return
        
        # Check if MCP server file exists
        import os
        if not os.path.exists('simple_hr_server.py'):
            logger.error("❌ simple_hr_server.py not found!")
            return
        
        async with websockets.serve(self.handle_client, host, port, ping_interval=20, ping_timeout=10):
            logger.info("🌟 MCP WebSocket Bridge is ready!")
            logger.info("💼 Supporting: Leave Requests, Expense Claims, Classification")
            logger.info("🔗 Connecting React frontend to MCP-powered n8n workflows")
            logger.info("📡 Waiting for client connections...")
            await asyncio.Future()  # Run forever

    async def cleanup(self):
        """Clean up"""
        logger.info("🧹 Bridge cleaned up")

async def main():
    bridge = ProperMCPBridge()
    
    try:
        await bridge.start_server()
    except KeyboardInterrupt:
        logger.info("👋 Shutting down MCP bridge...")
    finally:
        await bridge.cleanup()

if __name__ == "__main__":
    # Install required packages
    try:
        import websockets
    except ImportError:
        print("Installing websockets...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
        import websockets
    
    asyncio.run(main())