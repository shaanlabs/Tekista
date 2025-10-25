# Tekista Project - Status Badges

Add these badges to the top of your README.md:

```markdown
# Tekista - Project Management System

![CI/CD Pipeline](https://github.com/YOUR_USERNAME/Tekista/actions/workflows/ci.yml/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue)
![Code Coverage](https://img.shields.io/codecov/c/github/YOUR_USERNAME/Tekista)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)
![Pylint](https://img.shields.io/badge/pylint-8.0%2B-brightgreen)

[Add your existing project description here]
```

## Replace YOUR_USERNAME with your GitHub username

Example:
```markdown
![CI/CD Pipeline](https://github.com/shaanlabs/Tekista/actions/workflows/ci.yml/badge.svg)
![Code Coverage](https://img.shields.io/codecov/c/github/shaanlabs/Tekista)
```

## Advanced: Dynamic Badges

### Codecov Badge (Coverage)
1. Sign up at https://codecov.io
2. Connect your GitHub repository
3. The badge will auto-update with coverage percentage

### Custom Shields.io Badges
```markdown
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)
![Security](https://img.shields.io/badge/security-passing-brightgreen)
![Maintained](https://img.shields.io/badge/maintained-yes-brightgreen)
```

### Status Badge Colors
- Green (`brightgreen`): Passing, >= 80%
- Yellow (`yellow`): Warning, 60-80%
- Red (`red`): Failing, < 60%

## Complete README Header Example

```markdown
# 🚀 Tekista - Intelligent Project Management

![CI/CD Pipeline](https://github.com/YOUR_USERNAME/Tekista/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue)
![Coverage](https://img.shields.io/codecov/c/github/YOUR_USERNAME/Tekista)
![Pylint](https://img.shields.io/badge/pylint-8.0%2B-brightgreen)
![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

> AI-powered project management system with intelligent task allocation,
> risk prediction, and performance analytics.

## ✨ Features

- 🤖 **AI-Powered Insights** - Smart task estimation and risk prediction
- 📊 **Real-time Analytics** - Performance dashboards and metrics
- 🔄 **Automated Workflows** - Celery-based background processing
- 🔐 **Secure & Scalable** - Enterprise-ready authentication
- 📱 **Modern UI** - Responsive design with real-time updates

## 🚀 Quick Start

\`\`\`bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/Tekista.git
cd Tekista

# Install dependencies
pip install -r requirements.txt

# Run application
flask run
\`\`\`

[Rest of your README...]
```
