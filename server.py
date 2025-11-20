"""
Math MCP Server
===============

A Model Context Protocol (MCP) server that provides basic mathematical operations
as tools for LLM agents to use.

Features:
---------
- Addition, subtraction, multiplication, division
- Power and modulus operations
- Robust type conversion and error handling
- FastMCP-based implementation with stdio transport

Tools Provided:
---------------
- add(a, b): Returns a + b
- subtract(a, b): Returns a - b
- multiply(a, b): Returns a * b
- divide(a, b): Returns a / b (handles division by zero)
- power(a, b): Returns a ** b
- modulus(a, b): Returns a % b

Usage:
------
Run as standalone server:
    python server.py

Or integrate with MCP client by configuring the server connection:
    {
        "command": "python",
        "args": ["server.py"],
        "transport": "stdio"
    }

Dependencies:
-------------
- fastmcp: MCP server framework

Author: MCP Math Server Team
License: See LICENSE file
"""

from fastmcp import FastMCP

mcp = FastMCP('maths')

def _as_number(x):
    """
    Converts the input to a float if possible.
    Handles strings with whitespace and numeric types.
    Returns None if conversion fails.
    """
    try:
        if isinstance(x, str):
            return float(x.strip())
        if isinstance(x, (int, float)):
            return float(x)
    except Exception as e:
        print(e)
        return None


@mcp.tool()
async def add(a: float, b: float) -> float:
    """
    Adds two numbers and returns the result.

    Args:
        a (float): First number.
        b (float): Second number.

    Returns:
        float: Sum of a and b.
    """
    return _as_number(a) + _as_number(b)


@mcp.tool()
async def subtract(a: float, b: float) -> float:
    """
    Subtracts the second number from the first and returns the result.

    Args:
        a (float): First number.
        b (float): Second number.

    Returns:
        float: Difference of a and b.
    """
    return _as_number(a) - _as_number(b)


@mcp.tool()
async def multiply(a: float, b: float) -> float:
    """
    Multiplies two numbers and returns the result.

    Args:
        a (float): First number.
        b (float): Second number.

    Returns:
        float: Product of a and b.
    """
    return _as_number(a) * _as_number(b)


@mcp.tool()
async def divide(a: float, b: float) -> float:
    """
    Divides the first number by the second and returns the result.

    Args:
        a (float): Numerator.
        b (float): Denominator.

    Returns:
        float: Result of division. Returns float('inf') if denominator is zero.
    """
    denominator = _as_number(b)
    if denominator == 0:
        return float('inf')  # Handle division by zero
    return _as_number(a) / denominator


@mcp.tool()
async def power(a: float,b: float) -> float:
    return a**b


@mcp.tool()
async def modulus(a: float, b: float) -> float:
    """
    Returns the modulus (remainder) of the division of the first number by the second.

    Args:
        a (float): Dividend.
        b (float): Divisor.

    Returns:
        float: Remainder after division.
    """
    return _as_number(a) % _as_number(b)

if __name__ == "__main__":
    mcp.run(transport='stdio')