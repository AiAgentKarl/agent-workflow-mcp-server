"""Agent Workflow MCP Server — Wiederverwendbare Workflows für AI-Agents."""

from mcp.server.fastmcp import FastMCP
from src.tools.workflows import register_workflow_tools

mcp = FastMCP(
    "Agent Workflows",
    instructions="Reusable workflow templates for AI agents. Create, share, discover and rate multi-step workflows. Like recipes for agent tasks.",
)
register_workflow_tools(mcp)

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
