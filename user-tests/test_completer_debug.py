#!/usr/bin/env python
"""Debug version of completer test."""

from prompt_toolkit.document import Document

from src.cli.completion import GlobPatternCompleter


def test_completion(text: str):
    """Test what completions we get for a given text."""
    print(f"\nTesting: {repr(text)}")
    print("=" * 60)

    completer = GlobPatternCompleter()
    document = Document(text, len(text))

    completions = list(completer.get_completions(document, None))

    if completions:
        print(f"Found {len(completions)} completions:")
        for comp in completions:
            print(f"  - {comp.text!r} (display: {comp.display!r})")
    else:
        print("No completions found")

    print()


if __name__ == "__main__":
    # Test various inputs
    test_completion("ssh://")
    test_completion("ssh://mn5")
    test_completion("ssh://mn5:/")
    test_completion("ssh://mn5:/hom")
    test_completion("/")
    test_completion("/home")
