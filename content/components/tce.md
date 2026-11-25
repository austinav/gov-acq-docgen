---
id: comp.tce
title: Track Correlation Engine (TCE)
type: component
concerns: [architecture, performance]
elements: [TCE]
satisfies: [TFD-SRS-0300, TFD-SRS-0310, TFD-SRS-0110]
order: 20
status: approved
version: 3.0
owner: Fusion Team
---
The Track Correlation Engine maintains the fused track picture. For each observation it performs gating against existing tracks, assignment using a global nearest-neighbor algorithm, and state estimation using an Interacting Multiple Model (IMM) filter with constant-velocity and coordinated-turn motion models.

AIS observations carry a vessel identity (MMSI). When a radar track and an AIS track are associated for three consecutive updates, the TCE merges them into a single fused track that retains the AIS identity and the radar kinematics.

The TCE is sensor-agnostic: it consumes only normalized observations and a per-sensor error model supplied as configuration. Adding a new sensor type requires a new ingest adapter and error model, not a TCE code change.

The TCE is sized for 2,000 simultaneous tracks with 50% processing margin on the target hardware.
<!-- variant: summary -->
Associates observations with tracks, estimates track state with an IMM filter, and fuses radar and AIS tracks into the authoritative track picture.
