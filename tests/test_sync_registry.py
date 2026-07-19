import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "sync_registry.py"
HASH = "sha256:" + ("a" * 64)
REGISTRY = f"""\
skills:
  - name: existing
    path: https://github.com/amdmax/claude_marketplace/blob/main/skills/existing/SKILL.md
    hash: {HASH}
    description: Existing skill
commands: []
agents: []
"""


class SyncRegistryTest(unittest.TestCase):
    def run_sync(self, manifest):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "manifest.json"
            registry_path = root / "registry.yaml"
            manifest_path.write_text(json.dumps(manifest))
            registry_path.write_text(REGISTRY)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--marketplace-raw",
                    "https://raw.githubusercontent.com/amdmax/claude_marketplace/main",
                    "--registry",
                    str(registry_path),
                ],
                capture_output=True,
                check=False,
                text=True,
            )
            return result, registry_path.read_text()

    def test_no_changes_has_dedicated_exit_code(self):
        manifest = {
            "artifacts": {
                "existing": {
                    "type": "skill",
                    "hash": HASH,
                    "path": "skills/existing/SKILL.md",
                }
            }
        }

        result, registry = self.run_sync(manifest)

        self.assertEqual(2, result.returncode)
        self.assertIn("No changes detected", result.stdout)
        self.assertEqual(REGISTRY, registry)

    def test_invalid_manifest_remains_a_failure(self):
        manifest = {
            "artifacts": {
                "broken": {
                    "hash": HASH,
                    "path": "skills/broken/SKILL.md",
                }
            }
        }

        result, _registry = self.run_sync(manifest)

        self.assertEqual(1, result.returncode)
        self.assertIn("KeyError", result.stderr)

    def test_changed_registry_exits_successfully(self):
        changed_hash = "sha256:" + ("b" * 64)
        manifest = {
            "artifacts": {
                "existing": {
                    "type": "skill",
                    "hash": changed_hash,
                    "path": "skills/existing/SKILL.md",
                }
            }
        }

        result, registry = self.run_sync(manifest)

        self.assertEqual(0, result.returncode)
        self.assertIn("Registry updated", result.stdout)
        self.assertIn(changed_hash, registry)


if __name__ == "__main__":
    unittest.main()
