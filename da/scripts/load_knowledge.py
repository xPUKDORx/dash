"""
Load Knowledge
==============

Loads table metadata, query patterns, and business definitions into
the Data Agent's knowledge base.

Usage:
    python -m da.scripts.load_knowledge
"""

import sys

from da.paths import KNOWLEDGE_DIR


def load_knowledge(verbose: bool = True) -> bool:
    """Load knowledge files into the Data Agent's knowledge base.

    Args:
        verbose: Print progress messages.

    Returns:
        True if knowledge loaded successfully, False otherwise.
    """
    # Import here to avoid circular imports
    from da.agent import data_agent_knowledge

    if verbose:
        print(f"Loading knowledge from: {KNOWLEDGE_DIR}")
        print()

    # Load each subdirectory
    subdirs = ["tables", "queries", "business"]
    total_files = 0

    for subdir in subdirs:
        subdir_path = KNOWLEDGE_DIR / subdir
        if not subdir_path.exists():
            if verbose:
                print(f"  {subdir}/: (not found)")
            continue

        # Get non-hidden files only
        files = [f for f in subdir_path.iterdir() if f.is_file() and not f.name.startswith(".")]

        if verbose:
            print(f"  {subdir}/: {len(files)} files")
            for f in files:
                print(f"    - {f.name}")

        if files:
            try:
                data_agent_knowledge.insert(
                    name=f"Data Agent Knowledge - {subdir}",
                    path=str(subdir_path),
                )
                total_files += len(files)
            except OSError as e:
                if verbose:
                    print(f"    ERROR: Failed to load {subdir}: {e}")
                return False

    if verbose:
        print()
        print(f"Knowledge loaded successfully! ({total_files} files)")

    return True


def main() -> int:
    """Main entry point."""
    print("Loading knowledge into Data Agent knowledge base")
    print()

    success = load_knowledge(verbose=True)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
