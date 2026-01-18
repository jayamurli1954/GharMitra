# GitHub Actions CI/CD Pipeline

This repository uses GitHub Actions for Continuous Integration and Continuous Deployment.

## Workflow Overview

The CI/CD pipeline (`.github/workflows/ci-cd.yml`) runs automatically on:
- **Push** to `main` or `develop` branches
- **Pull Requests** to `main` or `develop` branches
- **Manual trigger** via GitHub Actions UI

## Jobs

### 1. Backend Tests & Linting (`backend-tests`)
- Runs Python linting with `flake8`
- Executes backend tests with `pytest`
- Validates Python syntax
- **Platform**: Ubuntu Latest
- **Python Version**: 3.11

### 2. Frontend Build & Tests (`frontend-tests`)
- Installs Node.js dependencies
- Builds web frontend with webpack
- Runs frontend tests (if configured)
- **Platform**: Ubuntu Latest
- **Node Version**: 18

### 3. Validate Dependencies (`validate-dependencies`)
- Validates `backend/requirements.txt`
- Validates `package.json` files
- Ensures all dependencies can be installed

### 4. Security Scan (`security-scan`)
- Runs `bandit` for Python security scanning
- Runs `npm audit` for dependency vulnerabilities
- Helps identify security issues early

### 5. Build Verification (`build-check`)
- Verifies backend imports work correctly
- Ensures web build completes successfully
- Catches build-time errors

## Status Badge

Add this to your README.md to show CI/CD status:

```markdown
![CI/CD](https://github.com/jayamurli1954/GharMitra/workflows/CI/CD%20Pipeline/badge.svg)
```

## Notes

- Most jobs use `continue-on-error: true` to prevent blocking deployments
- Adjust `continue-on-error` flags as your test suite matures
- Security scans are informational and won't block merges
- All jobs run in parallel for faster feedback

## Manual Trigger

To manually run the workflow:
1. Go to **Actions** tab in GitHub
2. Select **CI/CD Pipeline** workflow
3. Click **Run workflow** button

## Customization

To add more checks:
1. Edit `.github/workflows/ci-cd.yml`
2. Add new jobs or steps as needed
3. Push changes to trigger workflow
