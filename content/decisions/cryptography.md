---
id: dd.cryptography
title: Validated cryptography
type: design-decision
concerns: [cybersecurity]
elements: [HW-TFD-CSCI, SEC]
satisfies: [TFD-SRS-0420]
controls: [SC-13, SC-12, SC-28]
references: [FIPS-140-3, RFC-8446]
order: 40
status: approved
version: 1.0
owner: Cybersecurity Engineering
---
All cryptographic functions in the {{csci.abbrev}} CSCI are performed by FIPS 140-3 validated modules operating in their approved mode. Data in transit is protected with TLS 1.3 restricted to AES-256-GCM cipher suites. Track archive data at rest is encrypted with AES-256. Root and intermediate signing keys are generated and held in a Hardware Security Module (HSM) and are never exported.
