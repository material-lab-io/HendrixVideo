# Release Checklist for Hendrix Video Analysis Pipeline

This checklist should be followed for each release to ensure quality and consistency.

## Pre-Release Checklist

### Code Quality
- [ ] All tests pass locally (`pytest`)
- [ ] Code passes linting (`black --check . && flake8`)
- [ ] No security vulnerabilities (`safety check`)
- [ ] Documentation is up to date
- [ ] CHANGELOG.md is updated
- [ ] Version numbers updated in:
  - [ ] `setup.py`
  - [ ] `pyproject.toml`
  - [ ] `components/__init__.py`
  - [ ] `docs/conf.py` (if applicable)

### Testing
- [ ] Run full test suite on multiple Python versions
- [ ] Test installation from scratch in clean environment
- [ ] Test all example scripts
- [ ] Verify GPU and CPU modes work
- [ ] Test with different video formats
- [ ] Benchmark performance vs previous release

### Documentation
- [ ] Update README.md if needed
- [ ] Update API documentation
- [ ] Review and update guides:
  - [ ] GETTING_STARTED.md
  - [ ] USAGE_GUIDE.md
  - [ ] DEVELOPMENT_GUIDE.md
- [ ] Add migration guide if breaking changes

### Dependencies
- [ ] Review dependency updates
- [ ] Check for security advisories
- [ ] Verify compatibility with latest versions
- [ ] Update requirements files if needed

## Release Process

### 1. Create Release Branch
```bash
git checkout -b release/v2.1.0
```

### 2. Final Checks
- [ ] Run pre-commit hooks: `pre-commit run --all-files`
- [ ] Build package: `python -m build`
- [ ] Test package installation: `pip install dist/*.whl`

### 3. Create Release Commit
```bash
git add -A
git commit -m "chore: prepare release v2.1.0"
```

### 4. Tag Release
```bash
git tag -a v2.1.0 -m "Release version 2.1.0"
```

### 5. Push Changes
```bash
git push origin release/v2.1.0
git push origin v2.1.0
```

### 6. Create GitHub Release
- [ ] Go to GitHub releases page
- [ ] Click "Create a new release"
- [ ] Select the tag `v2.1.0`
- [ ] Use RELEASE_TEMPLATE.md as base
- [ ] Fill in all sections
- [ ] Attach built packages
- [ ] Publish release

### 7. Post-Release
- [ ] Merge release branch to main
- [ ] Update develop branch from main
- [ ] Announce release:
  - [ ] Discord community
  - [ ] Twitter/social media
  - [ ] Mailing list
- [ ] Update project board
- [ ] Close related issues

## Release Notes Template

```markdown
# Release v2.1.0

## Highlights
- Major feature: XXX
- Performance improvement: YYY
- Bug fixes and stability improvements

## What's Changed
- Feature: ... by @username in #PR
- Fix: ... by @username in #PR
- Docs: ... by @username in #PR

## Breaking Changes
- None (or list them)

## Migration Guide
(If applicable)

## Contributors
@user1, @user2, @user3

**Full Changelog**: https://github.com/yourusername/hendrix_12aug/compare/v2.0.0...v2.1.0
```

## Versioning Guidelines

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR** version (X.0.0): Incompatible API changes
- **MINOR** version (0.X.0): New functionality, backwards compatible
- **PATCH** version (0.0.X): Bug fixes, backwards compatible

## Emergency Hotfix Process

For critical bugs in production:

1. Create hotfix branch from main: `git checkout -b hotfix/v2.1.1 main`
2. Apply fix and test thoroughly
3. Update version to patch release
4. Follow steps 3-7 from main release process
5. Cherry-pick fix to develop branch

## Rollback Procedure

If issues discovered post-release:

1. Revert to previous stable release in documentation
2. Add warning to release notes
3. Fix issues in hotfix branch
4. Re-release when ready

Remember: Quality over speed. Take time to ensure each release is stable and well-tested.