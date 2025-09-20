# GitHub Actions CI/CD Configuration
# This file documents the CI/CD pipeline for quality checks and testing

## 🧪 Pipeline Overview

The CI/CD pipeline focuses on **quality assurance** rather than automatic deployment.
Deployment is handled **manually** for better control and security.

## 🔐 No Secrets Required

The pipeline only runs tests and quality checks - **no deployment secrets needed**!

## 🚀 Pipeline Features

### ✅ **Quality Assurance** 
- Tests on Python 3.10, 3.11, 3.12
- Runs flake8 linting for code quality
- Validates package imports and functionality
- Checks package build and metadata

### ✅ **Build Validation**
- Ensures package can be built correctly
- Validates PyPI metadata with twine
- Displays current version and description
- Confirms readiness for manual deployment

### ✅ **Smart Triggers**
- **Push to main**: Full quality pipeline
- **Pull Requests**: Same quality checks
- **Manual**: Can be triggered manually from GitHub Actions tab

## 📋 Workflow Steps

1. **Test** → Run tests and linting on multiple Python versions
2. **Quality Check** → Build validation and metadata verification
3. **Summary** → Display results and deployment readiness

## 🔧 Manual Deployment Process

### Build and Deploy
```bash
# 1. Update version in pyproject.toml
# 2. Test locally
python -m flake8 src
python -c "import sienge_mcp"

# 3. Build package
python -m build

# 4. Check package
python -m twine check dist/*

# 5. Upload to PyPI
python -m twine upload dist/sienge_ecbiesek_mcp-X.X.X-py3-none-any.whl

# 6. Create git tag (optional)
git tag vX.X.X
git push origin vX.X.X
```

### Benefits of Manual Deployment
- ✅ **Full Control** - You decide when to release
- ✅ **Security** - No PyPI tokens in GitHub
- ✅ **Flexibility** - Test builds locally first
- ✅ **Simplicity** - No complex automation to maintain

## 🎯 Usage

### Quality Check
```bash
# Commit and push - pipeline runs quality checks
git add .
git commit -m "feat: add new feature"
git push origin main
# ✅ Pipeline validates code quality and build
```

### Ready to Deploy?
The pipeline will tell you if the code is ready for deployment!

## 📊 Monitoring

- **GitHub Actions**: View pipeline status in repository Actions tab
- **PyPI Releases**: https://pypi.org/project/sienge-ecbiesek-mcp/#history
- **GitHub Releases**: Repository Releases tab for auto-generated release notes