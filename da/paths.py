"""
Shared Path Constants
=====================

Central location for path constants used across the data agent.
"""

from pathlib import Path

# Project root (parent of da/ directory)
PROJECT_ROOT = Path(__file__).parent.parent

# Knowledge directory at project root
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
TABLES_DIR = KNOWLEDGE_DIR / "tables"
BUSINESS_DIR = KNOWLEDGE_DIR / "business"
QUERIES_DIR = KNOWLEDGE_DIR / "queries"
