#!/usr/bin/env python3
"""
sync_registry.py — Sync claude_marketplace_skills.yaml with the published-artifacts-manifest.json.

Usage:
    python scripts/sync_registry.py \
        --manifest manifest.json \
        --marketplace-raw https://raw.githubusercontent.com/amdmax/claude_marketplace/main \
        --registry claude_marketplace_skills.yaml

Exit codes:
    0 — changes were made to the registry
    1 — no changes detected (registry already up to date)
"""

import argparse
import json
import re
import sys
import urllib.request
import yaml
from io import StringIO
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.error import CommentMark
from ruamel.yaml.tokens import CommentToken


GITHUB_BLOB_BASE = "https://github.com/amdmax/claude_marketplace/blob/main"
CLAUDE_MARKETPLACE_DOMAIN = "github.com/amdmax/claude_marketplace"


def fetch_url(url: str) -> str:
    with urllib.request.urlopen(url) as resp:
        return resp.read().decode("utf-8")


def parse_frontmatter_description(content: str) -> str:
    """Extract description from YAML frontmatter between first two --- delimiters."""
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return ""
    frontmatter = "\n".join(lines[1:end])
    try:
        data = yaml.safe_load(frontmatter)
        return data.get("description", "") if isinstance(data, dict) else ""
    except yaml.YAMLError:
        return ""


def manifest_name_to_registry_name(artifact_name: str, artifact_type: str) -> str:
    """Convert manifest artifact key to registry entry name."""
    if artifact_type == "skill":
        return artifact_name  # e.g. "debug", "arch:create-adr"
    elif artifact_type == "command":
        # "commands/agile-dev-team.md" -> "agile-dev-team"
        return Path(artifact_name).stem
    elif artifact_type == "agent":
        # "agents/architect.md" -> "architect"
        return Path(artifact_name).stem
    return artifact_name


def section_for_type(artifact_type: str) -> str:
    return {"skill": "skills", "command": "commands", "agent": "agents"}.get(artifact_type, "skills")


def find_entry(section_list, name: str):
    """Find an entry by name in a ruamel.yaml CommentedSeq, return (index, entry) or (None, None)."""
    for i, entry in enumerate(section_list):
        if entry.get("name") == name:
            return i, entry
    return None, None


def main():
    parser = argparse.ArgumentParser(description="Sync registry YAML from marketplace manifest")
    parser.add_argument("--manifest", required=True, help="Path to published-artifacts-manifest.json")
    parser.add_argument("--marketplace-raw", required=True, help="Base raw URL for marketplace content")
    parser.add_argument("--registry", required=True, help="Path to claude_marketplace_skills.yaml")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    registry_path = Path(args.registry)
    marketplace_raw = args.marketplace_raw.rstrip("/")

    manifest = json.loads(manifest_path.read_text())
    artifacts = manifest.get("artifacts", {})

    ryaml = YAML()
    ryaml.preserve_quotes = True
    ryaml.width = 120

    raw_text = registry_path.read_text()
    already_warned_names = set(re.findall(r"# WARNING: '([^']+)' not found", raw_text))

    registry = ryaml.load(StringIO(raw_text))

    # Ensure all sections exist
    for section in ("skills", "commands", "agents"):
        if section not in registry or registry[section] is None:
            registry[section] = CommentedSeq()

    changed = False

    # --- Pass 1: update existing entries, add new ones ---
    for artifact_name, artifact in artifacts.items():
        artifact_type = artifact["type"]
        artifact_hash = artifact["hash"]
        artifact_path = artifact["path"]

        registry_name = manifest_name_to_registry_name(artifact_name, artifact_type)
        section_key = section_for_type(artifact_type)
        section_list = registry[section_key]

        github_url = f"{GITHUB_BLOB_BASE}/{artifact_path}"

        idx, entry = find_entry(section_list, registry_name)

        if entry is not None:
            # Update existing entry
            if entry.get("hash") != artifact_hash or entry.get("path") != github_url:
                entry["hash"] = artifact_hash
                entry["path"] = github_url
                changed = True
        else:
            # New entry — use description from manifest (embedded by hash_published_artifacts.py)
            description = artifact.get("description", "") or f"Imported from marketplace: {registry_name}"

            new_entry = CommentedMap()
            new_entry["name"] = registry_name
            new_entry["path"] = github_url
            new_entry["hash"] = artifact_hash
            new_entry["description"] = description

            section_list.append(new_entry)
            print(f"  + Added new entry: {registry_name} ({section_key})")
            changed = True

    # --- Pass 2: flag registry entries not in manifest ---
    manifest_registry_names = {
        manifest_name_to_registry_name(k, v["type"])
        for k, v in artifacts.items()
    }

    for section_key in ("skills", "commands", "agents"):
        section_list = registry[section_key]
        if not section_list:
            continue
        for i, entry in enumerate(section_list):
            name = entry.get("name", "")
            # Skip entries not from claude_marketplace (e.g. skills-registry from agentic_skills_registry)
            path = entry.get("path", "")
            if CLAUDE_MARKETPLACE_DOMAIN not in path:
                continue
            if name not in manifest_registry_names and name not in already_warned_names:
                comment_text = f"# WARNING: '{name}' not found in marketplace manifest — possible rename or removal\n"
                ct = CommentToken(comment_text, CommentMark(0), None)
                if i not in section_list.ca.items:
                    section_list.ca.items[i] = [None, [ct], None, None]
                else:
                    existing = section_list.ca.items[i][1]
                    if existing is None:
                        section_list.ca.items[i][1] = [ct]
                    else:
                        existing.insert(0, ct)
                print(f"  ! Flagged missing entry: {name} ({section_key})")
                changed = True

    if not changed:
        print("No changes detected — registry is up to date.")
        sys.exit(1)

    ryaml.dump(registry, registry_path)
    print(f"Registry updated: {registry_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
