from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS = ROOT / "assets/diagrams"
SVG_NS = "{http://www.w3.org/2000/svg}"


def test_canonical_svgs_are_well_formed_self_contained_and_accessible():
    svgs = sorted(DIAGRAMS.glob("*.svg"))
    assert {path.name for path in svgs} == {
        "capability-compatibility.svg",
        "run-evidence-flow.svg",
        "system-architecture.svg",
    }

    for path in svgs:
        root = ET.parse(path).getroot()
        assert root.tag == f"{SVG_NS}svg"
        assert root.attrib.get("viewBox")
        assert root.attrib.get("role") == "img"
        assert root.find(f"{SVG_NS}title") is not None
        assert root.find(f"{SVG_NS}desc") is not None

        ids = [element.attrib["id"] for element in root.iter() if "id" in element.attrib]
        assert len(ids) == len(set(ids)), f"{path}: duplicate XML IDs"

        text = path.read_text(encoding="utf-8")
        assert not re.search(r"(?:href|src)=[\"']https?://", text)
        assert "<script" not in text.lower()


def test_each_canonical_svg_is_embedded_in_documentation():
    docs = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md")), ROOT / "playbooks/README.md"]
    )
    for svg in DIAGRAMS.glob("*.svg"):
        assert svg.name in docs, f"{svg.name} is not embedded in canonical documentation"
