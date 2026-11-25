---
id: if.time
title: Time Reference Interface (IF-TIME-04)
type: interface
concerns: [interfaces, performance]
elements: [IF-TIME-04, SIS]
satisfies: [TFD-SRS-0500]
references: [IEEE-1588]
order: 40
status: approved
version: 1.0
owner: Systems Engineering
---
**Interfacing entities.** The site GPS-disciplined grandmaster clock (source) and all CSCI hosts (destination).

**Protocol.** IEEE 1588 Precision Time Protocol, default profile, on the sensor network segment. Hosts discipline their system clocks to the grandmaster; the Sensor Ingest Service reads system time when stamping observations.

**Accuracy.** Host clock offset is monitored continuously. If the offset exceeds 500 microseconds, the CSCI raises a time-quality alert and flags affected observations.
<!-- variant: summary -->
Inbound IEEE 1588 PTP time from the site GPS-disciplined grandmaster, keeping host clocks within 500 microseconds of UTC.
