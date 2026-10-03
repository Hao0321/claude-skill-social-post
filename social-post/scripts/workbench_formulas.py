"""Read installed formula headings without publicizing a private library."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from workbench_contract import FORMULA_ALIASES, FORMULA_IDS
from workbench_store import safe_path


def formula_catalog(root: Path) -> list[dict[str, str]]:
    directory = safe_path(root, "references/formulas")
    if not directory.exists():
        return []
    rows = []
    for identity in sorted(FORMULA_IDS):
        base = FORMULA_ALIASES.get(identity, identity)
        path = safe_path(root, "references/formulas/" + base + ".md")
        if not path.is_file():
            continue
        if path.stat().st_size > 65536:
            raise ValueError("formula exceeds bound")
        source = path.read_text(encoding="utf-8-sig")
        if identity in FORMULA_ALIASES and not re.search(r"\bF0?" + str(int(identity[1:3])) + identity[-1] + r"\b", source, re.I):
            continue
        if identity == "F06" and re.search(r"\bF6[ab]\b", source):
            continue
        title = next((line.lstrip("# ").strip() for line in source.splitlines()
                      if re.match(r"^#{1,6} ", line)), identity)
        if identity in FORMULA_ALIASES:
            variant = re.compile(r"\bF0?" + str(int(identity[1:3])) + identity[-1] + r"\b", re.I)
            title = next((line.lstrip("# ").strip() for line in source.splitlines()
                          if re.match(r"^#{1,6} ", line) and variant.search(line)), title)
        title = "".join(char for char in title
                        if unicodedata.category(char) not in {"So", "Sk"}
                        and char not in "\ufe0f\u200d")[:160].strip()
        rows.append({"id": identity, "label": identity + " / " + title,
                     "reference": "references/formulas/" + base + ".md"})
    return rows
