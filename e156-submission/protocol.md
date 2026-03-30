Mahmood Ahmad
Tahir Heart Institute
author@example.com

Protocol: DrivePulse - Live Folder Evidence Audit

This protocol describes a snapshot-backed live folder audit using the bundled `data-source/portfolio-data.snapshot.json` copied from `ResearchConstellation`. Eligible records are all indexed paths referenced by the 134 portfolio rows, with repeated paths deduplicated before scanning. The primary estimand is the proportion of specific indexed paths exposing git repositories on the live drive. Secondary outputs will report path existence, recency bands, README markers, test markers, paper artifacts, protocol artifacts, Pages markers, dirty git repos, and signal density by tier. The build process will emit `data-source/folder-scan.snapshot.json`, `data.json`, `data.js`, and a static dashboard for browser review. Reproducible public rebuilds will use the bundled scan snapshot by default, while `--live-scan` will refresh the telemetry against the current machine. Anticipated limitations include shallow directory traversal, machine specificity, generic root paths that cannot be scanned precisely, and no guarantee that a signal such as `index.html` or `README` reflects scientific maturity.

Outside Notes

Type: protocol
Primary estimand: proportion of specific indexed paths exposing git repositories
App: DrivePulse v0.1
Code: repository root, scripts/build_drive_pulse.py, data-source/folder-scan.snapshot.json, and data-source/portfolio-data.snapshot.json
Date: 2026-03-30
Validation: DRAFT

References

1. Sandve GK, Nekrutenko A, Taylor J, Hovig E. Ten simple rules for reproducible computational research. PLoS Comput Biol. 2013;9:e1003285.
2. Wilkinson MD, Dumontier M, Aalbersberg IJJ, et al. The FAIR Guiding Principles for scientific data management and stewardship. Sci Data. 2016;3:160018.
3. Page MJ, McKenzie JE, Bossuyt PM, et al. The PRISMA 2020 statement. BMJ. 2021;372:n71.

AI Disclosure

This protocol was drafted from versioned local artifacts and deterministic build logic. AI was used as a drafting and implementation assistant under author supervision, with the author retaining responsibility for scope, methods, and reporting choices.
