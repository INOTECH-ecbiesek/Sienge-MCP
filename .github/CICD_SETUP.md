# GitHub Actions CI/CD Configuration
# This file documents the required secrets and configuration for the automated PyPI release pipeline

## 🔐 Required GitHub Secrets

You need to configure these secrets in your GitHub repository:
**Settings > Secrets and variables > Actions > Repository secrets**

### 1. PYPI_API_TOKEN
- **Description**: PyPI API token for automated publishing
- **How to get**: 
  1. Go to https://pypi.org/manage/account/token/
  2. Create a new API token with "Entire account" scope
  3. Copy the token (starts with `pypi-`)
  4. Add as repository secret named `PYPI_API_TOKEN`

### 2. GITHUB_TOKEN
- **Description**: GitHub token for creating releases (automatically provided)
- **Status**: ✅ Automatically available (no setup required)

## 🚀 Pipeline Features

### ✅ **Automated Version Management**
- Auto-increments patch version based on commit count
- Updates `pyproject.toml` automatically
- Commits version changes back to repository

### ✅ **Quality Assurance** 
- Tests on Python 3.10, 3.11, 3.12
- Runs flake8 linting
- Validates package imports
- Checks package build before publishing

### ✅ **Automated Publishing**
- Builds wheel and source distribution
- Publishes to PyPI automatically
- Creates GitHub release with auto-generated notes
- Only runs on `main` branch commits

### ✅ **Smart Triggers**
- **Push to main**: Full pipeline (test → version → build → publish)
- **Pull Requests**: Test only (no publishing)
- **Manual**: Can be triggered manually from GitHub Actions tab

## 📋 Workflow Steps

1. **Test** → Run tests and linting on multiple Python versions
2. **Auto-Version** → Increment version based on new commits  
3. **Build & Publish** → Build package and publish to PyPI
4. **Create Release** → Auto-create GitHub release with notes
5. **Notify** → Success/failure notifications

## 🔧 Customization

### Change Version Strategy
Edit the version logic in the `auto-version` job to:
- Use semantic versioning based on commit messages
- Increment minor/major versions
- Use different versioning schemes

### Add More Tests
Extend the `test` job to include:
- Unit tests with pytest
- Integration tests
- Code coverage reports
- Security scans

## 🎯 Usage

### Trigger Release
```bash
# Simply commit and push to main
git add .
git commit -m "feat: add new feature"
git push origin main
# 🚀 Pipeline automatically runs and publishes new version
```

### Manual Version Control
If you want to manually control versions, modify `pyproject.toml`:
```toml
version = "1.2.0"  # Your desired version
```

Then commit and push - the pipeline will use your version and continue auto-incrementing from there.

## 📊 Monitoring

- **GitHub Actions**: View pipeline status in repository Actions tab
- **PyPI Releases**: https://pypi.org/project/sienge-ecbiesek-mcp/#history
- **GitHub Releases**: Repository Releases tab for auto-generated release notes