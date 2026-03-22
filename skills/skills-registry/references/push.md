---
name: skills-registry:push
description: Reference for the push sub-command. Covers how publishing to claude_marketplace works, the automatic registry PR from CI, correct target paths, and step-by-step workflow.
---

# push

## Purpose

Publish a locally-authored or locally-modified skill, command, or agent to `amdmax/claude_marketplace` via a pull request. The registry hash update in `amdmax/agentic_skills_registry` is created automatically by CI — you only ever open one PR.

---

## Workflow

1. Locate the local file — check in order:
   - `.claude/skills/<name>/SKILL.md`
   - `.claude/commands/<name>.md`
   - `.claude/agents/<name>.md`

2. Write the file(s) into the local `../claude_marketplace` clone under the correct target path:

   | Type | Target path in marketplace |
   |------|---------------------------|
   | skill | `skills/<name>/SKILL.md` (copy full directory if sub-commands exist) |
   | command | `commands/<name>.md` |
   | agent | `agents/<name>.md` |

3. Create a branch, commit, push, and open **one PR** into `amdmax/claude_marketplace`:

   ```bash
   cd ../claude_marketplace
   git checkout main && git pull
   git checkout -b <branch-name>

   # copy files from project
   cp -r <project>/.claude/skills/<name>/ skills/<name>/
   # or: cp <project>/.claude/commands/<name>.md commands/<name>.md

   git add skills/<name>/
   git commit -m "feat: add/update <name>"
   git push -u origin <branch-name>

   gh pr create --repo amdmax/claude_marketplace \
     --title "feat: add/update <name>" \
     --body "..."
   ```

4. CI in `claude_marketplace` detects the changed files, computes the new hash, and automatically opens a corresponding PR into `amdmax/agentic_skills_registry`. No manual action needed.

---

## Validation criteria

- The PR branch is based on a current `main` — no stale base
- All files for the skill are included (SKILL.md + any sub-command `.md` files + `references/`)
- Each file has valid YAML frontmatter (`name`, `description` at minimum)
- Only one PR is opened — targeting `amdmax/claude_marketplace`, not the registry
- CI passes on the marketplace PR before merging

---

## Exceptions

| Situation | Resolution |
|-----------|-----------|
| `../claude_marketplace` does not exist | `git clone https://github.com/amdmax/claude_marketplace ../claude_marketplace` |
| You are an external contributor (not `amdmax`) | Fork the marketplace repo first: `gh repo fork amdmax/claude_marketplace --clone` |
| CI does not open a registry PR automatically | Open a registry PR manually, updating the `hash:` field for the entry in `claude_marketplace_skills.yaml` |

---

## What not to do

- Do not open a PR against `amdmax/agentic_skills_registry` — CI handles this
- Do not use `gh api PUT` to push file content byte-by-byte — use the local clone
- Do not push directly to `main` in the marketplace repo — always use a branch and PR
