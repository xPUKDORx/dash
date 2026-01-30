"""
Save Validated Query Tool
=========================

Enhanced tool for saving validated SQL queries to the knowledge base.
Enables the self-learning loop where successful queries become retrievable patterns.

Features:
- Validates query safety (SELECT/WITH only)
- Stores rich metadata for retrieval
- Tracks data quality notes and business context
"""

import json

from agno.knowledge import Knowledge
from agno.knowledge.reader.text_reader import TextReader
from agno.tools import tool
from agno.utils.log import logger


def create_save_validated_query_tool(knowledge: Knowledge):
    """Factory function that creates the save_validated_query tool with knowledge injected.

    Args:
        knowledge: The knowledge base to save queries to.

    Returns:
        A tool function that can save validated queries.
    """

    @tool
    def save_validated_query(
        name: str,
        question: str,
        query: str,
        summary: str | None = None,
        tables_used: list[str] | None = None,
        data_quality_notes: str | None = None,
        business_context: str | None = None,
    ) -> str:
        """Save a validated SQL query and its explanation to the knowledge base.

        Call this tool ONLY after:
        1. The query has been executed successfully
        2. The user has confirmed the results are correct
        3. The user has agreed to save the query

        This enables the self-learning loop: future similar questions will retrieve
        this validated query pattern, improving accuracy over time.

        Args:
            name: Short descriptive name for the query (e.g., "championship_wins_by_driver").
            question: The original natural language question from the user.
            query: The exact SQL query that was executed and validated.
            summary: Brief explanation of what the query does and what it returns.
            tables_used: List of tables used in the query for easier retrieval.
            data_quality_notes: Data quality issues encountered and how they were handled
                (e.g., "position is TEXT in drivers_championship - used string comparison").
            business_context: Business logic or domain knowledge applied
                (e.g., "Constructors Championship started in 1958").

        Returns:
            str: Status message indicating success or failure.

        Example:
            save_validated_query(
                name="most_race_wins_2019",
                question="Who won the most races in 2019?",
                query="SELECT name, COUNT(*) AS wins FROM race_wins WHERE...",
                summary="Counts race wins per driver for a given year",
                tables_used=["race_wins"],
                data_quality_notes="Used TO_DATE for date parsing in race_wins table",
                business_context="race_wins only contains first-place finishes"
            )
        """
        # Validate required fields
        if not name or not name.strip():
            return "Error: Query name is required."

        if not question or not question.strip():
            return "Error: Original question is required."

        sql_stripped = (query or "").strip()
        if not sql_stripped:
            return "Error: SQL query is required."

        # Security check: only allow SELECT queries (including CTEs)
        sql_lower = sql_stripped.lower().lstrip()
        if not sql_lower.startswith("select") and not sql_lower.startswith("with"):
            return "Error: Only SELECT queries (including CTEs) can be saved."

        # Check for dangerous keywords even in SELECT queries
        dangerous_keywords = [
            "drop",
            "delete",
            "truncate",
            "insert",
            "update",
            "alter",
            "create",
            "grant",
            "revoke",
        ]
        for keyword in dangerous_keywords:
            # Check for keyword as whole word (not part of column/table name)
            if f" {keyword} " in f" {sql_lower} ":
                return f"Error: Query contains potentially dangerous keyword: {keyword}"

        # Build payload with type marker for retrieval
        payload = {
            "type": "validated_query",
            "name": name.strip(),
            "question": question.strip(),
            "query": sql_stripped,
            "summary": summary.strip() if summary else None,
            "tables_used": tables_used or [],
            "data_quality_notes": data_quality_notes.strip() if data_quality_notes else None,
            "business_context": business_context.strip() if business_context else None,
        }

        # Remove None values for cleaner storage
        payload = {k: v for k, v in payload.items() if v is not None}

        logger.info(f"Saving validated query to knowledge base: {name}")

        try:
            knowledge.add_content(
                name=name.strip(),
                text_content=json.dumps(payload, ensure_ascii=False, indent=2),
                reader=TextReader(),
                skip_if_exists=True,
            )
        except Exception as e:
            logger.error(f"Failed to save query: {e}")
            return f"Error: Failed to save query - {e}"

        return (
            f"Successfully saved query '{name}' to knowledge base. It will be retrieved for similar future questions."
        )

    return save_validated_query
