---
name: skills-registry
description: >-
  Manage Claude Code skills, commands, and agents from the amdmax marketplace registry
  (github.com/amdmax/agentic_skills_registry). Use to install, update, discover, or
  publish skills/commands/agents. Triggered by: /skills-registry pull <name>,
  /skills-registry learn <description>, /skills-registry update <name>,
  /skills-registry push <name>, /skills-registry list. Also triggers on phrases like
  "install skill", "pull skill from registry", "update installed skill",
  "push skill to marketplace", "find a skill for X", "what skills are available".
argument-hint: "pull <name> | learn <description> | update <name> | push <name> | list [--type skill|command|agent]"
---

# Skills Registry

A package manager for Claude Code skills, commands, and agents sourced from the
amdmax marketplace registry.

## Configuration

```
Registry raw URL : https://raw.githubusercontent.com/amdmax/agentic_skills_registry/main/claude_marketplace_skills.yaml
Marketplace repo : amdmax/claude_marketplace
Registry repo    : amdmax/agentic_skills_registry
Lockfile         : .claude/.skills-registry.lock   (project-level, YAML)

Install roots
  skill   → .claude/skills/<name>/SKILL.md
  command → .claude/commands/<name>.md
  agent   → .claude/agents/<name>.md

URL conversion
  github.com/<o>/<r>/blob/<b>/<path>
  → raw.githubusercontent.com/<o>/<r>/<b>/<path>
  (drop the /blob/ segment only — everything else stays the same)
  See references/url-patterns.md for worked examples.

Hash commands
  macOS : shasum -a 256 <file> | awk '{print "sha256:"$1}'
  Linux : sha256sum <file>    | awk '{print "sha256:"$1}'
  For content in a variable:
  macOS : printf '%s' "$CONTENT" | shasum -a 256 | awk '{print "sha256:"$1}'
```

---

## Subcommand dispatch

Parse `$ARGUMENTS`. The first word determines which action to run. Jump directly
to the relevant section below.

| First word  | Action                              |
|-------------|-------------------------------------|
| `pull`      | Install a named entry               |
| `learn`     | Semantic discovery + install        |
| `update`    | Check for updates and apply         |
| `push`      | Publish local file to marketplace   |
| `list`      | Show registry contents              |
| *(nothing)* | Print usage summary                 |

---

## Action: pull

**Usage:** `pull <name> [--type skill|command|agent]`

The goal is to fetch a skill/command/agent from the marketplace and install it
into the current project's `.claude/` directory, recording the install in the
lockfile for future update checks.

1. **Fetch registry.** Use WebFetch with the raw registry URL from Configuration.

2. **Find the entry.** Search across all three sections (`skills`, `commands`,
   `agents`) for an entry whose `name` matches exactly (case-insensitive).
   If `--type` is present, restrict search to that section only.
   If no match: list the 5 names with the highest character-overlap to the
   requested name and stop — do not install anything.

3. **Convert URL.** Apply the URL conversion rule to the entry's `path` field
   to get the raw download URL. Also derive the `gh api` path from the entry's
   `path` field: extract `<owner>/<repo>` and `<file-path>` components.
   Consult `references/url-patterns.md` if unsure.

4. **Fetch content.** The marketplace repo may be private, so prefer `gh api`:
   ```bash
   # Extract owner/repo and file path from the GitHub path URL
   # e.g. path: https://github.com/amdmax/claude_marketplace/blob/main/skills/bug-fix/SKILL.md
   # → owner_repo=amdmax/claude_marketplace, file_path=skills/bug-fix/SKILL.md
   gh api repos/<owner_repo>/contents/<file_path> --jq '.content' | base64 --decode
   ```
   If `gh` is not installed or the command fails, fall back to WebFetch on the
   raw URL. If both fail, report the error and stop.

5. **Verify hash (if registry has one).** If the matched entry contains a `hash:`
   field in the YAML, compute the SHA256 of the downloaded content using the
   appropriate Bash command from Configuration. Compare with the registry hash.
   - Match → proceed normally.
   - Mismatch → print the block below and use AskUserQuestion to ask "Proceed
     anyway? (yes/no)" before continuing. If the user says no, stop.

   ```
   ⚠️  HASH MISMATCH — possible tampering detected
   Registry hash : <registry-hash>
   Computed hash : <computed-hash>
   Source URL    : <url>
   ```

