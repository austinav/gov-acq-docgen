---
id: if.ais
title: AIS Receiver Interface (IF-AIS-02)
type: interface
concerns: [interfaces, cybersecurity]
elements: [IF-AIS-02, SIS]
satisfies: [TFD-SRS-0210, TFD-SRS-0220]
controls: [SI-10]
references: [NMEA-0183, ITU-M1371]
order: 20
status: approved
version: 1.1
owner: Ingest Team
---
**Interfacing entities.** The AIS base station (source) and the Sensor Ingest Service (destination).

**Transport.** TCP stream initiated by the Sensor Ingest Service to the base station. Reconnection is attempted every 5 seconds after loss of connection.

**Format.** NMEA 0183 AIVDM sentences encapsulating ITU-R M.1371 messages. The CSCI processes message types 1, 2, 3 (Class A position), 5 (static and voyage data), 18 (Class B position), and 24 (Class B static data). Other types are discarded.

**Integrity.** AIS is an unauthenticated broadcast and vessel-reported data may be spoofed. Every sentence checksum is verified, and decoded positions are checked for kinematic plausibility against the vessel's track history before use.
<!-- variant: summary -->
Inbound TCP stream of NMEA 0183 AIVDM sentences from the AIS base station; vessel-reported data is treated as untrusted and checked for plausibility.
