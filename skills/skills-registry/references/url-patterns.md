# URL Conversion Patterns

When the registry YAML stores a `path` URL, it is a standard GitHub web URL
(the "blob" viewer). To download raw file content you must convert it to a
raw.githubusercontent.com URL.

## Rule

```
https://github.com/<owner>/<repo>/blob/<branch>/<file-path>
→
https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<file-path>
```

Two changes only:
1. Replace the hostname: `github.com` → `raw.githubusercontent.com`
2. Remove the `/blob/` path segment (so `/blob/main/` becomes `/main/`)

Everything else — owner, repo, branch, file path — stays identical.

## Worked examples

### Example 1 — skill (nested path)
```
Input:
  https://github.com/amdmax/claude_marketplace/blob/main/skills/bug-fix/SKILL.md

Output:
  https://raw.githubusercontent.com/amdmax/claude_marketplace/main/skills/bug-fix/SKILL.md
```

### Example 2 — command (flat .md file)
```
Input:
  https://github.com/amdmax/claude_marketplace/blob/main/commands/architect.md

Output:
  https://raw.githubusercontent.com/amdmax/claude_marketplace/main/commands/architect.md
```

### Example 3 — agent (flat .md file)
```
Input:
  https://github.com/amdmax/claude_marketplace/blob/main/agents/pm.md

Output:
  https://raw.githubusercontent.com/amdmax/claude_marketplace/main/agents/pm.md
```

### Example 4 — the registry YAML itself
```
Input:
  https://github.com/amdmax/agentic_skills_registry/blob/main/claude_marketplace_skills.yaml

Output:
  https://raw.githubusercontent.com/amdmax/agentic_skills_registry/main/claude_marketplace_skills.yaml
```

## Common mistakes to avoid

| Mistake | Correct |
|---------|---------|
| Leaving `/blob/` in the path | Remove it entirely |
| Changing the branch name | Keep it as-is (usually `main`) |
| Double-slashes after removing `/blob` | There should be none — `…/main/skills/…` is correct |
| Using `githubusercontent.com` without `raw.` prefix | Must be `raw.githubusercontent.com` |
