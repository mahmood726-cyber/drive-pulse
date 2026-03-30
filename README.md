# DrivePulse

DrivePulse is a new standalone project that scans the indexed C-drive portfolio paths for live folder evidence.

## Why this exists

The portfolio atlas and its derivative projects already know the declared project rows. What they do not know by default is whether the underlying folders:

- still exist
- were touched recently
- contain git history
- expose README, test, paper, protocol, or Pages signals

DrivePulse fills that gap by performing one live scan, bundling the resulting scan snapshot in-repo, and serving the findings as a static dashboard and E156 bundle.

## Outputs

- `data-source/folder-scan.snapshot.json` - bundled live scan snapshot
- `data.json` and `data.js` - dashboard payloads
- `index.html` - static folder telemetry dashboard
- `e156-submission/` - paper, protocol, metadata, and reader page

## Rebuild

To rebuild the dashboard from the bundled scan snapshot:

`python C:\Users\user\DrivePulse\scripts\build_drive_pulse.py`

To refresh the scan against the current live drive and rewrite the bundled scan snapshot:

`python C:\Users\user\DrivePulse\scripts\build_drive_pulse.py --live-scan`

## Scope note

The live scan is intentionally shallow and fast. It captures operational signals, not a perfect forensic inventory, and should be interpreted as portfolio telemetry rather than exhaustive compliance evidence.
