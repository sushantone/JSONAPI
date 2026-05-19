"""
Organize files by regex name patterns: detect, test (dry-run), then move.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

pre_defined_patterns: list[dict[str, str]] = [
    {
        "pattern": r"(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})",
        "target": "<year>/<month>/<day>",
    },
]

DEFAULT_MANIFEST = "organize_manifest.json"
STATUS_LISTED = "listed"
STATUS_MATCHED = "matched"
STATUS_MOVE = "move"
STATUS_OVERWRITE = "overwrite"
STATUS_NO_OVERWRITE = "no-overwrite"
STATUS_SKIPPED = "skipped"


def _normalize_exts(file_exts: list[str]) -> set[str]:
    exts: set[str] = set()
    for ext in file_exts:
        ext = ext.strip().lower()
        if not ext:
            continue
        if not ext.startswith("."):
            ext = f".{ext}"
        exts.add(ext)
    return exts


def _file_created_iso(path: str) -> str:
    ts = os.path.getctime(path)
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _manifest_path(dest_folder: str, manifest_name: str = DEFAULT_MANIFEST) -> str:
    return os.path.join(dest_folder, manifest_name)


def _load_manifest(json_path: str) -> list[dict[str, Any]]:
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


def _save_manifest(json_path: str, entries: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(json_path)) or ".", exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


def _apply_target_template(target: str, groups: dict[str, str]) -> str:
    result = target
    for key, value in groups.items():
        result = result.replace(f"<{key}>", value)
    return result.replace("\\", "/").strip("/")


def _match_file_name(
    file_name: str, patterns: list[dict[str, str]]
) -> tuple[dict[str, str] | None, str | None]:
    """Return (pattern_entry, regex_match) for first matching pattern."""
    stem = Path(file_name).stem
    for entry in patterns:
        pattern = entry.get("pattern", "")
        if not pattern:
            continue
        compiled = re.compile(pattern)
        for candidate in (file_name, stem):
            m = compiled.search(candidate)
            if m:
                return entry, m
    return None, None


def _build_dest_path(
    dest_folder: str, file_name: str, target: str, match: re.Match[str]
) -> str:
    rel = _apply_target_template(target, match.groupdict())
    return os.path.normpath(os.path.join(dest_folder, rel, file_name))


def _list_files(src_folder: str, file_exts: list[str]) -> list[str]:
    exts = _normalize_exts(file_exts)
    paths: list[str] = []
    for root, _dirs, files in os.walk(src_folder):
        for name in files:
            if exts and Path(name).suffix.lower() not in exts:
                continue
            paths.append(os.path.normpath(os.path.join(root, name)))
    return sorted(paths)


def _new_entry(src_path: str) -> dict[str, Any]:
    return {
        "src_path": src_path,
        "src_size": os.path.getsize(src_path),
        "date_created": _file_created_iso(src_path),
        "dest_path": "",
        "status": STATUS_LISTED,
        "file_name": os.path.basename(src_path),
        "name_pattern": "",
    }


def detect__organize(
    src_folder: str,
    dest_folder: str,
    file_exts: list[str],
    name_patterns: list[dict[str, str]] | None = None,
    *,
    manifest_name: str = DEFAULT_MANIFEST,
) -> str:
    """
    List files by extension, write manifest JSON, then match names to regex patterns.

    Returns path to the manifest JSON file.
    """
    src_folder = os.path.normpath(src_folder)
    dest_folder = os.path.normpath(dest_folder)
    os.makedirs(dest_folder, exist_ok=True)

    json_path = _manifest_path(dest_folder, manifest_name)
    patterns = list(pre_defined_patterns)
    if name_patterns:
        patterns.extend(name_patterns)

    # Step 1 & 2: list files and build manifest
    entries = [_new_entry(p) for p in _list_files(src_folder, file_exts)]
    _save_manifest(json_path, entries)

    # Step 3: pattern match and update manifest
    for entry in entries:
        pattern_entry, match = _match_file_name(entry["file_name"], patterns)
        if not pattern_entry or not match:
            continue
        entry["dest_path"] = _build_dest_path(
            dest_folder,
            entry["file_name"],
            pattern_entry["target"],
            match,
        )
        entry["name_pattern"] = pattern_entry.get("pattern", "")
        entry["status"] = STATUS_MATCHED

    _save_manifest(json_path, entries)
    return json_path


def _should_overwrite(
    src_path: str,
    dest_path: str,
    overwrite_rules: list[dict[str, bool]],
) -> bool:
    """True if any rule dict allows overwriting an existing dest file."""
    if not os.path.isfile(dest_path):
        return True

    src_stat = os.stat(src_path)
    dest_stat = os.stat(dest_path)

    for rules in overwrite_rules:
        newer_file = rules.get("newer_file", False)
        same_size = rules.get("same_size", False)

        if newer_file and src_stat.st_mtime > dest_stat.st_mtime:
            return True
        if same_size and src_stat.st_size == dest_stat.st_size:
            return True
    return False


def test_organize(
    json_path: str,
    overwrite_rules: list[dict[str, bool]] | None = None,
) -> str:
    """
    Dry-run: set status to move, overwrite, or no-overwrite for matched items.

    Updates the manifest after each entry. Returns json_path.
    """
    if overwrite_rules is None:
        overwrite_rules = [{"newer_file": True, "same_size": True}]

    entries = _load_manifest(json_path)
    claimed_dest_paths: set[str] = set()

    for entry in entries:
        if entry.get("status") not in (STATUS_MATCHED, STATUS_LISTED):
            continue

        dest_path = entry.get("dest_path", "")
        if not dest_path:
            continue

        dest_path = os.path.normpath(dest_path)
        entry["dest_path"] = dest_path

        # Duplicate dest_path within this manifest (earlier items win)
        if dest_path in claimed_dest_paths:
            entry["status"] = STATUS_NO_OVERWRITE
            _save_manifest(json_path, entries)
            continue

        dest_exists = os.path.isfile(dest_path)

        if not dest_exists:
            entry["status"] = STATUS_MOVE
            claimed_dest_paths.add(dest_path)
        elif _should_overwrite(entry["src_path"], dest_path, overwrite_rules):
            entry["status"] = STATUS_OVERWRITE
            claimed_dest_paths.add(dest_path)
        else:
            entry["status"] = STATUS_NO_OVERWRITE

        _save_manifest(json_path, entries)

    return json_path


def run_organize(json_path: str) -> list[dict[str, Any]]:
    """
    Move files whose status is move or overwrite from src_path to dest_path.

    Returns list of per-file results.
    """
    entries = _load_manifest(json_path)
    results: list[dict[str, Any]] = []

    for entry in entries:
        status = entry.get("status", "")
        if status not in (STATUS_MOVE, STATUS_OVERWRITE):
            continue

        src_path = entry.get("src_path", "")
        dest_path = entry.get("dest_path", "")
        if not src_path or not dest_path:
            results.append(
                {"src_path": src_path, "dest_path": dest_path, "ok": False, "error": "missing path"}
            )
            continue

        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            if status == STATUS_OVERWRITE and os.path.isfile(dest_path):
                os.remove(dest_path)
            shutil.move(src_path, dest_path)
            entry["status"] = "moved"
            results.append({"src_path": src_path, "dest_path": dest_path, "ok": True})
        except OSError as exc:
            entry["status"] = "error"
            results.append(
                {
                    "src_path": src_path,
                    "dest_path": dest_path,
                    "ok": False,
                    "error": str(exc),
                }
            )

    _save_manifest(json_path, entries)
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Detect, test, and run file organization.")
    parser.add_argument("src_folder")
    parser.add_argument("dest_folder")
    parser.add_argument("--ext", nargs="+", default=[".jpg", ".jpeg", ".png", ".mp4"])
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--test-only", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()

    manifest = detect__organize(
        args.src_folder,
        args.dest_folder,
        args.ext,
        name_patterns=[],
        manifest_name=args.manifest,
    )
    print(f"Manifest written: {manifest}")

    test_organize(manifest)
    print("Dry-run (test_organize) complete.")

    if args.run and not args.test_only:
        outcomes = run_organize(manifest)
        moved = sum(1 for o in outcomes if o.get("ok"))
        print(f"Moved {moved} file(s).")
