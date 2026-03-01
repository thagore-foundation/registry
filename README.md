# Thagore Registry

Central package index for Drago and Thagore ecosystem packages.

## Files

- `authentic.yaml`: foundation-maintained and verified packages.
- `community.yaml`: community packages reviewed by maintainers.
- `publish.yaml`: intake queue for new package publish requests.

## Automation

- `Registry Validate` workflow
  - Runs on PR and push.
  - Validates YAML schema, required fields, semver format, and duplicate names.
- `Registry Publish Intake` workflow
  - Runs when a GitHub issue is opened/edited/reopened.
  - Parses `publish <package>@<version>`, updates `publish.yaml`, opens PR automatically.

## Publish Issue Format

```text
publish mypkg@0.1.0
repo: myorg/mypkg
description: My package
checksum: <sha256-hex>
```
