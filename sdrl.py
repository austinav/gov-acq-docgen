#!/usr/bin/env python3
"""SDRL content assembler.

Content units (content/**/*.md) are small, reusable blocks of text with YAML
metadata (type, concerns, system elements, requirements satisfied, controls
implemented, references cited). Templates (templates/*.yaml) describe a
deliverable's outline and pull units in by ID or by metadata query. This tool
validates the library, assembles documents, and writes them as Word files.

    uv run sdrl.py validate
    uv run sdrl.py build [sdd idd ...]
    uv run sdrl.py where-used [UNIT_ID]
    uv run sdrl.py find --concern cybersecurity --type interface
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent
VARIANT_RE = re.compile(r"^<!--\s*variant:\s*([\w-]+)\s*-->\s*$", re.M)
VAR_RE = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")
REF_RE = re.compile(r"\{\{\s*ref:([\w.-]+)\s*\}\}")
LIST_FIELDS = ("concerns", "elements", "satisfies", "controls", "references")
REQUIRED_FIELDS = ("id", "title", "type", "status", "version")


class BuildError(Exception):
    pass


def as_list(v) -> list:
    if v is None:
        return []
    return [str(x) for x in v] if isinstance(v, list) else [str(v)]


# --------------------------------------------------------------------------- library

@dataclass
class Unit:
    id: str
    meta: dict
    variants: dict[str, str]
    path: Path

    @property
    def title(self) -> str:
        return self.meta["title"]

    @property
    def status(self) -> str:
        return str(self.meta.get("status", "draft"))

    @property
    def version(self) -> str:
        return str(self.meta.get("version", ""))

    def tags(self, key: str) -> list[str]:
        return as_list(self.meta.get(key))

    def text(self, variant: str) -> str:
        return self.variants.get(variant, self.variants["full"])


class Library:
    def __init__(self, root: Path = ROOT):
        self.root = root
        reg = root / "registry"
        load = lambda n: yaml.safe_load((reg / n).read_text()) or {}
        self.vars = load("program.yaml")
        self.taxonomy = load("taxonomy.yaml")
        self.requirements = load("requirements.yaml")
        self.references = load("references.yaml")
        self.glossary = load("glossary.yaml")
        self.units: dict[str, Unit] = {}
        self.load_errors: list[str] = []
        for p in sorted((root / "content").rglob("*.md")):
            self._load_unit(p)

    def _load_unit(self, p: Path):
        rel = p.relative_to(self.root)
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", p.read_text(), re.S)
        if not m:
            self.load_errors.append(f"{rel}: missing YAML front matter")
            return
        meta = yaml.safe_load(m.group(1)) or {}
        missing = [f for f in REQUIRED_FIELDS if f not in meta]
        if missing:
            self.load_errors.append(f"{rel}: missing field(s) {', '.join(missing)}")
            return
        parts = VARIANT_RE.split(m.group(2))
        variants = {"full": parts[0].strip()}
        variants.update({n: t.strip() for n, t in zip(parts[1::2], parts[2::2])})
        uid = str(meta["id"])
        if uid in self.units:
            self.load_errors.append(f"{rel}: duplicate id {uid} (also {self.units[uid].path.relative_to(self.root)})")
            return
        self.units[uid] = Unit(uid, meta, variants, p)

    def query(self, q: dict) -> list[Unit]:
        def ok(u: Unit) -> bool:
            for key, want in q.items():
                have = u.tags(key) if key in LIST_FIELDS else as_list(u.meta.get(key))
                if not set(as_list(want)) & set(have):
                    return False
            return True
        hits = [u for u in self.units.values() if ok(u)]
        return sorted(hits, key=lambda u: (u.meta.get("order", 1000), u.id))

    def templates(self) -> dict[str, Path]:
        return {p.stem: p for p in sorted((self.root / "templates").glob("*.yaml"))}


def substitute(text: str, ctx: dict, where: str) -> str:
    def repl(m):
        cur = ctx
        for part in m.group(1).split("."):
            if not isinstance(cur, dict) or part not in cur:
                raise BuildError(f"{where}: unknown variable {{{{{m.group(1)}}}}}")
            cur = cur[part]
        return str(cur)
    return VAR_RE.sub(repl, text)


# --------------------------------------------------------------------------- assembly

@dataclass
class Node:
    title: str
    level: int
    content: list = field(default_factory=list)  # ("unit", Unit, variant) | ("text", str) | ("generate", name, opts)
    children: list["Node"] = field(default_factory=list)
    number: str = ""


class Assembly:
    """A template resolved against the library into a numbered outline."""

    def __init__(self, lib: Library, template: Path):
        self.lib = lib
        self.name = template.stem
        spec = yaml.safe_load(template.read_text())
        self.meta = spec["document"]
        self.statuses = set(as_list(self.meta.get("release_statuses", ["approved"])))
        self.warnings: list[str] = []
        self.excluded: dict[str, str] = {}
        self.ctx = {**lib.vars, "doc": self.meta}
        self.sections = [self._section(s, 1) for s in spec["sections"]]
        self._number(self.sections, "")
        self.usage: dict[str, list[tuple[str, str, str]]] = {}
        for node in self.walk():
            for item in node.content:
                if item[0] == "unit":
                    self.usage.setdefault(item[1].id, []).append((node.number, node.title, item[2]))

    # -- resolution
    def _released(self, u: Unit) -> bool:
        if u.status in self.statuses:
            return True
        self.excluded[u.id] = f"status '{u.status}' not released for {self.meta['id']}"
        return False

    def _unit_item(self, uid: str, variant: str):
        if uid not in self.lib.units:
            raise BuildError(f"{self.name}: unknown unit '{uid}'")
        u = self.lib.units[uid]
        if variant not in u.variants:
            raise BuildError(f"{self.name}: unit '{uid}' has no '{variant}' variant")
        return ("unit", u, variant) if self._released(u) else None

    def _section(self, spec: dict, level: int) -> Node:
        node = Node(spec["title"], level)
        before, after = [], []
        for b in spec.get("blocks", []):
            variant = b.get("variant", "full")
            if "unit" in b:
                item = self._unit_item(b["unit"], variant)
                if item:
                    node.content.append(item)
            elif "text" in b:
                node.content.append(("text", b["text"]))
            elif "generate" in b:
                node.content.append(("generate", b["generate"], b))
            elif "query" in b:
                hits = [u for u in self.lib.query(b["query"]) if self._released(u)]
                if not hits:
                    self.warnings.append(f"query {b['query']} in '{spec['title']}' matched no released units")
                items = [self._unit_item(u.id, variant) for u in hits]
                if b.get("as") == "subsections":
                    subs = [Node(it[1].title, level + 1, [it]) for it in items]
                    (after if b.get("after_children") else before).extend(subs)
                else:
                    node.content.extend(items)
            else:
                raise BuildError(f"{self.name}: unrecognized block {b}")
        node.children = before + [self._section(c, level + 1) for c in spec.get("sections", [])] + after
        return node

    def _number(self, nodes: list[Node], prefix: str):
        for i, n in enumerate(nodes, 1):
            n.number = f"{prefix}{i}"
            self._number(n.children, n.number + ".")

    def walk(self, nodes=None):
        for n in self.sections if nodes is None else nodes:
            yield n
            yield from self.walk(n.children)

    # -- derived data
    def used_units(self) -> list[Unit]:
        return [self.lib.units[uid] for uid in self.usage]

    def sections_for(self, uid: str) -> str:
        return ", ".join(dict.fromkeys(num for num, _, _ in self.usage.get(uid, [])))

    def sub(self, text: str, where: str) -> str:
        """Resolve {{ref:unit.id}} cross-references, then {{variables}}."""
        def ref(m):
            uid = m.group(1)
            if uid not in self.lib.units:
                raise BuildError(f"{self.name}/{where}: cross-reference to unknown unit '{uid}'")
            title = self.lib.units[uid].title
            if uid in self.usage:
                return f"Section {self.usage[uid][0][0]} ({title})"
            return f"*{title}*"
        return substitute(REF_RE.sub(ref, text), self.ctx, f"{self.name}/{where}")

    def all_text(self) -> str:
        parts = [self.meta["title"], self.sub(self.meta.get("subject", ""), "subject")]
        for n in self.walk():
            parts.append(n.title)
            for item in n.content:
                if item[0] == "unit":
                    parts.append(self.sub(item[1].text(item[2]), item[1].id))
                elif item[0] == "text":
                    parts.append(self.sub(item[1], n.title))
        return "\n".join(parts)


# --------------------------------------------------------------------------- generators

def gen_references(a: Assembly):
    keys = list(dict.fromkeys(as_list(a.meta.get("cite")) + [r for u in a.used_units() for r in u.tags("references")]))
    rows = sorted(([a.lib.references[k]["number"], a.lib.references[k]["title"]] for k in keys), key=lambda r: r[0])
    intro = "The following documents form a part of this document to the extent specified herein."
    return [("para", intro), ("table", ["Document number", "Title"], rows)]


def gen_traceability(a: Assembly):
    trace: dict[str, list[str]] = {}
    for u in a.used_units():
        for r in u.tags("satisfies"):
            trace.setdefault(r, []).extend(num for num, _, _ in a.usage[u.id])
    rows = [[r, a.lib.requirements.get(r, "(not in SRS extract)"), ", ".join(sorted(set(s), key=_numkey))]
            for r, s in sorted(trace.items())]
    out = [("para", "The following table traces CSCI requirements to the sections of this document that address them."),
           ("table", ["Requirement", "Requirement text", "Section(s)"], rows)]
    open_reqs = sorted(set(a.lib.requirements) - set(trace))
    if open_reqs and a.meta.get("report_unaddressed", True):
        out.append(("para", "CSCI requirements not addressed in this document: " + ", ".join(open_reqs) + "."))
    return out


def gen_acronyms(a: Assembly):
    text = a.all_text()
    rows = [[k, v] for k, v in sorted(a.lib.glossary.items(), key=lambda kv: kv[0].lower())
            if re.search(rf"(?<![\w-]){re.escape(k)}s?(?![\w-])", text)]
    return [("table", ["Acronym", "Meaning"], rows)]


def gen_element_table(a: Assembly, kind: str):
    els = {k: v for k, v in a.lib.taxonomy["elements"].items() if v.get("kind") == kind}
    extra = [c for c in dict.fromkeys(c for v in els.values() for c in v) if c not in ("name", "kind")]
    headers = ["Identifier", "Name"] + [c.capitalize() for c in extra]
    return [("table", headers, [[k, v["name"]] + [str(v.get(c, "")) for c in extra] for k, v in els.items()])]


def gen_control_matrix(a: Assembly):
    ctl: dict[str, list[Unit]] = {}
    for u in a.used_units():
        for c in u.tags("controls"):
            ctl.setdefault(c, []).append(u)
    rows = [[c, "; ".join(u.title for u in us), ", ".join(sorted({a.sections_for(u.id) for u in us}, key=_numkey))]
            for c, us in sorted(ctl.items(), key=lambda kv: _ctlkey(kv[0]))]
    return [("para", "NIST SP 800-53 controls implemented by the design elements in this document:"),
            ("table", ["Control", "Implemented by", "Section(s)"], rows)]


def gen_provenance(a: Assembly):
    rows = [[u.id, u.version, u.status, str(u.meta.get("owner", "")), a.sections_for(u.id)]
            for u in sorted(a.used_units(), key=lambda u: u.id)]
    out = [("para", "This document was assembled from the controlled content units listed below. "
                    "A change to any listed unit requires re-issue of this document."),
           ("table", ["Content unit", "Version", "Status", "Owner", "Section(s)"], rows)]
    if a.excluded:
        out.append(("para", "Excluded from this release: " +
                    "; ".join(f"{k} ({v})" for k, v in sorted(a.excluded.items())) + "."))
    return out


def _numkey(s: str):
    return [int(x) if x.isdigit() else x for x in re.split(r"[.,\s]+", s) if x]


def _ctlkey(c: str):
    fam, _, num = c.partition("-")
    return (fam, int(num) if num.isdigit() else 0)


GENERATORS = {
    "references": lambda a, o: gen_references(a),
    "traceability": lambda a, o: gen_traceability(a),
    "acronyms": lambda a, o: gen_acronyms(a),
    "element_table": lambda a, o: gen_element_table(a, o["kind"]),
    "control_matrix": lambda a, o: gen_control_matrix(a),
    "provenance": lambda a, o: gen_provenance(a),
}


# --------------------------------------------------------------------------- Word output

FONT = "Arial"
INLINE_RE = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)")


class DocxWriter:
    def __init__(self, a: Assembly):
        self.a = a
        self.doc = Document()
        self._styles()
        self._page_setup()

    # -- setup
    def _styles(self):
        st = self.doc.styles
        normal = st["Normal"]
        normal.font.name, normal.font.size = FONT, Pt(11)
        normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        normal.paragraph_format.space_after = Pt(6)
        for lvl, size in zip(range(1, 6), (14, 12, 11, 11, 11)):
            h = st[f"Heading {lvl}"]
            h.font.name, h.font.size, h.font.bold = FONT, Pt(size), True
            h.font.italic = False
            h.font.color.rgb = RGBColor(0, 0, 0)
            rpr = h.element.get_or_add_rPr()
            rpr.get_or_add_rFonts().set(qn("w:asciiTheme"), "")  # drop theme font so Arial applies
            for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
                rpr.rFonts.attrib.pop(qn(attr), None)
            rpr.rFonts.set(qn("w:ascii"), FONT)
            rpr.rFonts.set(qn("w:hAnsi"), FONT)
            h.paragraph_format.space_before = Pt(12 if lvl == 1 else 9)
            h.paragraph_format.space_after = Pt(6)
            h.paragraph_format.keep_with_next = True
        st["List Bullet"].font.name = FONT
        # Ask Word to refresh the TOC and fields when the file is opened.
        upd = OxmlElement("w:updateFields")
        upd.set(qn("w:val"), "true")
        self.doc.settings.element.append(upd)

    def _page_setup(self):
        m = self.a.meta
        sec = self.doc.sections[0]
        sec.left_margin = sec.right_margin = Inches(1)
        sec.top_margin = sec.bottom_margin = Inches(1)
        hp = sec.header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._run(hp, self.a.lib.vars["classification"], bold=True, size=10)
        fp = sec.footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._run(fp, f"{m['doc_number']} Rev {m.get('revision', '-')}    |    Page ", size=9)
        self._field(fp, "PAGE", "1", size=9)
        fp2 = sec.footer.add_paragraph()
        fp2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._run(fp2, self.a.lib.vars["classification"], bold=True, size=10)

    # -- primitives
    def _run(self, p, text, bold=False, italic=False, size=None, mono=False, color=None):
        r = p.add_run(text)
        r.bold, r.italic = bold or None, italic or None
        if size:
            r.font.size = Pt(size)
        if mono:
            r.font.name = "Consolas"
        if color:
            r.font.color.rgb = RGBColor.from_string(color)
        return r

    def _field(self, p, instr: str, placeholder: str, size=None):
        def fld(t):
            e = OxmlElement("w:fldChar")
            e.set(qn("w:fldCharType"), t)
            return e
        r = p.add_run()
        r._r.append(fld("begin"))
        r2 = p.add_run()
        it = OxmlElement("w:instrText")
        it.set(qn("xml:space"), "preserve")
        it.text = f" {instr} "
        r2._r.append(it)
        p.add_run()._r.append(fld("separate"))
        r3 = self._run(p, placeholder, size=size)
        p.add_run()._r.append(fld("end"))
        return r3

    def inline(self, p, text: str, size=None):
        for tok in INLINE_RE.split(text):
            if not tok:
                continue
            if tok.startswith("**"):
                self._run(p, tok[2:-2], bold=True, size=size)
            elif tok.startswith("`"):
                self._run(p, tok[1:-1], mono=True, size=size)
            elif tok.startswith("*") and len(tok) > 2:
                self._run(p, tok[1:-1], italic=True, size=size)
            else:
                self._run(p, tok, size=size)

    def table(self, headers, rows):
        t = self.doc.add_table(rows=1, cols=len(headers))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for cell, h in zip(t.rows[0].cells, headers):
            cell.text = ""
            self.inline(cell.paragraphs[0], h, size=9.5)
            for r in cell.paragraphs[0].runs:
                r.bold = True
            shd = OxmlElement("w:shd")
            shd.set(qn("w:val"), "clear")
            shd.set(qn("w:fill"), "D9D9D9")
            cell._tc.get_or_add_tcPr().append(shd)
        trpr = t.rows[0]._tr.get_or_add_trPr()
        hdr = OxmlElement("w:tblHeader")
        hdr.set(qn("w:val"), "true")
        trpr.append(hdr)
        for row in rows:
            cells = t.add_row().cells
            for cell, val in zip(cells, row):
                self.inline(cell.paragraphs[0], str(val), size=9.5)
        # Column widths proportional to content length (bounded), across 6.5 in.
        all_rows = [headers] + [list(map(str, r)) for r in rows]
        longest_word = lambda c: max(len(w) for r in all_rows for w in (r[c].split() or ['']))
        weight = [max(longest_word(c) * 1.6, min(max(len(r[c]) for r in all_rows), 60), 6)
                  for c in range(len(headers))]
        total = sum(weight)
        t.autofit = False
        for col, w in zip(t.columns, weight):
            col.width = Inches(6.5 * w / total)
        for row in t.rows:
            for cell, w in zip(row.cells, weight):
                cell.width = Inches(6.5 * w / total)
                for p in cell.paragraphs:
                    p.paragraph_format.space_after = Pt(2)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def markdown(self, text: str):
        lines = text.split("\n")
        i = 0
        is_bullet = lambda l: re.match(r"^\s*[-*] ", l)
        is_num = lambda l: re.match(r"^\s*\d+\. ", l)
        is_table = lambda l: l.lstrip().startswith("|")
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1
            elif is_table(line):
                rows = []
                while i < len(lines) and is_table(lines[i]):
                    cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                    if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                        rows.append(cells)
                    i += 1
                self.table(rows[0], rows[1:])
            elif is_bullet(line) or is_num(line):
                numbered, n = bool(is_num(line)), 0
                while i < len(lines) and lines[i].strip() and (is_bullet(lines[i]) or is_num(lines[i]) or lines[i].startswith(" ")):
                    if is_bullet(lines[i]) or is_num(lines[i]):
                        n += 1
                        item = re.sub(r"^\s*([-*]|\d+\.) ", "", lines[i])
                        i += 1
                        while i < len(lines) and lines[i].startswith("  ") and not (is_bullet(lines[i]) or is_num(lines[i])):
                            item += " " + lines[i].strip()
                            i += 1
                        if numbered:
                            p = self.doc.add_paragraph()
                            p.paragraph_format.left_indent = Inches(0.35)
                            p.paragraph_format.first_line_indent = Inches(-0.25)
                            self._run(p, f"{n}.  ")
                        else:
                            p = self.doc.add_paragraph(style="List Bullet")
                        p.paragraph_format.space_after = Pt(3)
                        self.inline(p, item)
                    else:
                        i += 1
            else:
                para = []
                while i < len(lines) and lines[i].strip() and not (is_table(lines[i]) or is_bullet(lines[i]) or is_num(lines[i])):
                    para.append(lines[i].strip())
                    i += 1
                self.inline(self.doc.add_paragraph(), " ".join(para))

    # -- document parts
    def cover(self):
        a, m, v = self.a, self.a.meta, self.a.lib.vars
        d = self.doc
        for _ in range(4):
            d.add_paragraph()
        p = d.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._run(p, m["title"].upper(), bold=True, size=22)
        p = d.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._run(p, a.sub(m.get("subject", ""), "subject"), size=14)
        p = d.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._run(p, f"{v['system']['name']} ({v['system']['abbrev']})", size=12)
        for _ in range(3):
            d.add_paragraph()
        rows = [
            ("Document number", f"{m['doc_number']} Rev {m.get('revision', '-')}"),
            ("Data item", m.get("data_item", "")),
            ("SDRL item", m.get("sdrl", "")),
            ("Contract number", v["contract"]["number"]),
            ("Prepared for", v["contract"]["acquirer"]),
            ("Prepared by", v["contract"]["contractor"]),
            ("Date", dt.date.today().strftime("%d %B %Y")),
        ]
        t = d.add_table(rows=0, cols=2)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for k, val in rows:
            c = t.add_row().cells
            self._run(c[0].paragraphs[0], k, bold=True, size=10)
            self._run(c[1].paragraphs[0], str(val), size=10)
            c[0].width, c[1].width = Inches(1.8), Inches(3.6)
        for _ in range(5):
            d.add_paragraph()
        p = d.add_paragraph()
        self._run(p, v["distribution"].strip(), size=9, bold=True)
        d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def toc(self):
        p = self.doc.add_paragraph()
        self._run(p, "TABLE OF CONTENTS", bold=True, size=14)
        p = self.doc.add_paragraph()
        self._field(p, 'TOC \\o "1-3" \\h \\z \\u',
                    "Right-click here and choose Update Field to build the table of contents.")
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def body(self):
        for node in self.a.walk():
            self.doc.add_heading(f"{node.number}  {node.title}", level=min(node.level, 5))
            if not node.content and not node.children:
                self.doc.add_paragraph("Not applicable.")
            for item in node.content:
                kind = item[0]
                if kind == "text":
                    self.markdown(self.a.sub(item[1], node.title))
                elif kind == "unit":
                    u, variant = item[1], item[2]
                    if u.status != "approved":
                        p = self.doc.add_paragraph()
                        self._run(p, f"[{u.status.upper()} CONTENT: {u.id} v{u.version}]", italic=True, size=9, color="C00000")
                    self.markdown(self.a.sub(u.text(variant), u.id))
                elif kind == "generate":
                    for part in GENERATORS[item[1]](self.a, item[2]):
                        if part[0] == "para":
                            self.markdown(part[1])
                        else:
                            self.table(part[1], part[2])

    def save(self, path: Path):
        self.cover()
        self.toc()
        self.body()
        self.doc.core_properties.title = f"{self.a.meta['title']} {self.a.sub(self.a.meta.get('subject', ''), 'subject')}"
        self.doc.core_properties.subject = self.a.meta.get("sdrl", "")
        self.doc.save(path)


# --------------------------------------------------------------------------- commands

def validate(lib: Library) -> tuple[list[str], list[str]]:
    errors, warnings = list(lib.load_errors), []
    tx = lib.taxonomy
    checks = {
        "type": (tx["content_types"], "content type"),
        "concerns": (tx["concerns"], "concern"),
        "elements": (tx["elements"], "element"),
        "satisfies": (lib.requirements, "requirement"),
        "references": (lib.references, "reference"),
    }
    ctx = {**lib.vars, "doc": {"sdrl": "", "title": "", "id": ""}}
    for u in lib.units.values():
        where = u.path.relative_to(lib.root)
        for key, (vocab, label) in checks.items():
            for val in as_list(u.meta.get(key)):
                if val not in vocab:
                    errors.append(f"{where}: unknown {label} '{val}'")
        for c in u.tags("controls"):
            if not re.fullmatch(r"[A-Z]{2}-\d+(\(\d+\))?", c):
                errors.append(f"{where}: malformed control id '{c}'")
        for name, text in u.variants.items():
            for ref in REF_RE.findall(text):
                if ref not in lib.units:
                    errors.append(f"{where}[{name}]: cross-reference to unknown unit '{ref}'")
            try:
                substitute(REF_RE.sub("", text), ctx, f"{where}[{name}]")
            except BuildError as e:
                errors.append(str(e))
        if u.status != "approved":
            warnings.append(f"{u.id}: status is '{u.status}'")
    used: set[str] = set()
    for name, path in lib.templates().items():
        try:
            a = Assembly(lib, path)
            used |= set(a.usage) | set(a.excluded)
            for node in a.walk():
                for item in node.content:
                    if item[0] == "generate" and item[1] not in GENERATORS:
                        errors.append(f"templates/{name}.yaml: unknown generator '{item[1]}'")
            for r in as_list(a.meta.get("cite")):
                if r not in lib.references:
                    errors.append(f"templates/{name}.yaml: unknown reference '{r}'")
            a.all_text()
            warnings += [f"{name}: {w}" for w in a.warnings]
        except (BuildError, KeyError) as e:
            errors.append(f"templates/{name}.yaml: {e}")
    for uid in sorted(set(lib.units) - used):
        warnings.append(f"{uid}: not used by any template")
    covered = {r for u in lib.units.values() for r in u.tags("satisfies")}
    for r in sorted(set(lib.requirements) - covered):
        warnings.append(f"{r}: no content unit claims to satisfy this requirement")
    return errors, warnings


def cmd_validate(lib, args):
    errors, warnings = validate(lib)
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"\n{len(lib.units)} units, {len(lib.templates())} templates: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


def cmd_build(lib, args):
    errors, _ = validate(lib)
    if errors:
        print("Validation failed; run `sdrl.py validate` for details.")
        return 1
    tpls = lib.templates()
    names = args.templates or list(tpls)
    out = lib.root / "out"
    out.mkdir(exist_ok=True)
    for name in names:
        if name not in tpls:
            print(f"Unknown template '{name}'. Available: {', '.join(tpls)}")
            return 1
        a = Assembly(lib, tpls[name])
        path = out / f"{a.meta['doc_number']}.docx"
        DocxWriter(a).save(path)
        print(f"Built {path.relative_to(lib.root)}  ({len(a.usage)} units, {sum(1 for _ in a.walk())} sections)")
        for w in a.warnings:
            print(f"  warn: {w}")
        for k, v in a.excluded.items():
            print(f"  excluded: {k} ({v})")
    return 0


def cmd_where_used(lib, args):
    assemblies = [Assembly(lib, p) for p in lib.templates().values()]
    ids = [args.unit] if args.unit else sorted(lib.units)
    lines = ["| Unit | Ver | Status | Used in |", "|---|---|---|---|"]
    for uid in ids:
        if uid not in lib.units:
            print(f"Unknown unit '{uid}'")
            return 1
        u = lib.units[uid]
        uses = []
        for a in assemblies:
            for num, _, variant in a.usage.get(uid, []):
                uses.append(f"{a.meta['id']} §{num}" + ("" if variant == "full" else f" ({variant})"))
            if uid in a.excluded:
                uses.append(f"{a.meta['id']}: excluded")
        lines.append(f"| {uid} | {u.version} | {u.status} | {'; '.join(uses) or '—'} |")
    report = "\n".join(lines)
    print(report)
    if not args.unit:
        (lib.root / "out").mkdir(exist_ok=True)
        (lib.root / "out" / "where-used.md").write_text("# Where-used report\n\n" + report + "\n")
    return 0


def cmd_find(lib, args):
    q = {k: v for k, v in {"type": args.type, "concerns": args.concern, "elements": args.element,
                           "controls": args.control, "satisfies": args.requirement, "status": args.status}.items() if v}
    for u in lib.query(q):
        print(f"{u.id:28} {u.status:9} v{u.version:5} {u.title}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("validate", help="check units and templates against the registries")
    b = sp.add_parser("build", help="assemble documents into out/*.docx")
    b.add_argument("templates", nargs="*", help="template names (default: all)")
    w = sp.add_parser("where-used", help="show which documents/sections use each unit")
    w.add_argument("unit", nargs="?")
    f = sp.add_parser("find", help="query units by metadata")
    for opt in ("type", "concern", "element", "control", "requirement", "status"):
        f.add_argument(f"--{opt}", action="append")
    args = ap.parse_args(argv)
    lib = Library()
    try:
        return {"validate": cmd_validate, "build": cmd_build, "where-used": cmd_where_used, "find": cmd_find}[args.cmd](lib, args)
    except BuildError as e:
        print(f"ERROR {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
