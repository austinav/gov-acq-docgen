---
id: if.radar
title: Radar Sensor Interface (IF-RAD-01)
type: interface
concerns: [interfaces]
elements: [IF-RAD-01, SIS]
satisfies: [TFD-SRS-0200]
references: [ASTERIX-048]
order: 10
status: approved
version: 1.3
owner: Ingest Team
---
**Interfacing entities.** Surface search radar processors (source) and the Sensor Ingest Service (destination).

**Transport.** UDP multicast on a dedicated sensor network segment. Each radar processor publishes to a unique multicast group. The interface is one-way; the CSCI sends nothing to the radar.

**Format.** ASTERIX Category 048 target reports, one or more records per datagram.

**Timing.** One report per detected target per antenna scan (nominal scan period 2.5 seconds).

| Data item | ASTERIX field | Units / range | Used for |
|---|---|---|---|
| Data source identifier | I048/010 | SAC/SIC | Sensor attribution |
| Time of day | I048/140 | seconds since midnight UTC, 1/128 s | Latency monitoring only |
| Measured position (polar) | I048/040 | range 0-256 NM, azimuth 0-360 deg | Track update |
| Track number | I048/161 | 0-4095 | Radar-local association hint |
| Calculated velocity | I048/200 | speed, heading | Track initiation |
<!-- variant: summary -->
Inbound UDP multicast of ASTERIX Category 048 target reports from surface search radar processors to the Sensor Ingest Service, one report per target per scan.
