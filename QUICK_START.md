# Tekista Project - Quick Start Guide

## 🚀 Setup & Run

```bash
# 1. Clone and setup
git clone <your-repo>
cd tekista-project
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-flask pylint black isort pre-commit

# 3. Setup pre-commit hooks
pre-commit install

# 4. Initialize database
flask db upgrade  # if using migrations
# OR
python -c "from app import create_app; from models import db; app=create_app(); app.app_context().push(); db.create_all()"

# 5. Run tests
pytest -v --cov=.

# 6. Run app
flask run
```

## ✅ Quality Checks

```bash
# Run all quality checks
pre-commit run --all-files

# Test with coverage
pytest --cov=. --cov-report=html
open htmlcov/index.html

# Lint check
pylint app.py models.py api/ --fail-under=9.0

# Format code
black . --line-length=100
isort .
```

## 🧪 Testing Commands

```bash
# All tests
pytest

# With verbose output
pytest -v

# Specific markers
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests
pytest -m api            # API tests
pytest -m auth           # Auth tests
pytest -m ai             # AI tests

# Specific file
pytest tests/test_auth.py -v

# Single test
pytest tests/test_auth.py::TestAuthentication::test_login_required_redirect -v

# Coverage report
pytest --cov=. --cov-report=term-missing
```

## 🔧 Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/your-feature

# 2. Make changes

# 3. Run tests locally
pytest -v

# 4. Check code quality
pylint your_file.py --fail-under=9.0

# 5. Format code
black . --line-length=100
isort .

# 6. Pre-commit checks
pre-commit run --all-files

# 7. Commit (pre-commit hooks run automatically)
git add .
git commit -m "feat: your feature"

# 8. Push (triggers CI/CD)
git push origin feature/your-feature

# 9. Create PR (CI runs automatically)
```

## 📊 CI/CD Status

GitHub Actions runs on every push and PR:
- ✅ **Lint**: Pylint >= 9.0/10
- ✅ **Test**: Pytest with >= 90% coverage
- ✅ **Security**: Dependency vulnerability scan

View status: `.github/workflows/ci.yml`

## 🐛 Troubleshooting

### Tests failing?
```bash
# Clear cache
pytest --cache-clear

# Verbose output
pytest -vv --tb=long

# Stop on first failure
pytest -x
```

### Coverage too low?
```bash
# See uncovered lines
pytest --cov=. --cov-report=term-missing

# HTML report with details
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### Pylint score too low?
```bash
# Detailed output
pylint your_file.py --output-format=colorized

# Fix specific issues
pylint your_file.py --disable=C0114,C0115,C0116  # Ignore docstrings temporarily
```

### Pre-commit hook failing?
```bash
# Run specific hook
pre-commit run black --all-files
pre-commit run pylint --all-files

# Skip hooks (NOT recommended)
git commit --no-verify
```

## 📝 Writing Tests

```python
# tests/test_your_feature.py
import pytest

@pytest.mark.unit
class TestYourFeature:
    """Test your feature."""
    
    def test_something(self, client, user):
        """Test description."""
        # Arrange
        with client.session_transaction() as session:
            session['user_id'] = user.id
        
        # Act
        resp = client.get('/your/endpoint')
        
        # Assert
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['key'] == 'expected_value'
```

## 🔐 Environment Variables

```bash
# Create .env file
DATABASE_URL=sqlite:///tekista.db
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
USE_CELERY=False  # True for production with Celery
OLLAMA_API_URL=http://localhost:11434  # If using AI features
```

## 📚 Key Files

- `pytest.ini` - Pytest configuration
- `.coveragerc` - Coverage settings
- `.pylintrc` - Linting rules
- `.pre-commit-config.yaml` - Pre-commit hooks
- `.github/workflows/ci.yml` - CI/CD pipeline
- `TEST_REPORT.md` - Test documentation
- `AUDIT_SUMMARY.md` - Full audit report

## 🎯 Quality Gates

**Enforced in CI:**
- ✅ Pylint score >= 9.0/10
- ✅ Test coverage >= 90%
- ✅ All tests pass
- ✅ No security vulnerabilities

**Build fails if any gate fails!**

## 🚢 Production Deployment

```bash
# 1. Set environment variables
export USE_CELERY=True
export DATABASE_URL=postgresql://...
export SECRET_KEY=...

# 2. Start Celery worker
celery -A celery_app.celery_app worker -l info -D

# 3. Start Celery beat
celery -A celery_app.celery_app beat -l info -D

# 4. Start Flask app
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

## 🆘 Getting Help

- **Test docs**: `TEST_REPORT.md`
- **Full audit**: `AUDIT_SUMMARY.md`
- **Pytest docs**: https://docs.pytest.org/
- **Pylint docs**: https://pylint.pycqa.org/

---

**Last Updated:** 2025-10-25  
**Minimum Requirements:** Python 3.11, Pytest, Pylint, Coverage >= 90%
