# Release Process

This document explains how to release a new version of openproject-mcp.

## Prerequisites

- Push access to main branch
- PyPI Trusted Publisher configured for openproject-mcp
- Admin access to repository (for creating tags)

## Release Steps

### 1. Update Version

Edit `pyproject.toml`:
```toml
[project]
version = "1.0.3"  # Update this
```

### 2. Commit and Tag

```bash
git add pyproject.toml
git commit -m "Bump version to 1.0.3"
git tag v1.0.3
git push origin main --tags
```

### 3. Automated Publishing

The publish workflow automatically:
1. Builds the package
2. Publishes to PyPI with Trusted Publishing
3. Creates digital attestations (PEP 740)
4. Creates GitHub release with auto-generated notes

Monitor: https://github.com/Compass-Rose-Systems/openproject-mcp-server/actions/workflows/publish.yml

## Versioning

This project follows [Semantic Versioning](https://semver.org/).

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality
- **PATCH** version for backwards-compatible bug fixes

## PyPI Trusted Publisher

Ensure Trusted Publisher is configured at https://pypi.org/manage/account/publishing/

Configuration:
- PyPI Project Name: `openproject-mcp`
- Owner: `Compass-Rose-Systems`
- Repository: `openproject-mcp-server`
- Workflow: `publish.yml`
- Environment: `pypi`

## Troubleshooting

### Tag Not Triggering Publish

**Check:**
- Tag matches pattern `v*` (e.g., v1.0.3)
- Tag was pushed to GitHub
- Workflow file exists at `.github/workflows/publish.yml`

### Publish Fails - Trusted Publishing

**Solutions:**
1. Verify PyPI Trusted Publisher settings match exactly
2. Check environment `pypi` exists in repository settings
3. Ensure workflow has `id-token: write` permission

### Version Already Published

**Error:** Package version already exists on PyPI

**Solution:**
1. Bump version to next patch/minor/major
2. Create new tag
3. Never reuse version numbers

## First Release

For the first release after setting up Trusted Publishing:

1. Configure pending publisher on PyPI (see above)
2. Create and push tag
3. Workflow will establish the publisher relationship
4. Future releases work automatically
