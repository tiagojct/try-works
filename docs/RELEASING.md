# Releasing

1. Bump `version` in try-works.json (single source).
2. `make generate` then `make test` (validate + drift check must pass).
3. Update CHANGELOG.md and CITATION.cff.
4. Commit, then tag: `git tag -a vX.Y.Z -m "X.Y.Z"` and push tags.
5. Publish surfaces as needed (PUBLISHING.md).

The version is stamped into the Obsidian, VS Code, and Tailwind manifests by the
generator, so they never drift from the json.
