---
id: dd.track-store
title: Single authoritative track store
type: design-decision
concerns: [architecture, data-management]
elements: [TCE, ARC]
satisfies: [TFD-SRS-0300, TFD-SRS-0360]
order: 20
status: approved
version: 1.1
owner: Software Architecture
---
The Track Correlation Engine (TCE) is the only component permitted to create, update, or delete tracks. All other components consume track state as a read-only event stream. Each track update is published as an immutable event carrying a monotonically increasing sequence number, which the Track Archive Service persists for replay and after-action analysis.

This prevents divergent track pictures between the operator display, the archive, and external C2 consumers.
