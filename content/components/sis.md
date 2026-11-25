---
id: comp.sis
title: Sensor Ingest Service (SIS)
type: component
concerns: [interfaces, cybersecurity, maintainability]
elements: [SIS, IF-RAD-01, IF-AIS-02, IF-TIME-04]
satisfies: [TFD-SRS-0200, TFD-SRS-0210, TFD-SRS-0220, TFD-SRS-0500]
controls: [SI-10]
references: [ASTERIX-048, NMEA-0183]
order: 10
status: approved
version: 2.2
owner: Ingest Team
---
The Sensor Ingest Service is a family of sensor adapters sharing a common framework. One adapter instance runs per physical sensor feed. Each adapter:

- receives raw sensor messages on its assigned interface;
- applies a UTC time stamp derived from the PTP time reference;
- validates message structure, field ranges, and plausibility (for example, reported positions outside the configured coverage area are rejected);
- converts accepted messages to the normalized observation schema; and
- publishes observations to the message broker.

Rejected messages are counted, sampled to a diagnostic log, and reported as a security-relevant event when the rejection rate exceeds a configurable threshold, since sustained malformed input may indicate spoofing or a compromised sensor.

**Units and accuracy.** Positions are normalized to WGS-84 latitude/longitude in decimal degrees; speeds to meters per second; courses to degrees true.
<!-- variant: summary -->
Receives, time-stamps, validates, and normalizes radar and AIS messages through one adapter per sensor feed, then publishes observations to the message broker.
