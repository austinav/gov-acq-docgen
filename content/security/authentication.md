---
id: sec.authn
title: User authentication and role-based access control
type: security-design
concerns: [cybersecurity]
elements: [SEC, ODS]
satisfies: [TFD-SRS-0400, TFD-SRS-0350]
controls: [IA-2, IA-5, AC-2, AC-3, AC-6]
references: [NIST-800-53]
order: 60
status: approved
version: 1.3
owner: Cybersecurity Engineering
---
Users authenticate to the Operator Display Subsystem with DoD PKI credentials on a Common Access Card (CAC). Certificate revocation status is checked on each login. There are no local passwords.

Authorization uses Role-Based Access Control (RBAC) with four roles, assigned by account managers through the enterprise identity system:

| Role | Permitted functions |
|---|---|
| Watchstander | View COP, annotate tracks, acknowledge alerts |
| Supervisor | Watchstander functions plus alert zone management |
| Maintainer | System health, configuration, and state transitions; no COP access |
| ISSO | Audit review and security configuration; no COP access |

Sessions lock after 15 minutes of inactivity.
