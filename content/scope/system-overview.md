---
id: scope.system-overview
title: System overview
type: scope
concerns: [architecture]
elements: [HW-TFD-CSCI]
references: [HW-CSS-SSDD]
status: approved
version: 1.3
owner: Systems Engineering
---
The {{system.abbrev}} provides persistent maritime domain awareness for port approaches and coastal waters. The system fuses surface search radar and Automatic Identification System (AIS) data into a Common Operational Picture (COP) for harbor operations watchstanders, and shares that picture with a regional Command and Control (C2) system.

The {{csci.abbrev}} CSCI is the software core of the {{system.abbrev}}. It receives sensor data, correlates observations into tracks, presents the COP to operators, archives track history, and exports tracks to external consumers.

The system is acquired by {{contract.acquirer}} and developed by {{contract.contractor}} under contract {{contract.number}}. It is deployed at three harbor operations centers, each operating an independent instance of the {{csci.abbrev}} CSCI. The full system architecture is documented in the System/Subsystem Design Description.
<!-- variant: summary -->
The {{system.abbrev}} fuses radar and AIS data into a Common Operational Picture (COP) for harbor watchstanders and shares tracks with a regional Command and Control (C2) system. The {{csci.abbrev}} CSCI is the software core of the system.
