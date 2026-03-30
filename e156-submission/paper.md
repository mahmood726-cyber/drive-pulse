Mahmood Ahmad
Tahir Heart Institute
author@example.com

Paper: DrivePulse - Live Folder Telemetry for the C Drive Evidence Portfolio

Can the portfolio atlas be linked back to live folder evidence rather than relying on index rows? We reused the bundled ResearchConstellation snapshot, deduplicated its 134 project records into 107 indexed paths, and refreshed those paths against the current C drive. DrivePulse v0.1 captured existence, recency, git state, README markers, test markers, paper artifacts, protocol artifacts, and Pages signals into a telemetry snapshot. All 105 specific filesystem paths were found live, and 85.7 percent (90 of 105) exposed git repositories while 79.0 percent (83 of 105) were already Pages-ready. Signal density peaked in tiers 4 and 7, whereas tier 12 collapsed to a generic root path and tier 8 remained operationally sparse. This shifts the next portfolio task from directory discovery toward index cleanup and evidence normalization, because the folders now exist but the metadata layer remains uneven. The scan improves operational visibility, but it is shallow, machine-specific, and cannot replace deeper repository or manuscript audits.

Outside Notes

Type: methods
Primary estimand: proportion of specific indexed paths exposing git repositories
App: DrivePulse v0.1
Code: repository root, scripts/build_drive_pulse.py, data-source/folder-scan.snapshot.json, and data-source/portfolio-data.snapshot.json
Date: 2026-03-30
Validation: PASS
Protocol: e156-submission/protocol.md
