"""Validate Zensical TOML nav and local Markdown links without external dependencies."""
from __future__ import annotations

from pathlib import Path
import re
import sys
import tomllib
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CONFIG = tomllib.loads((ROOT / "zensical.toml").read_text(encoding="utf-8"))
PROJ = CONFIG["project"]


def walk_nav(nodes):
    for node in nodes:
        if isinstance(node, str):
            yield node
        elif isinstance(node, dict):
            for child in node.values():
                if isinstance(child, str):
                    yield child
                elif isinstance(child, list):
                    yield from walk_nav(child)
                else:
                    raise ValueError(f"Unsupported nav child: {child!r}")
        else:
            raise ValueError(f"Unsupported nav node: {node!r}")


def validate():
    errors = []
    md_files = sorted(DOCS.rglob("*.md"))
    referenced = list(walk_nav(PROJ.get("nav", [])))

    for entry in referenced:
        if not (DOCS / entry).is_file():
            errors.append(f"Menu link missing: {entry}")
    listed = set(referenced)
    for file in md_files:
        relative = file.relative_to(DOCS).as_posix()
        if relative not in listed:
            errors.append(f"File missing from nav: {relative}")
        text = file.read_text(encoding="utf-8")
        # Skip fenced blocks, which can include template links.
        text = re.sub(r"(?ms)^(```|~~~).*?^\1[^\n]*$", "", text)
        for match in re.finditer(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text):
            url = match.group(1).strip().split(' "', 1)[0]
            parts = urlsplit(url)
            if parts.scheme or url.startswith(("//", "#", "mailto:")):
                continue
            dest = unquote(parts.path)
            if not dest:
                continue
            local = (file.parent / dest).resolve()
            if not local.is_relative_to(DOCS.resolve()):
                errors.append(f"Link escapes docs root in {relative}: {url}")
                continue
            if not local.is_file():
                errors.append(f"Broken link in {relative}: {url}")

    if len(referenced) != len(set(referenced)):
        errors.append("Duplicate menu targets")
    for msg in errors:
        print('ERROR:', msg, file=sys.stderr)
    print(f"Validated {len(md_files)} Markdown pages and {len(referenced)} menu links.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(validate())
