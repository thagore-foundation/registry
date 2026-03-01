#!/usr/bin/env python3
"""Parse publish issues and upsert entries into publish.yaml."""

from __future__ import annotations

import datetime as dt
import os
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PUBLISH_PATH = ROOT / "publish.yaml"

PUBLISH_RE = re.compile(
    r"\bpublish\s+([a-z0-9][a-z0-9._-]*)@(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)\b",
    re.IGNORECASE,
)
REPO_RE = re.compile(r"\brepo\s*[:=]\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\b", re.IGNORECASE)
DESC_RE = re.compile(r"\bdesc(?:ription)?\s*[:=]\s*(.+)", re.IGNORECASE)
CHECKSUM_RE = re.compile(r"\bchecksum\s*[:=]\s*([A-Fa-f0-9]{64})\b", re.IGNORECASE)


def set_output(name: str, value: str) -> None:
    out = os.environ.get("GITHUB_OUTPUT")
    if not out:
        return
    with open(out, "a", encoding="utf-8") as fh:
        fh.write(f"{name}={value}\n")


def main() -> int:
    title = os.environ.get("ISSUE_TITLE", "")
    body = os.environ.get("ISSUE_BODY", "")
    issue_user = os.environ.get("ISSUE_USER", "unknown-user")
    text = f"{title}\n{body}"

    match = PUBLISH_RE.search(text)
    if not match:
        set_output("create_pr", "false")
        set_output("reason", "No `publish <pkg>@<version>` request found.")
        return 0

    pkg, version = match.group(1), match.group(2)
    repo_match = REPO_RE.search(text)
    desc_match = DESC_RE.search(text)
    checksum_match = CHECKSUM_RE.search(text)

    repo = repo_match.group(1) if repo_match else f"{issue_user}/{pkg}"
    description = desc_match.group(1).strip() if desc_match else f"{pkg} package"
    checksum = checksum_match.group(1).lower() if checksum_match else ""

    data = {}
    if PUBLISH_PATH.exists():
        loaded = yaml.safe_load(PUBLISH_PATH.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            data = loaded

    data[pkg] = {
        "repo": repo,
        "version": version,
        "description": description,
        "checksum": checksum,
        "submitted": dt.date.today().isoformat(),
        "status": "pending-review",
    }

    ordered = {k: data[k] for k in sorted(data.keys())}
    PUBLISH_PATH.write_text(yaml.safe_dump(ordered, sort_keys=False), encoding="utf-8")

    set_output("create_pr", "true")
    set_output("pkg", pkg)
    set_output("version", version)
    set_output("repo", repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
