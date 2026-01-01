# CI/CD Troubleshooting

## CI Workflow Issues

### Ruff Linting Fails

**Error:** Linting violations found

**Solutions:**
```bash
# Run locally to see issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Ruff Format Check Fails

**Error:** Files would be reformatted

**Solution:**
```bash
# Format code
uv run ruff format .

# Commit changes
git add .
git commit -m "Format code with Ruff"
```

### mypy Type Checking Fails

**Error:** Type check errors

**Solutions:**
```bash
# Run locally
uv run mypy openproject_mcp.py

# Option 1: Fix type errors
# Option 2: Add type ignore comments for false positives
# type: ignore[error-code]

# Option 3: Adjust mypy settings in pyproject.toml
```

### Tests Fail on Specific Python Version

**Error:** Tests pass locally but fail on CI for specific version

**Solutions:**
```bash
# Install specific Python version locally
uv python install 3.10

# Run tests with that version
uv run --python 3.10 pytest tests/

# Check for version-specific issues
```

### Build Fails

**Error:** Package build errors

**Solutions:**
```bash
# Build locally
uv build

# Check for:
# - Missing files in git
# - Invalid pyproject.toml
# - Build backend issues
```

---

## Publish Workflow Issues

### Trusted Publishing Fails

**Error:** `OIDC token retrieval failed` or `Trusted publishing exchange failure`

**Possible Causes:**
1. PyPI Trusted Publisher not configured
2. Workflow name doesn't match (`publish.yml`)
3. Environment name doesn't match (`pypi`)
4. Repository/owner mismatch

**Solution:**
```bash
# Verify PyPI configuration at:
# https://pypi.org/manage/account/publishing/

# Check configuration matches:
PyPI Project Name: openproject-mcp
Owner: Compass-Rose-Systems
Repository: openproject-mcp-server
Workflow name: publish.yml
Environment name: pypi
```

### Permission Denied

**Error:** `insufficient permissions` or `403 Forbidden`

**Solutions:**
1. Check `id-token: write` permission in workflow
2. Verify you're repository admin
3. Check environment `pypi` has correct URL
4. Ensure environment protection rules allow workflow

### Version Already Exists

**Error:** `File already exists` on PyPI

**Solution:**
```bash
# Bump version in pyproject.toml
[project]
version = "1.0.4"  # Increment

# Never reuse version numbers
# PyPI doesn't allow overwriting
```

### Tag Doesn't Trigger Workflow

**Error:** Tag pushed but workflow doesn't run

**Solutions:**
1. Verify tag matches pattern `v*`
   ```bash
   git tag v1.0.3  # Correct
   git tag 1.0.3   # Won't trigger
   ```
2. Check tag was pushed
   ```bash
   git push origin v1.0.3
   ```
3. Verify workflow file exists and is valid

---

## Security Workflow Issues

### Dependency Review Blocks PR

**Error:** High-severity vulnerabilities detected

**Solutions:**
1. Review vulnerability details in PR
2. Update affected dependency:
   ```bash
   uv sync --upgrade-package vulnerable-package
   ```
3. If false positive, request manual review
4. Check for available security patches

### CodeQL Fails

**Error:** CodeQL analysis fails

**Solutions:**
1. Check for syntax errors in Python code
2. Verify Python version compatibility
3. Review CodeQL logs in Actions tab
4. May need to exclude certain files

### SBOM Generation Fails

**Error:** `cyclonedx-py` command fails

**Solutions:**
```bash
# Test locally
uv run cyclonedx-py environment -o sbom.json --of json

# Check cyclonedx-bom is installed
uv sync --dev

# Verify it's in dev dependencies
```

---

## General Debugging

### View Workflow Logs

1. Go to **Actions** tab in GitHub
2. Click on failed workflow run
3. Click on failed job
4. Expand failed step to see detailed logs

### Re-run Failed Workflows

1. In Actions tab, click failed run
2. Click **Re-run jobs** → **Re-run failed jobs**

### Enable Debug Logging

Add repository secret `ACTIONS_STEP_DEBUG` = `true`

Or add to workflow temporarily:
```yaml
env:
  ACTIONS_STEP_DEBUG: true
```

### Test Workflows Locally

```bash
# Install act
brew install act  # macOS
# or: https://github.com/nektos/act

# Run specific workflow
act -W .github/workflows/ci.yml

# Run specific job
act -j lint

# Use specific runner image
act -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest
```

---

## Common Issues

### uv Cache Issues

**Error:** Dependencies not updating or cache corruption

**Solution:**
```bash
# Clear uv cache locally
rm -rf ~/.cache/uv

# In CI: disable cache temporarily
# Remove or comment out: enable-cache: true
```

### Workflow Not Running

**Check:**
1. Workflow file has valid YAML syntax
2. Triggers are correctly configured
3. Branch/tag names match patterns
4. Repository Actions are enabled

### Rate Limiting

**Error:** GitHub API rate limit exceeded

**Rare but possible:**
- Wait for rate limit reset (usually 1 hour)
- Check if too many workflows running concurrently
- Review Dependabot PR frequency

---

## Getting Help

**GitHub Actions Issues:**
- Review logs in Actions tab
- Check [GitHub Actions documentation](https://docs.github.com/en/actions)
- Search [GitHub Community forums](https://github.community/)

**uv Issues:**
- Check [uv documentation](https://docs.astral.sh/uv/)
- Review [uv GitHub issues](https://github.com/astral-sh/uv/issues)

**PyPI Publishing:**
- [PyPI Help](https://pypi.org/help/)
- [Trusted Publishing docs](https://docs.pypi.org/trusted-publishers/)

**Ruff Issues:**
- [Ruff documentation](https://docs.astral.sh/ruff/)
- [Configuration reference](https://docs.astral.sh/ruff/configuration/)
