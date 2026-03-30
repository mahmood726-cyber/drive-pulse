from __future__ import annotations

import argparse
import json
import os
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO_SOURCE = PROJECT_ROOT / "data-source" / "portfolio-data.snapshot.json"
SCAN_SNAPSHOT = PROJECT_ROOT / "data-source" / "folder-scan.snapshot.json"
DATA_JSON = PROJECT_ROOT / "data.json"
DATA_JS = PROJECT_ROOT / "data.js"

MANIFEST_FILES = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "description",
    "cargo.toml",
    "environment.yml",
    "environment.yaml",
}
PAPER_FILES = {"paper.md", "paper.json", "manuscript.md"}
PROTOCOL_FILES = {"protocol.md"}


def load_portfolio() -> dict[str, object]:
    return json.loads(PORTFOLIO_SOURCE.read_text(encoding="utf-8"))


def is_specific_windows_path(raw_path: str) -> bool:
    if not raw_path or not raw_path.startswith("C:\\"):
        return False
    return raw_path not in {"C:\\Projects\\", "C:\\"}


def normalize_path(raw_path: str) -> Path | None:
    if not is_specific_windows_path(raw_path):
        return None
    cleaned = raw_path.rstrip("\\")
    return Path(cleaned)


def iso_from_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(timespec="seconds")


