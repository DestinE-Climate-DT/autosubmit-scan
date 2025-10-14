#!/usr/bin/env python
"""Quick test script for the fsspec path completer."""

from prompt_toolkit.shortcuts import prompt

from src.cli.completion import GlobPatternCompleter


def main():
    """Test the completer interactively."""
    print("Testing FsspecPathCompleter with tab completion")
    print("=" * 60)
    print("Try these:")
    print("  - Type 'ssh://' and press Tab to see protocol suggestions")
    print("  - Type '/' and press Tab to see local files")
    print("  - Type 'ssh://user@host/' and press Tab (will fail without SSH)")
    print("  - Type a path ending with '/' and press Tab for glob patterns")
    print("=" * 60)
    print()

    completer = GlobPatternCompleter()

    try:
        file_uri = prompt(
            "File URI: ",
            completer=completer,
            complete_while_typing=False,
        )
        print(f"\nYou entered: {file_uri}")
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled")


if __name__ == "__main__":
    main()