6. **Check for existing install.** Check whether the target file already exists.
   If it does, use AskUserQuestion to ask "File already exists at <path>.
   Overwrite? (yes/no)". Stop if the user says no.

7. **Install.** Create the parent directory with `mkdir -p` if needed. Write the
   file content to the install path.

8. **Update lockfile.** Compute the SHA256 of the written file. Read
   `.claude/.skills-registry.lock` if it exists; create it otherwise. Upsert an
   entry under `entries.<name>` with the fields shown in
   `references/lockfile-schema.md`. Write the file back.

9. **Confirm.** Print:
   ```
   ✓ Installed <type> "<name>"
     path : <install-path>
     hash : <sha256>
   ```

---

## Action: learn

**Usage:** `learn <natural-language-description>`

The goal is to help the user discover entries they don't know the exact name of,
by matching their description against the registry semantically.

1. **Fetch registry.** Use WebFetch with the raw registry URL.

2. **Build flat list.** Collect every entry from all three sections into a single
   list of `{name, type, description}` objects.

3. **Semantic scoring.** Using your own reasoning (no external calls), score each
   entry against the user's description. Consider: domain overlap, task
   similarity, shared keywords, inferred intent. Pick the top 3.

4. **Present matches.** Show a table:

   | # | Name | Type | Why it matches |
   |---|------|------|----------------|
   | 1 | ... | ... | ... |
   | 2 | ... | ... | ... |
   | 3 | ... | ... | ... |

5. **Ask for selection.** Use AskUserQuestion: "Which would you like to install?
   Enter 1, 2, 3, or 'none' to cancel."

6. **Install.** On a valid selection, run the full `pull` flow for the chosen
   entry's name (starting from step 1 of the pull action).

---

## Action: update

**Usage:** `update <name>`

The goal is to compare the currently-installed version of an entry against
what the marketplace serves now, and apply an update if one is available.

1. **Read lockfile.** Read `.claude/.skills-registry.lock`.
   If the file doesn't exist or the entry `<name>` is absent under `entries`,
   stop with: "No lockfile entry for '<name>'. Run `pull <name>` first."

2. **Extract stored state.** Pull `source_url` and `hash` from the lockfile entry.

3. **Fetch fresh content.** The `source_url` in the lockfile is a
   raw.githubusercontent.com URL. Derive the `gh api` path from it:
   strip `https://raw.githubusercontent.com/` and insert `repos/` +
   `/contents/` between the repo and branch components.
   ```bash
   # source_url: https://raw.githubusercontent.com/amdmax/claude_marketplace/main/skills/bug-fix/SKILL.md
   # → gh api repos/amdmax/claude_marketplace/contents/skills/bug-fix/SKILL.md?ref=main
   gh api "repos/<owner>/<repo>/contents/<path>?ref=<branch>" --jq '.content' | base64 --decode
   ```
   Fall back to WebFetch on the `source_url` if `gh api` is unavailable.

4. **Compute hash.** Use the Bash hash command from Configuration on the fetched
   content.

5. **Compare.**
   - Hashes match → print "✓ <name> is already up to date (hash: <hash>)" and stop.
   - Hashes differ → continue.

6. **Show diff summary.** Read the currently-installed local file. Report:
   - Line count before vs after
   - First section heading that changed (if detectable)
   - A one-line summary: "Remote version has N more/fewer lines."

7. **Confirm.** Use AskUserQuestion: "Update <name> from <old-hash-short> to
   <new-hash-short>? (yes/no)"

8. **Apply update.** On "yes": overwrite the local file with the fetched content.
   Update the lockfile entry: set `hash` to the new hash, add `updated_at` with
   the current ISO 8601 timestamp. Print "✓ Updated <name>".

---

## Action: push

**Usage:** `push <name>`

The goal is to publish a locally-authored or locally-modified skill/command/agent
back to the marketplace via a pull request, and to update the registry YAML with
the new content hash.

1. **Locate local file.** Check in order:
   - `.claude/skills/<name>/SKILL.md`
   - `.claude/commands/<name>.md`
   - `.claude/agents/<name>.md`
   Use the first path that exists. If none found, stop with an error listing
   the paths that were checked.

2. **Read and hash.** Read the file content. Compute SHA256 via Bash.

3. **Confirm intent.** Use AskUserQuestion before running any `gh` commands.
   Show the user exactly what will happen:

   ```
   This will open 2 pull requests:
   1. amdmax/claude_marketplace  — update <type>/<target-path>
   2. amdmax/agentic_skills_registry — update hash for "<name>" in YAML

   Proceed? (yes/no)
   ```

   Stop if the user says no.

