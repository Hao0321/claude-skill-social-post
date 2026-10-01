"""Read installed formula headings without publicizing a private library."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from workbench_contract import FORMULA_IDS
from workbench_store import safe_path


def formula_catalog(root: Path) -> list[dict[str, str]]:
    directory = safe_path(root, "references/formulas")
    if not directory.exists():
        return []
    rows = []
    for identity in sorted(FORMULA_IDS):
        path = safe_path(root, "references/formulas/" + identity + ".md")
        if not path.is_file():
            continue
        if path.stat().st_size > 65536:
            raise ValueError("formula exceeds bound")
        source = path.read_text(encoding="utf-8-sig")
        title = next((line.lstrip("# ").strip() for line in source.splitlines()
                      if re.match(r"^#{1,6} ", line)), identity)
        title = "".join(char for char in title
                        if unicodedata.category(char) not in {"So", "Sk"}
                        and char not in "\ufe0f\u200d")[:160].strip()
        rows.append({"id": identity, "label": identity + " / " + title,
                     "reference": "references/formulas/" + identity + ".md"})
    return rows
