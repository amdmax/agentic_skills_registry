# Lockfile Schema

The lockfile lives at `.claude/.skills-registry.lock` within the current project.
It is YAML, indented with 2 spaces. Never use tabs.

## Full example

```yaml
registry_url: https://raw.githubusercontent.com/amdmax/agentic_skills_registry/main/claude_marketplace_skills.yaml
entries:
  bug-fix:
    type: skill
    hash: sha256:3b4c2a1d9f8e7b6a5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1
    installed_at: 2026-03-18T10:00:00Z
    source_url: https://raw.githubusercontent.com/amdmax/claude_marketplace/main/skills/bug-fix/SKILL.md
  architect:
    type: agent
    hash: sha256:9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7
    installed_at: 2026-03-18T11:30:00Z
    updated_at: 2026-03-18T14:00:00Z
    source_url: https://raw.githubusercontent.com/amdmax/claude_marketplace/main/agents/architect.md
  write-typescript:
    type: command
    hash: sha256:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3
    installed_at: 2026-03-18T09:15:00Z
    source_url: https://raw.githubusercontent.com/amdmax/claude_marketplace/main/commands/write-typescript.md
```

## Field reference

| Field          | Required | Description |
|----------------|----------|-------------|
| `registry_url` | Yes      | Raw URL of the registry YAML that was used when the entry was installed. Top-level field, not under `entries`. |
| `entries`      | Yes      | Map keyed by entry name (string). |
| `type`         | Yes      | One of: `skill`, `command`, `agent`. Determines install path. |
| `hash`         | Yes      | SHA256 of the file content at install time, prefixed with `sha256:`. |
| `installed_at` | Yes      | ISO 8601 UTC timestamp of first install (e.g. `2026-03-18T10:00:00Z`). |
| `updated_at`   | No       | ISO 8601 UTC timestamp of most recent `update` run. Omit on first install; add/overwrite on each successful update. |
| `source_url`   | Yes      | Raw download URL (raw.githubusercontent.com) used to fetch this entry. Stored so `update` can re-fetch without consulting the registry. |

## Notes

- Keys under `entries` are the entry **name** exactly as it appears in the registry
  YAML (e.g. `bug-fix`, `arch:create-adr`, `write-typescript`).
- When upserting an entry, preserve existing fields that you are not changing.
  For example, `update` should overwrite `hash` and add `updated_at` but leave
  `installed_at` and `source_url` unchanged.
- If the lockfile does not exist, create it from scratch with `registry_url` and
  an empty `entries` map, then add the new entry.