def git_probe(path: Path) -> dict[str, object]:
    if not ((path / ".git").exists() or (path / ".git").is_file()):
        return {"hasGit": False, "gitBranch": "", "gitHead": "", "gitDirty": False}

    result = {"hasGit": True, "gitBranch": "", "gitHead": "", "gitDirty": False}
    try:
        head = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        if head.returncode == 0:
            result["gitHead"] = head.stdout.strip()
        branch = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        if branch.returncode == 0:
            result["gitBranch"] = branch.stdout.strip()
        dirty = subprocess.run(
            ["git", "-C", str(path), "status", "--porcelain", "--untracked-files=no"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        if dirty.returncode == 0:
            result["gitDirty"] = bool(dirty.stdout.strip())
    except (subprocess.TimeoutExpired, OSError):
        pass
    return result


def scan_tree(path: Path, max_depth: int = 2, max_files: int = 1500) -> dict[str, object]:
    ext_counts: Counter[str] = Counter()
    sample_files: list[str] = []
    has_protocol = False
    has_paper = False
    has_tests = False
    scanned_files = 0

    root_depth = len(path.parts)
    for current_root, dirnames, filenames in os.walk(path):
        current_path = Path(current_root)
        depth = len(current_path.parts) - root_depth
        if depth >= max_depth:
            dirnames[:] = []

        lower_dirnames = {name.lower() for name in dirnames}
        if "tests" in lower_dirnames or any("test" in name for name in lower_dirnames):
            has_tests = True

        for filename in filenames:
            lower_name = filename.lower()
            ext_counts[Path(filename).suffix.lower() or "<none>"] += 1
            if scanned_files < 24:
                try:
                    rel = str((current_path / filename).relative_to(path)).replace("\\", "/")
                    sample_files.append(rel)
                except ValueError:
                    sample_files.append(filename)
            if lower_name in PROTOCOL_FILES:
                has_protocol = True
            if lower_name in PAPER_FILES or "manuscript" in lower_name:
                has_paper = True
            if "test" in lower_name or lower_name.startswith("pytest"):
                has_tests = True
            scanned_files += 1
            if scanned_files >= max_files:
                return {
                    "extensionCounts": dict(ext_counts),
                    "sampleFiles": sample_files,
                    "hasProtocolArtifact": has_protocol,
                    "hasPaperArtifact": has_paper,
                    "hasTestsMarker": has_tests,
                    "scannedFiles": scanned_files,
                    "scanTruncated": True,
                }

    return {
        "extensionCounts": dict(ext_counts),
        "sampleFiles": sample_files,
        "hasProtocolArtifact": has_protocol,
        "hasPaperArtifact": has_paper,
        "hasTestsMarker": has_tests,
        "scannedFiles": scanned_files,
        "scanTruncated": False,
    }


def classify_activity(age_days: int | None) -> str:
    if age_days is None:
        return "unknown"
    if age_days <= 7:
        return "fresh"
    if age_days <= 30:
        return "recent"
    if age_days <= 180:
        return "warm"
    return "stale"


def scan_path(raw_path: str, linked_projects: list[dict[str, object]]) -> dict[str, object]:
    candidate = normalize_path(raw_path)
    if candidate is None:
        return {
            "path": raw_path,
            "specificPath": False,
            "exists": False,
            "reason": "Generic or non-filesystem path; live scan skipped.",
            "linkedProjectCount": len(linked_projects),
            "linkedProjects": [project["name"] for project in linked_projects[:8]],
            "linkedTiers": sorted({project["tierShortName"] for project in linked_projects}),
            "operationalSignals": 0,
            "activityBand": "generic",
        }

    exists = candidate.exists()
    if not exists:
        return {
            "path": raw_path,
            "specificPath": True,
            "exists": False,
            "reason": "Indexed path was not found on the live drive.",
            "linkedProjectCount": len(linked_projects),
            "linkedProjects": [project["name"] for project in linked_projects[:8]],
            "linkedTiers": sorted({project["tierShortName"] for project in linked_projects}),
            "operationalSignals": 0,
            "activityBand": "missing",
        }

    stat = candidate.stat()
    age_days = int((datetime.now(timezone.utc).timestamp() - stat.st_mtime) // 86400)
    entry_names = []
    if candidate.is_dir():
        try:
            entry_names = sorted(item.name for item in candidate.iterdir())[:80]
        except OSError:
            entry_names = []

    lower_entries = {name.lower() for name in entry_names}
    has_readme = any(name.startswith("readme") for name in lower_entries)
    has_manifest = any(name in MANIFEST_FILES for name in lower_entries)
    has_index_html = "index.html" in lower_entries or ("docs" in lower_entries and (candidate / "docs" / "index.html").exists())
    has_nojekyll = ".nojekyll" in lower_entries
    has_e156 = "e156-submission" in lower_entries
    tree_scan = scan_tree(candidate) if candidate.is_dir() else {
        "extensionCounts": {},
        "sampleFiles": [],
        "hasProtocolArtifact": False,
        "hasPaperArtifact": False,
        "hasTestsMarker": False,
        "scannedFiles": 0,
        "scanTruncated": False,
    }
    git_info = git_probe(candidate) if candidate.is_dir() else {"hasGit": False, "gitBranch": "", "gitHead": "", "gitDirty": False}

    signals = sum(
        1
        for flag in [
            git_info["hasGit"],
            has_readme,
            has_manifest,
            tree_scan["hasTestsMarker"],
            tree_scan["hasPaperArtifact"],
            tree_scan["hasProtocolArtifact"],
            has_index_html or has_nojekyll,
            has_e156,
        ]
        if flag
    )

    return {
        "path": raw_path,
        "specificPath": True,
        "exists": True,
        "isDirectory": candidate.is_dir(),
        "lastModified": iso_from_timestamp(stat.st_mtime),
        "ageDays": age_days,
        "activityBand": classify_activity(age_days),
        "linkedProjectCount": len(linked_projects),
        "linkedProjects": [project["name"] for project in linked_projects[:8]],
        "linkedTiers": sorted({project["tierShortName"] for project in linked_projects}),
        "hasReadme": has_readme,
        "hasManifest": has_manifest,
        "hasIndexHtml": has_index_html,
        "hasNoJekyll": has_nojekyll,
        "hasE156Bundle": has_e156,
        "hasProtocolArtifact": tree_scan["hasProtocolArtifact"],
        "hasPaperArtifact": tree_scan["hasPaperArtifact"],
        "hasTestsMarker": tree_scan["hasTestsMarker"],
        "extensionCounts": tree_scan["extensionCounts"],
        "sampleFiles": tree_scan["sampleFiles"],
        "scannedFiles": tree_scan["scannedFiles"],
        "scanTruncated": tree_scan["scanTruncated"],
        "operationalSignals": signals,
        **git_info,
    }


def build_live_scan(portfolio: dict[str, object]) -> dict[str, object]:
    grouped: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
    for project in portfolio["portfolio"]:
        grouped[project["path"]].append(project)

    scans = [scan_path(path, projects) for path, projects in sorted(grouped.items())]
    specific = [item for item in scans if item.get("specificPath")]
    overview = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sourcePath": portfolio["overview"]["sourcePath"],
        "trackedProjects": portfolio["overview"]["trackedProjects"],
        "uniquePaths": len(scans),
        "specificPaths": len(specific),
        "genericPaths": len(scans) - len(specific),
        "existingSpecificPaths": sum(1 for item in specific if item.get("exists")),
        "missingSpecificPaths": sum(1 for item in specific if not item.get("exists")),
        "gitRepos": sum(1 for item in specific if item.get("hasGit")),
        "dirtyGitRepos": sum(1 for item in specific if item.get("gitDirty")),
        "readmePaths": sum(1 for item in specific if item.get("hasReadme")),
        "testMarkedPaths": sum(1 for item in specific if item.get("hasTestsMarker")),
        "paperPaths": sum(1 for item in specific if item.get("hasPaperArtifact")),
        "protocolPaths": sum(1 for item in specific if item.get("hasProtocolArtifact")),
        "pagesReadyPaths": sum(1 for item in specific if item.get("hasIndexHtml") or item.get("hasNoJekyll")),
        "freshOrRecentPaths": sum(1 for item in specific if item.get("activityBand") in {"fresh", "recent"}),
        "evidenceRichPaths": sum(1 for item in specific if item.get("operationalSignals", 0) >= 4),
    }
    return {"overview": overview, "scans": scans}


def build_dashboard(scan_snapshot: dict[str, object], portfolio: dict[str, object]) -> dict[str, object]:
    scans = scan_snapshot["scans"]
    specific_existing = [item for item in scans if item.get("specificPath") and item.get("exists")]
    tier_scores: defaultdict[str, list[int]] = defaultdict(list)
    tier_missing: defaultdict[str, int] = defaultdict(int)
    for item in scans:
        for tier in item.get("linkedTiers", []):
            tier_scores[tier].append(item.get("operationalSignals", 0))
            if item.get("specificPath") and not item.get("exists"):
                tier_missing[tier] += 1

    tier_rows = [
        {
            "tier": tier,
            "meanSignals": round(sum(values) / len(values), 1) if values else 0.0,
            "paths": len(values),
            "missing": tier_missing.get(tier, 0),
        }
        for tier, values in tier_scores.items()
    ]

    recent = sorted(
        [item for item in specific_existing if item.get("activityBand") in {"fresh", "recent"}],
        key=lambda item: (item.get("ageDays", 999999), item["path"]),
    )
    rich = sorted(
        [item for item in specific_existing if item.get("operationalSignals", 0) >= 4],
        key=lambda item: (-item.get("operationalSignals", 0), item["path"]),
    )
    missing = [item for item in scans if item.get("specificPath") and not item.get("exists")]
    generic = [item for item in scans if not item.get("specificPath")]

    return {
        "project": {
            "name": "DrivePulse",
            "version": "0.1.0",
            "generatedAt": scan_snapshot["overview"]["generatedAt"],
            "sourcePath": scan_snapshot["overview"]["sourcePath"],
            "designBasis": [
                "Live filesystem scan captured into a bundled snapshot",
                "Git, README, test, paper, and Pages signal extraction",
                "Static GitHub Pages dashboard",
            ],
        },
        "metrics": scan_snapshot["overview"],
        "tierSignals": sorted(tier_rows, key=lambda item: (-item["meanSignals"], item["tier"])),
        "recentPaths": recent[:12],
        "evidenceRichPaths": rich[:12],
        "missingPaths": missing[:12],
        "genericPaths": generic[:12],
        "activityBreakdown": [
            {"band": band.title(), "count": count}
            for band, count in sorted(
                Counter(item.get("activityBand", "unknown") for item in scans if item.get("specificPath")).items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
        "signalBreakdown": [
            {"label": label, "count": count}
            for label, count in [
                ("Git repos", scan_snapshot["overview"]["gitRepos"]),
                ("Dirty git repos", scan_snapshot["overview"]["dirtyGitRepos"]),
                ("README paths", scan_snapshot["overview"]["readmePaths"]),
                ("Test-marked paths", scan_snapshot["overview"]["testMarkedPaths"]),
                ("Paper paths", scan_snapshot["overview"]["paperPaths"]),
                ("Protocol paths", scan_snapshot["overview"]["protocolPaths"]),
                ("Pages-ready paths", scan_snapshot["overview"]["pagesReadyPaths"]),
                ("Evidence-rich paths", scan_snapshot["overview"]["evidenceRichPaths"]),
            ]
        ],
    }


def write_outputs(scan_snapshot: dict[str, object], dashboard: dict[str, object], write_scan_snapshot: bool) -> None:
    if write_scan_snapshot:
        SCAN_SNAPSHOT.write_text(json.dumps(scan_snapshot, indent=2), encoding="utf-8")
    DATA_JSON.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")
    DATA_JS.write_text("window.DRIVE_PULSE_DATA = " + json.dumps(dashboard, indent=2) + ";\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build DrivePulse artifacts.")
    parser.add_argument(
        "--live-scan",
        action="store_true",
        help="Scan the live indexed C-drive paths and refresh data-source/folder-scan.snapshot.json.",
    )
    args = parser.parse_args()

    portfolio = load_portfolio()
    if args.live_scan or not SCAN_SNAPSHOT.exists():
        scan_snapshot = build_live_scan(portfolio)
        write_scan = True
    else:
        scan_snapshot = json.loads(SCAN_SNAPSHOT.read_text(encoding="utf-8"))
        write_scan = False

    dashboard = build_dashboard(scan_snapshot, portfolio)
    write_outputs(scan_snapshot, dashboard, write_scan)
    metrics = dashboard["metrics"]
    print(
        "Built DrivePulse "
        f"({metrics['specificPaths']} specific paths, "
        f"{metrics['gitRepos']} git repos, "
        f"{metrics['pagesReadyPaths']} pages-ready paths)."
    )


if __name__ == "__main__":
    main()
