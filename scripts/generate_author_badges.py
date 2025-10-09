#!/usr/bin/env python
"""
Generate author badges/banners for README.md with Gravatar, name, affiliation, and ORCID.

Usage:
    python scripts/generate_author_badges.py
"""
import hashlib
import yaml
from pathlib import Path
from typing import List, Dict


def get_gravatar_url(email: str, size: int = 100, gravatar_email: str = None) -> str:
    """Generate Gravatar URL from email address.

    Args:
        email: Display email address
        size: Avatar size in pixels
        gravatar_email: Optional different email to use for Gravatar lookup
                       (useful when display email differs from Gravatar registered email)
    """
    lookup_email = gravatar_email if gravatar_email else email
    email_hash = hashlib.md5(lookup_email.lower().encode('utf-8')).hexdigest()
    return f"https://secure.gravatar.com/avatar/{email_hash}?s={size}&d=identicon"


def generate_author_card_html(author: Dict[str, str]) -> str:
    """Generate HTML for a single author card."""
    gravatar_url = get_gravatar_url(
        author['email'],
        gravatar_email=author.get('gravatar_email')
    )
    orcid_badge = ""

    if author.get('orcid'):
        orcid_badge = f'<a href="https://orcid.org/{author["orcid"]}" target="_blank"><img src="https://orcid.org/assets/vectors/orcid.logo.icon.svg" width="16" height="16" alt="ORCID"></a>'

    html = f"""
<div align="center" style="display: inline-block; margin: 10px; padding: 20px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 50%; width: 180px; height: 180px; position: relative;">
    <a href="mailto:{author['email']}">
        <img src="{gravatar_url}" alt="{author['name']}" style="border-radius: 50%; width: 100px; height: 100px; border: 3px solid white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    </a>
    <h4 style="margin: 8px 0 3px 0; font-size: 0.95em;">{author['name']}</h4>
    <p style="margin: 3px 0; font-size: 0.75em; color: #555;">{author['affiliation']}</p>
    <p style="margin: 5px 0; font-size: 1.2em;">
        {orcid_badge if orcid_badge else ""}
        <a href="mailto:{author['email']}" style="text-decoration: none;">📧</a>
    </p>
    {f'<p style="margin: 3px 0; font-size: 0.7em; font-style: italic; color: #666;">{author.get("role", "")}</p>' if author.get('role') else ""}
</div>
"""
    return html.strip()


def generate_author_table_markdown(authors: List[Dict[str, str]]) -> str:
    """Generate Markdown table for authors."""
    header = "| Developer | Affiliation | ORCID | Contribution |\n"
    header += "|-----------|-------------|-------|--------------|"

    rows = []
    for author in authors:
        name = author['name']
        affiliation = author['affiliation']

        if author.get('orcid'):
            orcid = f"[{author['orcid']}](https://orcid.org/{author['orcid']})"
        else:
            orcid = "_N/A_"

        role = author.get('role', '_Contributor_')

        rows.append(f"| {name} | {affiliation} | {orcid} | {role} |")

    return header + "\n" + "\n".join(rows)


def generate_author_cards_html(authors: List[Dict[str, str]]) -> str:
    """Generate HTML for all author cards in a flex container."""
    cards = [generate_author_card_html(author) for author in authors]

    html = """
<div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; margin: 20px 0;">
"""
    for card in cards:
        html += card + "\n"

    html += "</div>"

    return html


def load_authors_from_yaml(yaml_path: Path) -> List[Dict[str, str]]:
    """Load author information from YAML file."""
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    return data.get('authors', [])


def main():
    """Generate author badges and update README."""
    # Define authors
    authors = [
        {
            "name": "Paul Gierz",
            "email": "paul.gierz@awi.de",
            "affiliation": "Alfred Wegener Institute (AWI)",
            "orcid": "0000-0002-4512-087X",
            "role": "Lead Developer, Architecture"
        },
        # Add more authors here or load from YAML
    ]

    # Check if authors.yaml exists
    authors_yaml = Path(__file__).parent.parent / "AUTHORS.yaml"
    if authors_yaml.exists():
        authors = load_authors_from_yaml(authors_yaml)

    # Generate both formats
    print("=" * 80)
    print("MARKDOWN TABLE FORMAT")
    print("=" * 80)
    print(generate_author_table_markdown(authors))
    print()

    print("=" * 80)
    print("HTML CARD FORMAT (for README)")
    print("=" * 80)
    print(generate_author_cards_html(authors))
    print()

    # Write to file for easy copying
    output_file = Path(__file__).parent.parent / "AUTHORS.md"
    with open(output_file, 'w') as f:
        f.write("# Authors\n\n")
        f.write("## Table Format\n\n")
        f.write(generate_author_table_markdown(authors))
        f.write("\n\n## Card Format (HTML)\n\n")
        f.write(generate_author_cards_html(authors))

    print(f"✅ Author badges written to: {output_file}")


if __name__ == "__main__":
    main()
