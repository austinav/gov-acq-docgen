---
id: dd.architecture-style
title: Service-oriented containerized architecture
type: design-decision
concerns: [architecture, maintainability, availability]
elements: [HW-TFD-CSCI]
satisfies: [TFD-SRS-0100, TFD-SRS-0110]
order: 10
status: approved
version: 2.0
owner: Software Architecture
---
The {{csci.abbrev}} CSCI is implemented as a set of independently deployable services running in containers on a hardened container orchestration platform. Services communicate asynchronously through a publish/subscribe message broker using versioned, schema-validated messages.

This decision was made to:

- isolate sensor-specific parsing from correlation logic, so that new sensor types are added by deploying a new ingest adapter rather than modifying the Track Correlation Engine;
- allow individual services to be restarted or scaled without interrupting the operational picture; and
- align with the program's container-based software factory and its continuous authorization pipeline.

**Alternatives considered.** A monolithic application was rejected because it would couple sensor changes to full CSCI regression testing and re-accreditation.
