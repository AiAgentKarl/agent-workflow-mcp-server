"""Workflow-Tools — Wiederverwendbare Arbeitsabläufe für AI-Agents."""

from mcp.server.fastmcp import FastMCP
from src import db


def register_workflow_tools(mcp: FastMCP):

    @mcp.tool()
    async def create_workflow(
        name: str, description: str, category: str, steps: list[dict],
        required_tools: list[str] = None, author: str = None, tags: list[str] = None,
    ) -> dict:
        """Einen Workflow-Template erstellen und teilen.

        Args:
            name: Eindeutiger Workflow-Name
            description: Was der Workflow macht
            category: Kategorie (z.B. "research", "analysis", "due-diligence")
            steps: Liste von Schritten [{\"step\": 1, \"action\": \"...\", \"tool\": \"...\"}]
            required_tools: Welche MCP-Tools werden benötigt
            author: Autor des Workflows
            tags: Tags für bessere Auffindbarkeit
        """
        return db.create_workflow(name, description, category, steps, required_tools, author=author, tags=tags)

    @mcp.tool()
    async def get_workflow(name: str) -> dict:
        """Einen Workflow-Template abrufen und ausführen.

        Args:
            name: Name des Workflows
        """
        result = db.get_workflow(name)
        if result:
            return result
        return {"found": False, "name": name}

    @mcp.tool()
    async def search_workflows(query: str = None, category: str = None, limit: int = 10) -> dict:
        """Workflows suchen.

        Args:
            query: Suchbegriff
            category: Kategorie-Filter
            limit: Maximale Ergebnisse
        """
        results = db.search_workflows(query, category, limit)
        return {"results_count": len(results), "workflows": results}

    @mcp.tool()
    async def rate_workflow(name: str, rating: int, review: str = None) -> dict:
        """Workflow bewerten (1-5 Sterne).

        Args:
            name: Workflow-Name
            rating: 1-5 Sterne
            review: Optionaler Text
        """
        return db.rate_workflow(name, rating, review)

    @mcp.tool()
    async def popular_workflows(limit: int = 10) -> dict:
        """Beliebteste Workflows anzeigen.

        Args:
            limit: Anzahl
        """
        return {"popular": db.get_popular(limit)}

    @mcp.tool()
    async def workflow_categories() -> dict:
        """Alle Workflow-Kategorien auflisten."""
        return {"categories": db.list_categories()}
