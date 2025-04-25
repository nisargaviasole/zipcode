from mcp.server.fastmcp import FastMCP
import importlib
import os
import sys
import json
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_service_modules(service_dir="server/services"):
    """Import all service modules from the services directory."""
    services_path = os.path.abspath(service_dir)
    if services_path not in sys.path:
        sys.path.insert(0, services_path)
    
    service_modules = []
    
    for file in os.listdir(service_dir):
        if file.endswith('.py') and not file.startswith('__'):
            module_name = file[:-3]
            try:
                module = importlib.import_module(f"services.{module_name}")
                if hasattr(module, 'mcp'):
                    service_modules.append(module)
                else:
                    logger.warning(f"No 'mcp' attribute in {module_name}")
            except Exception as e:
                logger.error(f"Error importing {module_name}: {e}")
    
    return service_modules

async def main():
    # Create a main MCP server
    main_mcp = FastMCP(
        name="main-server",
        host="0.0.0.0",
        port=8000
    )
    
    # Import all service modules
    service_modules = import_service_modules()
    
    # Register all services with the main MCP server
    for service_module in service_modules:
        service_name = service_module.mcp.name
        try:
            tools = await service_module.mcp.list_tools() or []
            if isinstance(tools, list):
                for tool in tools:
                    try:
                        # Get the tool function from the module
                        tool_func = getattr(service_module, tool.name, None)
                        if tool_func and callable(tool_func):
                            main_mcp.add_tool(tool_func)
                        else:
                            logger.warning(f"No callable function found for tool {tool.name} in {service_name}")
                    except Exception as e:
                        logger.error(f"Error registering tool {tool.name}: {e}")
            else:
                logger.warning(f"No tools or invalid tool format for service {service_name}")
        except Exception as e:
            logger.error(f"Error listing tools for service {service_name}: {e}")
    
    # Verify SSE setup
    if hasattr(main_mcp, 'sse_app'):
        logger.info("SSE application is set up.")
    else:
        logger.warning("SSE application not found in FastMCP.")
    
    # Run the main MCP server with SSE transport
    try:
        await main_mcp.run_sse_async()
    except Exception as e:
        logger.error(f"Error starting SSE server: {e}")

if __name__ == "__main__":
    asyncio.run(main())