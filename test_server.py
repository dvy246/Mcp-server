"""
Unit Tests for Math MCP Server
===============================

Tests all mathematical operations provided by the server.
"""

import pytest
import sys
from pathlib import Path

# Import the helper function
sys.path.insert(0, str(Path(__file__).parent))
import server


class TestNumberConversion:
    """Test the _as_number helper function."""
    
    def test_convert_int(self):
        assert server._as_number(5) == 5.0
    
    def test_convert_float(self):
        assert server._as_number(3.14) == 3.14
    
    def test_convert_string(self):
        assert server._as_number("42") == 42.0
    
    def test_convert_string_with_whitespace(self):
        assert server._as_number("  10.5  ") == 10.5
    
    def test_convert_invalid_string(self):
        assert server._as_number("not a number") is None
    
    def test_convert_none(self):
        assert server._as_number(None) is None


class TestMathOperations:
    """Test math operations through the MCP server."""
    
    @pytest.mark.asyncio
    async def test_add_positive_numbers(self):
        # Call the decorated function's underlying function
        result = await server.add.fn(5, 3)
        assert result == 8.0
    
    @pytest.mark.asyncio
    async def test_add_negative_numbers(self):
        result = await server.add.fn(-5, -3)
        assert result == -8.0
    
    @pytest.mark.asyncio
    async def test_subtract_positive_numbers(self):
        result = await server.subtract.fn(10, 3)
        assert result == 7.0
    
    @pytest.mark.asyncio
    async def test_multiply_positive_numbers(self):
        result = await server.multiply.fn(5, 3)
        assert result == 15.0
    
    @pytest.mark.asyncio
    async def test_divide_positive_numbers(self):
        result = await server.divide.fn(10, 2)
        assert result == 5.0
    
    @pytest.mark.asyncio
    async def test_divide_by_zero(self):
        result = await server.divide.fn(10, 0)
        assert result == float('inf')
    
    @pytest.mark.asyncio
    async def test_power_positive_exponent(self):
        result = await server.power.fn(2, 3)
        assert result == 8.0
    
    @pytest.mark.asyncio
    async def test_modulus_positive_numbers(self):
        result = await server.modulus.fn(10, 3)
        assert result == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
