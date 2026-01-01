# CI/CD Documentation

## Overview

This repository uses GitHub Actions for automated testing, security scanning, and publishing.

## Workflows

### CI Workflow (`.github/workflows/ci.yml`)

**Triggers:** Push to main, Pull requests

**Purpose:** Run tests, linting, type checking, and build verification

**Jobs:**
- **Lint & Format Check**
  - Ruff linting and formatting
  - Type checking with mypy
- **Test Matrix**
  - Python 3.10, 3.11, 3.12, 3.13
  - Parallel execution across versions
- **Build Package**
  - Verifies package builds successfully
  - Uploads build artifacts

**Estimated Runtime:** 3-5 minutes

---

### Publish Workflow (`.github/workflows/publish.yml`)

**Triggers:** Tags matching `v*`

**Purpose:** Automated PyPI publishing via Trusted Publishing

**Jobs:**
- **Build Distribution** - Creates wheel and source distribution
- **Publish to PyPI** - Publishes with digital attestations (PEP 740)
- **Create GitHub Release** - Auto-generates release notes

**Estimated Runtime:** 2-3 minutes

**Features:**
- ✅ PyPI Trusted Publishing (no API tokens)
- ✅ Digital attestations for supply chain security
- ✅ Automatic GitHub release creation

---

### Security Workflow (`.github/workflows/security.yml`)

**Triggers:** Push to main, Pull requests, Weekly schedule (Sundays)

**Purpose:** Dependency scanning, SBOM generation, code analysis

**Jobs:**
- **Dependency Review** - Blocks PRs with high-severity vulnerabilities
- **SBOM Generation** - CycloneDX format for compliance
- **CodeQL Analysis** - Code-level security scanning

**Estimated Runtime:** 5-10 minutes

**Features:**
- ✅ Dependency vulnerability blocking
- ✅ Software Bill of Materials (SBOM)
- ✅ CodeQL for detecting security issues
- ✅ Weekly automated scans

---

## Badges

Add these to your README:

```markdown
![CI](https://github.com/Compass-Rose-Systems/openproject-mcp-server/workflows/CI/badge.svg)
![Security](https://github.com/Compass-Rose-Systems/openproject-mcp-server/workflows/Security/badge.svg)
![PyPI](https://img.shields.io/pypi/v/openproject-mcp)
![Python](https://img.shields.io/pypi/pyversions/openproject-mcp)
```

## Technologies

| Tool | Purpose |
|------|---------|
| **uv** | Fast Python package manager |
| **Ruff** | Modern linting and formatting |
| **mypy** | Static type checking |
| **pytest** | Testing framework |
| **CodeQL** | Security code scanning |
| **PyPI Trusted Publishing** | Secure publishing (OIDC) |

## Workflow Status

Check workflow runs: https://github.com/Compass-Rose-Systems/openproject-mcp-server/actions

## Local Testing

### Run CI checks locally:

```bash
# Install dev dependencies
uv sync --dev

# Run linting
uv run ruff check .
uv run ruff format --check .

# Run type checking
uv run mypy openproject_mcp.py

# Run tests
uv run pytest tests/

# Build package
uv build
```

### Test with act:

```bash
# Install act (GitHub Actions local runner)
brew install act  # macOS
# or: https://github.com/nektos/act

# Run CI workflow locally
act push -W .github/workflows/ci.yml
```

## Configuration Files

- `.github/workflows/ci.yml` - CI workflow
- `.github/workflows/publish.yml` - Publishing workflow
- `.github/workflows/security.yml` - Security scanning
- `.github/dependabot.yml` - Automated dependency updates
- `pyproject.toml` - Project config + tool settings
