---
id: exec.concept
title: Concept of execution
type: execution
concerns: [architecture, performance]
elements: [SIS, TCE, ODS, ARC]
satisfies: [TFD-SRS-0310, TFD-SRS-0500]
references: [IEEE-1588]
status: approved
version: 1.4
owner: Software Architecture
---
The {{csci.abbrev}} CSCI operates as a continuous data-driven pipeline. Processing proceeds as follows:

1. The Sensor Ingest Service receives radar and AIS messages, stamps each with UTC time from the Precision Time Protocol (PTP) reference, validates it, and publishes a normalized observation.
2. The Track Correlation Engine associates each observation with an existing track or initiates a tentative track, updates the track state estimate, and publishes a track update event.
3. The Operator Display Subsystem, the Track Archive Service, and the external C2 export function each consume track update events independently.

The CSCI has four states: **Startup**, **Operational**, **Degraded** (one or more sensor feeds lost; remaining feeds continue to be processed), and **Maintenance**. State transitions are commanded by an authorized Maintainer or triggered automatically by health monitoring.

The end-to-end latency budget from sensor receipt to display is 1.0 second (95th percentile), allocated as follows:

| Stage | Budget (ms) |
|---|---|
| Ingest and validation | 100 |
| Correlation and state update | 400 |
| Distribution via message broker | 100 |
| Display rendering | 400 |
