"""
Entry point for running the MCP server as a module
Usage: python -m infra_manager_mcp
"""

from .server import run

if __name__ == "__main__":
    run()
