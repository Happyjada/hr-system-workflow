#!/usr/bin/env python3
"""
Check MCP library version and test different protocol formats
"""

import asyncio
import json
import sys

async def test_different_formats():
    """Test different MCP protocol formats"""
    
    process = await asyncio.create_subprocess_exec(
        sys.executable, 'simple_hr_server.py',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    try:
        # Initialize first
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
        
        process.stdin.write((json.dumps(init_request) + "\n").encode())
        await process.stdin.drain()
        init_line = await asyncio.wait_for(process.stdout.readline(), timeout=10)
        print("✅ Initialization successful")
        
        # Test different tools/list formats
        formats_to_test = [
            # Format 1: Empty params
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            },
            # Format 2: No params
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            },
            # Format 3: Null params
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/list",
                "params": None
            }
        ]
        
        for i, format_test in enumerate(formats_to_test, 1):
            print(f"\n📤 Testing tools/list format {i}...")
            process.stdin.write((json.dumps(format_test) + "\n").encode())
            await process.stdin.drain()
            
            try:
                line = await asyncio.wait_for(process.stdout.readline(), timeout=5)
                response = json.loads(line.decode().strip())
                print(f"📥 Response: {json.dumps(response, indent=2)}")
                
                if "error" not in response:
                    print(f"✅ Format {i} works!")
                    working_format = format_test
                    break
            except asyncio.TimeoutError:
                print(f"⏱️ Format {i} timed out")
            except Exception as e:
                print(f"❌ Format {i} error: {e}")
        
        # Now test tools/call with different formats
        call_formats = [
            # Format 1: Standard format
            {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {
                    "name": "classify_hr_request",
                    "arguments": {
                        "message": "I need vacation"
                    }
                }
            },
            # Format 2: Different structure
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {
                    "tool": "classify_hr_request",
                    "arguments": {
                        "message": "I need vacation"
                    }
                }
            },
            # Format 3: Flat structure
            {
                "jsonrpc": "2.0",
                "id": 12,
                "method": "tools/call",
                "params": {
                    "classify_hr_request": {
                        "message": "I need vacation"
                    }
                }
            }
        ]
        
        for i, call_format in enumerate(call_formats, 1):
            print(f"\n📤 Testing tools/call format {i}...")
            process.stdin.write((json.dumps(call_format) + "\n").encode())
            await process.stdin.drain()
            
            try:
                line = await asyncio.wait_for(process.stdout.readline(), timeout=10)
                response = json.loads(line.decode().strip())
                print(f"📥 Response: {json.dumps(response, indent=2)}")
                
                if "error" not in response:
                    print(f"✅ Call format {i} works!")
                    break
            except asyncio.TimeoutError:
                print(f"⏱️ Call format {i} timed out")
            except Exception as e:
                print(f"❌ Call format {i} error: {e}")
                
    except Exception as e:
        print(f"❌ Test error: {e}")
        stderr_data = await process.stderr.read()
        if stderr_data:
            print(f"🔍 MCP Server stderr: {stderr_data.decode()}")
    finally:
        process.terminate()
        await process.wait()

async def check_mcp_version():
    """Check MCP library version"""
    try:
        import mcp
        print(f"📦 MCP library version: {getattr(mcp, '__version__', 'unknown')}")
        
        # Check available methods
        from mcp.server import Server
        server = Server("test")
        print(f"🔧 Server methods: {[m for m in dir(server) if not m.startswith('_')]}")
        
    except Exception as e:
        print(f"❌ Error checking MCP: {e}")

if __name__ == "__main__":
    print("🔍 Checking MCP setup...")
    asyncio.run(check_mcp_version())
    print("\n🧪 Testing protocol formats...")
    asyncio.run(test_different_formats())