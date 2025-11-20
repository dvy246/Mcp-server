"""
MCP Chat Application - Streamlit Interface
===========================================

This is a Streamlit-based chat application that integrates Google's Gemini LLM with 
Model Context Protocol (MCP) servers to provide tool-augmented conversational AI.

Features:
---------
- Interactive chat interface using Streamlit
- Multi-server MCP integration (expense tracking, Manim animations, etc.)
- Configuration-driven setup with YAML and environment variables
- Comprehensive error handling and logging
- Clean message rendering (hides intermediate tool calls)
- Persistent conversation history

Architecture:
-------------
1. Loads configuration from config.yaml and environment variables
2. Initializes MCP client with configured server connections
3. Loads available tools from all connected MCP servers
4. Binds tools to Gemini LLM using LangChain
5. Manages async operations properly for Streamlit
6. Handles tool invocation and response rendering

Configuration:
--------------
- config.yaml: Server and application settings
- .env: Environment variables (API keys, paths)

Usage:
------
    streamlit run app.py

Dependencies:
-------------
- streamlit: Web interface
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
import inspect
import logging
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

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
        logging.FileHandler(log_dir / 'mcp_chat.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# System prompt
SYSTEM_PROMPT = (
    "You have access to tools. When you choose to call a tool, do not narrate status updates. "
    "After tools run, return only a concise final answer."
)


def initialize_app():
    """
    Initialize the Streamlit application with configuration, LLM, and MCP tools.
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    try:
        logger.info("Starting application initialization")
        
        # Load and validate configuration
        config = load_config()
        validate_config(config)
        
        # Get app settings
        app_config = config.get('app', {})
        st.set_page_config(
            page_title=app_config.get('title', 'MCP Chat'),
            page_icon=app_config.get('icon', '🧰'),
            layout=app_config.get('layout', 'centered')
        )
        
        # Initialize LLM
        llm_config = config.get('llm', {})
        api_key = os.getenv(llm_config.get('api_key_env', 'GEMINI_API_KEY'))
        
        if not api_key:
            st.error("❌ GEMINI_API_KEY not found in environment variables")
            logger.error("GEMINI_API_KEY not set")
            return False
        
        st.session_state.llm = ChatGoogleGenerativeAI(
            api_key=api_key,
            model=llm_config.get('model', 'gemini-2.5-flash'),
            temperature=llm_config.get('temperature', 0.5)
        )
        logger.info(f"LLM initialized: {llm_config.get('model')}")
        
        # Initialize MCP client with enabled servers
        servers = get_enabled_servers(config)
        
        if not servers:
            st.error("❌ No enabled servers found in configuration")
            logger.error("No enabled servers configured")
            return False
        
        logger.info(f"Initializing MCP client with servers: {list(servers.keys())}")
        st.session_state.client = MultiServerMCPClient(servers)
        
        # Get tools from all servers
        try:
            tools = asyncio.run(st.session_state.client.get_tools())
            st.session_state.tools = tools
            st.session_state.tool_by_name = {t.name: t for t in tools}
            logger.info(f"Loaded {len(tools)} tools from MCP servers")
        except Exception as e:
            st.error(f"❌ Failed to load tools from MCP servers: {str(e)}")
            logger.error(f"Failed to load tools: {e}", exc_info=True)
            return False
        
        # Bind tools to LLM
        st.session_state.llm_with_tools = st.session_state.llm.bind_tools(tools)
        
        # Initialize conversation history
        st.session_state.history = [SystemMessage(content=SYSTEM_PROMPT)]
        st.session_state.initialized = True
        
        logger.info("Application initialization complete")
        return True
        
    except FileNotFoundError as e:
        st.error(f"❌ Configuration file not found: {str(e)}")
        logger.error(f"Configuration file not found: {e}")
        return False
    
    except ValueError as e:
        st.error(f"❌ Configuration error: {str(e)}")
        logger.error(f"Configuration validation failed: {e}")
        return False
    
    except Exception as e:
        st.error(f"❌ Unexpected error during initialization: {str(e)}")
        logger.error(f"Unexpected initialization error: {e}", exc_info=True)
        return False


def render_chat_history():
    """Render chat history, skipping system and tool messages."""
    for msg in st.session_state.history:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user"):
                st.markdown(msg.content)
        elif isinstance(msg, AIMessage):
            # Skip assistant messages that contain tool_calls
            if getattr(msg, "tool_calls", None):
                continue
            with st.chat_message("assistant"):
                st.markdown(msg.content)


def process_user_message(user_text: str):
    """
    Process user message with tool invocation support.
    
    Args:
        user_text: User's input message
    """
    try:
        logger.info(f"Processing user message: {user_text[:50]}...")
        
        # Add user message to history
        st.session_state.history.append(HumanMessage(content=user_text))
        
        # First pass: let the model decide whether to call tools
        first = st.session_state.llm_with_tools.invoke(st.session_state.history)
        tool_calls = getattr(first, "tool_calls", None)
        
        if not tool_calls:
            # No tools → show & store assistant reply
            with st.chat_message("assistant"):
                st.markdown(first.content or "")
            st.session_state.history.append(first)
            logger.info("Response generated without tool calls")
        else:
            # Append assistant message WITH tool_calls (do NOT render)
            st.session_state.history.append(first)
            logger.info(f"Executing {len(tool_calls)} tool calls")
            
            # Execute requested tools and append ToolMessages
            tool_msgs = []
            for tc in tool_calls:
                try:
                    name = tc["name"]
                    args = tc.get("args") or {}
                    
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse tool args as JSON: {args}")
                    
                    logger.info(f"Calling tool: {name} with args: {args}")
                    tool = st.session_state.tool_by_name[name]
                    
                    # Handle both sync and async tools
                    if inspect.iscoroutinefunction(tool.invoke):
                        res = asyncio.run(tool.ainvoke(args))
                    else:
                        res = tool.invoke(args)
                    
                    tool_msgs.append(
                        ToolMessage(tool_call_id=tc["id"], content=json.dumps(res))
                    )
                    logger.info(f"Tool {name} executed successfully")
                    
                except KeyError:
                    error_msg = f"Tool '{name}' not found"
                    logger.error(error_msg)
                    tool_msgs.append(
                        ToolMessage(tool_call_id=tc["id"], content=json.dumps({"error": error_msg}))
                    )
                
                except Exception as e:
                    error_msg = f"Error executing tool '{name}': {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    tool_msgs.append(
                        ToolMessage(tool_call_id=tc["id"], content=json.dumps({"error": error_msg}))
                    )
            
            st.session_state.history.extend(tool_msgs)
            
            # Final assistant reply using tool outputs
            final = st.session_state.llm.invoke(st.session_state.history)
            with st.chat_message("assistant"):
                st.markdown(final.content or "")
            st.session_state.history.append(AIMessage(content=final.content or ""))
            logger.info("Final response generated with tool results")
    
    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        logger.error(error_msg, exc_info=True)
        st.error(f"❌ {error_msg}")


def main():
    """Main application entry point."""
    # One-time initialization
    if "initialized" not in st.session_state:
        if not initialize_app():
            st.stop()
    
    # Display title
    st.title("🧰 MCP Chat")
    
    # Render chat history
    render_chat_history()
    
    # Chat input
    user_text = st.chat_input("Type a message…")
    if user_text:
        with st.chat_message("user"):
            st.markdown(user_text)
        process_user_message(user_text)


if __name__ == "__main__":
    main()