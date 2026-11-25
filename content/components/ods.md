---
id: comp.ods
title: Operator Display Subsystem (ODS)
type: component
concerns: [architecture]
elements: [ODS]
satisfies: [TFD-SRS-0350, TFD-SRS-0310]
order: 30
status: approved
version: 1.5
owner: HMI Team
---
The Operator Display Subsystem is a browser-based Human-Machine Interface (HMI) served from within the CSCI enclave. It renders the COP on a chart background, provides track detail and history views, and raises alerts for configured conditions such as a vessel entering a restricted area.

Display content and available actions are tailored to the authenticated user's role. Watchstanders view and annotate tracks; Supervisors additionally manage alert zones; Maintainers access system health views but not the operational picture.
<!-- variant: summary -->
Browser-based HMI that renders the COP, track details, and alerts, with content tailored to the user's role.
