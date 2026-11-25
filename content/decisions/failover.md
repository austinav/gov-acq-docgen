---
id: dd.failover
title: Active/standby failover
type: design-decision
concerns: [availability, performance]
elements: [TCE, ODS]
satisfies: [TFD-SRS-0100]
order: 50
status: draft
version: 0.3
owner: Software Architecture
---
Each stateful service runs as an active/standby pair across two physical hosts. The standby instance replays the track event stream continuously and assumes the active role within 5 seconds of a detected failure. Operators may see a brief pause in track updates during failover; no track history is lost.
