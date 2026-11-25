# gov-acq-docgen
Framework for managing content and generating documents required in government acquisition contracts be submitted by direct suppliers and subs

Build SDRL deliverables (SDD, IDD, cybersecurity summaries, …) from a library of
small, reusable, controlled pieces of content, instead of maintaining each Word
document by hand.

Example system: **HARBORWATCH Coastal Surveillance System**, Track Fusion and
Display CSCI (fictional).

```
uv run sdrl.py validate            # check everything against the registries
uv run sdrl.py build               # -> out/HW-TFD-SDD.docx, HW-TFD-IDD.docx, HW-TFD-CDS.docx
uv run sdrl.py where-used          # which deliverables/sections use each unit (impact analysis)
uv run sdrl.py where-used if.c2
uv run sdrl.py find --concern cybersecurity --type interface
```

## The model

```
registry/                 controlled vocabularies + shared data
  program.yaml            variables: system/CSCI names, contract no., classification
  taxonomy.yaml           content types, concerns, system elements (CSCs, interfaces)
  requirements.yaml       SRS extract (for traceability)
  references.yaml         reference catalog (cited by key)
  glossary.yaml           acronyms
content/**/*.md           CONTENT UNITS: one topic each, Markdown + YAML metadata
templates/*.yaml          DOCUMENT TEMPLATES: outline + rules for what goes where
sdrl.py                   validate / assemble / render to .docx
```

### Content unit

One reusable block of text about one thing. Its metadata creates the links:

```yaml
---
id: if.c2                          # stable ID that templates reference
title: External C2 Track Interface (IF-C2-03)   # becomes the heading when used as a subsection
type: interface                    # what kind of content (taxonomy.content_types)
concerns: [interfaces, cybersecurity, performance]   # the concerns it addresses
elements: [IF-C2-03, TCE, SEC]     # the parts of the system it describes
satisfies: [TFD-SRS-0320, TFD-SRS-0420]  # drives the traceability matrix
controls: [SC-8, SC-13, IA-3]      # drives the NIST 800-53 control matrix
references: [COT-SCHEMA, RFC-8446] # drives Section 2 "Referenced documents"
status: approved                   # release gating per deliverable
version: 2.0
owner: Integration Team
---
Full text ... uses {{csci.abbrev}} variables and {{ref:sec.audit}} cross-references
<!-- variant: summary -->
One-paragraph version for documents that need less detail.
```

* **Variants**: the same topic at different levels of detail. The SDD uses the
  `summary` of an interface in §4.3, and the IDD uses the `full` text.
* **Variables** (`{{system.name}}`) keep the text independent of any one
  program or CSCI.
* **Cross-references** (`{{ref:unit-id}}`) resolve to the section number in
  *whichever document* the text lands in. If the target isn't in that
  document, they fall back to the title.

### Template

The outline of a deliverable, normally the DID's paragraph structure. Each
section pulls content in by:

| Block | Meaning |
|---|---|
| `unit: id` (+ `variant`) | a specific unit |
| `query: {type: …, concerns: …, elements: …}` | every released unit whose metadata matches; `as: subsections` makes one numbered subsection per unit |
| `text: …` | document-specific connective text |
| `generate: references \| traceability \| acronyms \| element_table \| control_matrix \| provenance` | computed from the units actually in the document |

`release_statuses` controls which unit statuses a deliverable accepts. The
formal SDD takes only `approved` units. The internal cyber summary also accepts
`draft` units, which are flagged in red where they appear.

### Why this structure

* **Write once, use many times**: the C2 interface text appears in the SDD,
  the IDD, and the Cybersecurity Design Summary, in different sections and at
  different levels of detail.
* **Assemble by concern**: the Cybersecurity Design Summary has almost no
  hand-picked content. It is "everything tagged `cybersecurity`", so a new
  security mechanism shows up there automatically.
* **Derived sections are never stale**: referenced documents, acronyms,
  requirements traceability, the control matrix, and the content provenance
  table are computed at build time.
* **Change impact**: `where-used` shows every deliverable and section that
  must be re-issued when a unit changes.
* **Plain text in git**: units diff and review cleanly in pull requests, and
  approval status lives next to the content.

## Next steps (not built yet)

* Images/diagrams as units (`type: figure`, with an asset file and caption) and
  auto-numbered figure and table captions.
* A corporate Word template (`.dotx`) for styles, so formatting matches the
  program's standard.
* Element-scoped queries per CSCI: one template generating an SDD for each CSCI.
* A database and web UI on top of the same model, once the schema settles.
