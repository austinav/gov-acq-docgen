---
id: sec.hardening
title: Platform hardening and supply chain
type: security-design
concerns: [cybersecurity, maintainability]
elements: [HW-TFD-CSCI]
satisfies: [TFD-SRS-0440]
controls: [CM-6, CM-7, SI-2, SR-4, RA-5]
references: [CONTAINER-SRG, DODI-8510]
order: 80
status: approved
version: 1.0
owner: Cybersecurity Engineering
---
Container images are built from a hardened base image in the program software factory. Each build produces a Software Bill of Materials (SBOM), is scanned for vulnerabilities, and is signed. The orchestration platform admits only signed images from the program registry. Host operating systems and the container platform are configured per the applicable Security Technical Implementation Guides (STIGs) and the Container Platform Security Requirements Guide (SRG). Scan and compliance results feed the system's continuous Risk Management Framework (RMF) monitoring.
