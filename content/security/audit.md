---
id: sec.audit
title: Audit logging
type: security-design
concerns: [cybersecurity]
elements: [SEC]
satisfies: [TFD-SRS-0430]
controls: [AU-2, AU-3, AU-9, AU-12]
references: [NIST-800-53]
order: 70
status: approved
version: 1.1
owner: Cybersecurity Engineering
---
Every component emits audit records for security-relevant events: authentication success and failure, authorization denials, role and configuration changes, state transitions, data purges, and sensor input rejection thresholds being exceeded. Each record contains the event type, UTC time, user or workload identity, source component, and outcome.

Security Services forwards audit records to the enterprise Security Information and Event Management (SIEM) system over TLS within 60 seconds and retains a local copy for 30 days in append-only storage that only the ISSO role can read.
