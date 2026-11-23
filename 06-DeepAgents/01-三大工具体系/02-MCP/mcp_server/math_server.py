from fastmcp import FastMCP

"""
    Math MCP服务器（stdio 传输）
"""

mcp = FastMCP("Math")

@mcp.tool()
def add(a: int, b: int) -> int:
    """2个数相加"""
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """2个数相乘"""
    return a * b

if __name__ == "__main__":
    mcp.run(transport="stdio")