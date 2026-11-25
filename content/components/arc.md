---
id: comp.arc
title: Track Archive Service (ARC)
type: component
concerns: [data-management, cybersecurity]
elements: [ARC]
satisfies: [TFD-SRS-0360]
controls: [SC-28, AU-9]
order: 40
status: approved
version: 1.2
owner: Data Team
---
The Track Archive Service persists every track update event to an encrypted time-series database and supports time-window queries and replay at up to 10x real time. Data older than the configured retention period (default 90 days) is purged by a daily job; purge actions are audited.
<!-- variant: summary -->
Persists track update events for 90 days and supports query and replay.
