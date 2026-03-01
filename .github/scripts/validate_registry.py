#!/usr/bin/env python3
"""Validate registry YAML files for structure and required metadata."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

PKG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

FILES = {
    "authentic.yaml": {"repo", "version", "description", "checksum", "maintainer"},
    "community.yaml": {"repo", "version", "description", "checksum", "reviewed_by"},
    "publish.yaml": {"repo", "version", "description", "checksum", "submitted", "status"},
}


def fail(messages: list[str]) -> int:
    for msg in messages:
        print(f"ERROR: {msg}", file=sys.stderr)
    return 1


def load_yaml(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must be a top-level mapping")
    return data


def validate_entry(file_name: str, pkg_name: str, metadata: object, required: set[str], errors: list[str]) -> None:
    if not PKG_RE.match(pkg_name):
        errors.append(f"{file_name}: invalid package name `{pkg_name}`")
    if not isinstance(metadata, dict):
        errors.append(f"{file_name}:{pkg_name}: entry must be a mapping")
        return

    missing = sorted(required - set(metadata.keys()))
    if missing:
        errors.append(f"{file_name}:{pkg_name}: missing required keys: {', '.join(missing)}")

    repo = str(metadata.get("repo", "")).strip()
    version = str(metadata.get("version", "")).strip()
    description = str(metadata.get("description", "")).strip()
    checksum = str(metadata.get("checksum", "")).strip()

    if repo and not REPO_RE.match(repo):
        errors.append(f"{file_name}:{pkg_name}: invalid repo `{repo}` (expected org/name)")
    if version and not SEMVER_RE.match(version):
        errors.append(f"{file_name}:{pkg_name}: invalid version `{version}` (expected semver)")
    if not description:
        errors.append(f"{file_name}:{pkg_name}: description must not be empty")
    if checksum and not re.fullmatch(r"[A-Fa-f0-9]{64}", checksum):
        errors.append(f"{file_name}:{pkg_name}: checksum must be empty or sha256 hex")

    if file_name == "publish.yaml":
        status = str(metadata.get("status", "")).strip()
        if status not in {"pending-review", "approved", "rejected"}:
            errors.append(
                f"{file_name}:{pkg_name}: status must be one of pending-review|approved|rejected"
            )
        submitted = str(metadata.get("submitted", "")).strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", submitted):
            errors.append(f"{file_name}:{pkg_name}: submitted must be YYYY-MM-DD")


def main() -> int:
    errors: list[str] = []
    ownership: dict[str, str] = {}

    for file_name, required in FILES.items():
        path = ROOT / file_name
        if not path.exists():
            errors.append(f"missing file: {file_name}")
            continue
        try:
            data = load_yaml(path)
        except Exception as exc:  # pragma: no cover
            errors.append(f"{file_name}: {exc}")
            continue

        for pkg_name, metadata in data.items():
            validate_entry(file_name, str(pkg_name), metadata, required, errors)
            owner = ownership.get(str(pkg_name))
            if owner and owner != file_name:
                errors.append(f"package `{pkg_name}` appears in both {owner} and {file_name}")
            else:
                ownership[str(pkg_name)] = file_name

    if errors:
        return fail(errors)

    print("registry validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
