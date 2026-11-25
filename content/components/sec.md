---
id: comp.sec
title: Security Services (SEC)
type: component
concerns: [cybersecurity]
elements: [SEC]
satisfies: [TFD-SRS-0400, TFD-SRS-0410, TFD-SRS-0430]
order: 50
status: approved
version: 1.4
owner: Cybersecurity Engineering
---
Security Services provides the identity, authorization, audit, and certificate management functions used by all other components. User authentication and authorization are described in {{ref:sec.authn}}; audit logging in {{ref:sec.audit}}; and workload certificate issuance in {{ref:dd.zero-trust}}.
<!-- variant: summary -->
Provides identity, authorization, audit, and certificate management to all other components.
