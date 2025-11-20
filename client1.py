"""
MCP Chat Application - CLI Interface
=====================================

A command-line interface for interacting with Google's Gemini LLM enhanced with
Model Context Protocol (MCP) tools. This is a simpler, non-Streamlit version
suitable for scripting and testing.

Features:
---------
- Direct async/await implementation (no Streamlit overhead)
- Multi-server MCP integration (math operations, Manim animations)
- Configuration-driven setup with YAML and environment variables
- Comprehensive error handling and logging
- Tool invocation with proper message handling
- Clean separation of tool execution and response generation

Architecture:
-------------
1. Loads configuration from config.yaml and environment variables
2. Creates MCP client with configured servers
3. Retrieves available tools from all servers
4. Binds tools to Gemini LLM
5. Processes user prompt with tool invocation support
6. Returns final response after tool execution

Configuration:
--------------
- config.yaml: Server and LLM settings
- .env: Environment variables (API keys, paths)

Usage:
------
    python client1.py
    
Or import and use programmatically:
    from client1 import main
    result = asyncio.run(main("your prompt here"))

Dependencies:
-------------
- langchain-google-genai: Gemini LLM integration
- langchain-mcp-adapters: MCP protocol support
- python-dotenv: Environment variable management
- pyyaml: Configuration file parsing

Author: MCP Chat Team
License: See LICENSE file
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.messages import ToolMessage, HumanMessage

from config_loader import load_config, get_enabled_servers, validate_config

# Load environment variables
load_dotenv()

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'mcp_cli.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def main(prompt: str) -> str:
    """
    Process a prompt using MCP tools and Gemini LLM.
    
    Args:
        prompt: User's input prompt
        
    Returns:
        str: LLM's response after tool execution (if needed)
        
    Raises:
        ValueError: If configuration is invalid
        Exception: For other errors during processing
    """
    try:
        logger.info(f"Processing prompt: {prompt[:50]}...")
        
        # Load and validate configuration
        config = load_config()
        validate_config(config)
        
        # Get enabled servers
        servers = get_enabled_servers(config)
        logger.info(f"Initializing MCP client with servers: {list(servers.keys())}")
        
        # Create MCP client
        client = MultiServerMCPClient(servers)
        
        # Get tools from all servers
        try:
            tools = await client.get_tools()
            logger.info(f"Loaded {len(tools)} tools from MCP servers")
        except Exception as e:
            logger.error(f"Failed to load tools: {e}", exc_info=True)
            raise RuntimeError(f"Failed to load MCP tools: {str(e)}")
        
        # Create tool name mapping
        named_tools = {tool.name: tool for tool in tools}
        logger.info(f"Available tools: {list(named_tools.keys())}")
        
        # Initialize LLM
        llm_config = config.get('llm', {})
        api_key = os.getenv(llm_config.get('api_key_env', 'GEMINI_API_KEY'))
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        llm = ChatGoogleGenerativeAI(
            model=llm_config.get('model', 'gemini-2.5-flash'),
            api_key=api_key,
            temperature=llm_config.get('temperature', 0.5)
        )
        logger.info(f"LLM initialized: {llm_config.get('model')}")
        
        # Bind tools to LLM
        llm_with_tools = llm.bind_tools(tools=tools)
        
        # First invocation: let model decide whether to use tools
        response = await llm_with_tools.ainvoke(prompt)
        
        # Check if model wants to use tools
        if not getattr(response, 'tool_calls', None):
            logger.info("Response generated without tool calls")
            return response.content
        
        # Execute tool calls
        logger.info(f"Executing {len(response.tool_calls)} tool calls")
        tool_messages = []
        
        for tool_call in response.tool_calls:
            try:
                tool_name = tool_call['name']
                tool_args = tool_call['args'] or {}
                tool_id = tool_call['id']
                
                logger.info(f"Calling tool: {tool_name} with args: {tool_args}")
                
                # Execute the tool
                if tool_name not in named_tools:
                    error_msg = f"Tool '{tool_name}' not found"
                    logger.error(error_msg)
                    tool_messages.append(
                        ToolMessage(content=json.dumps({"error": error_msg}), tool_call_id=tool_id)
                    )
                    continue
                
                tool_response = await named_tools[tool_name].ainvoke(tool_args)
                logger.info(f"Tool {tool_name} executed successfully")
                
                # Create the tool message
                tool_messages.append(
                    ToolMessage(content=json.dumps(tool_response), tool_call_id=tool_id)
                )
                
            except Exception as e:
                error_msg = f"Error executing tool '{tool_name}': {str(e)}"
                logger.error(error_msg, exc_info=True)
                tool_messages.append(
                    ToolMessage(content=json.dumps({"error": error_msg}), tool_call_id=tool_id)
                )
        
        # Build message history
        messages = [HumanMessage(content=prompt), response] + tool_messages
        
        # Get final response from model
        logger.info("Getting final response from LLM")
        model_response = await llm_with_tools.ainvoke(messages)
        
        logger.info(f"Final response: {model_response.content[:100]}...")
        return model_response.content
        
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        raise
    
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    try:
        result = asyncio.run(main(prompt='What is 25 + 17?'))
        print(f"\n{'='*60}")
        print(f"Result: {result}")
        print(f"{'='*60}\n")
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