4. **Check gh CLI.** Run `gh --version`. If the command fails, print:

   ```
   gh CLI not found. To push manually:
   1. Fork https://github.com/amdmax/claude_marketplace
   2. Copy your local file to <target-path> in the fork
   3. Open a PR: gh pr create --repo amdmax/claude_marketplace \
        --title "Update <name>" --body "Updated via skills-registry"
   4. Repeat for amdmax/agentic_skills_registry to update the hash field.
   ```
   Then stop.

5. **PR to marketplace.** Execute these steps via Bash:

   ```bash
   # Fork the repo (idempotent)
   gh repo fork amdmax/claude_marketplace --clone=false

   # Get the authenticated user's login
   GH_USER=$(gh api user --jq .login)
   BRANCH="update-${name}"
   TARGET_PATH="<type-prefix>/<name>[/SKILL.md if skill]"

   # Get current file SHA (needed for PUT if file exists)
   FILE_SHA=$(gh api "repos/${GH_USER}/claude_marketplace/contents/${TARGET_PATH}" \
     --jq .sha 2>/dev/null || echo "")

   # Base64-encode the file content
   CONTENT_B64=$(base64 < <local-file-path>)

   # Create or update the file on a branch in the fork
   gh api "repos/${GH_USER}/claude_marketplace/contents/${TARGET_PATH}" \
     -X PUT \
     -f message="Update ${name}" \
     -f content="${CONTENT_B64}" \
     -f branch="${BRANCH}" \
     ${FILE_SHA:+-f sha="${FILE_SHA}"}

   # Open the PR against upstream
   gh pr create \
     --repo amdmax/claude_marketplace \
     --head "${GH_USER}:${BRANCH}" \
     --title "Update ${name} (${type})" \
     --body "Updated via skills-registry push"
   ```

6. **PR to registry.** Fetch the current registry YAML. Find the entry for
   `<name>`. If its `hash` field equals the computed hash, skip this PR.
   Otherwise:
   - Update the `hash:` field in the YAML for this entry.
   - Write a temp file, commit to a branch in a fork of `amdmax/agentic_skills_registry`.
   - Open a PR: `gh pr create --repo amdmax/agentic_skills_registry ...`

7. **Report.** Print both PR URLs.

---

## Action: list

**Usage:** `list [--type skill|command|agent]`

Fetch the registry YAML and display its contents as a readable table.

1. Use WebFetch to get the raw registry YAML.
2. If `--type` is provided, display only that section. Otherwise display all three.
3. Format as a markdown table with columns: **Type**, **Name**, **Description**
   (truncated to 80 characters with `…` if longer).
4. Print a summary line at the bottom:
   `Total: X skills, Y commands, Z agents`

---

## No subcommand (usage)

When `$ARGUMENTS` is empty or the first word is unrecognised, print:

```
skills-registry — package manager for Claude Code marketplace

Usage:
  pull   <name> [--type skill|command|agent]  Install an entry from the registry
  learn  <description>                         Discover entries by natural language
  update <name>                                Check for and apply updates
  push   <name>                                Publish a local file to the marketplace
  list   [--type skill|command|agent]          List available registry entries

Examples:
  /skills-registry pull bug-fix
  /skills-registry learn "something that helps write GitHub Actions"
  /skills-registry update bug-fix
  /skills-registry push my-custom-skill
  /skills-registry list --type command
```

---

## Error handling

| Condition                          | Response                                          |
|------------------------------------|---------------------------------------------------|
| Registry YAML unreachable          | Warn + print raw URL for manual check             |
| Entry not found by name            | List 5 closest names by character overlap         |
| Hash mismatch on pull              | Print WARNING block + AskUserQuestion to confirm  |
| File already installed             | AskUserQuestion whether to overwrite              |
| `gh` CLI missing on push           | Print manual PR instructions and stop             |
| Lockfile entry missing on update   | "Run `pull <name>` first"                         |
| Local file missing on push         | List the three paths that were checked            |

---

## Reference files

- **references/lockfile-schema.md** — full lockfile YAML spec and field descriptions.
  Read this before writing or updating the lockfile.
- **references/url-patterns.md** — URL conversion rule with worked examples.
  Read this when converting a `path` field to a raw download URL.
