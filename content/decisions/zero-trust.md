---
id: dd.zero-trust
title: Zero trust service communication
type: design-decision
concerns: [cybersecurity, architecture]
elements: [HW-TFD-CSCI, SEC]
satisfies: [TFD-SRS-0410]
controls: [SC-7, SC-8, IA-3, AC-4]
references: [NIST-800-207, NIST-800-53]
order: 30
status: approved
version: 1.2
owner: Cybersecurity Engineering
---
No component of the {{csci.abbrev}} CSCI trusts another on the basis of network location. Every service holds a short-lived X.509 workload identity certificate issued by Security Services, and all service-to-service connections use mutually authenticated TLS 1.3. Platform network policies are default-deny; each permitted flow is declared explicitly alongside the service's deployment configuration and reviewed as part of the change control process.
<!-- variant: summary -->
All service-to-service connections use mutually authenticated TLS 1.3 with short-lived workload certificates, and platform network policies are default-deny.
