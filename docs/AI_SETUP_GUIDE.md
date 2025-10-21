# AI Features Setup Guide

## Quick Start

Follow these steps to enable AI features in your TaskManager application.

## Step 1: Install Dependencies

```bash
# Install all required packages including AI libraries
pip install -r requirements.txt
```

### Key Dependencies
- `openai>=0.27.0` - OpenAI API client
- `scikit-learn>=1.0.0` - Machine learning library
- `numpy>=1.21.0` - Numerical computing
- `pandas>=1.3.0` - Data analysis

## Step 2: Get OpenAI API Key

### Option A: Create New OpenAI Account
1. Visit https://platform.openai.com/signup
2. Sign up with your email
3. Verify your email address
4. Add payment method (required for API access)

### Option B: Use Existing Account
1. Visit https://platform.openai.com/account/api-keys
2. Click "Create new secret key"
3. Copy the key (you won't be able to see it again)

## Step 3: Configure Environment Variables

### Create or Update `.env` file

```bash
# In your project root directory, create or edit .env file
```

### Add These Variables

```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///app.db

# Email Configuration (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# AI Features Configuration
ENABLE_AI_FEATURES=true
OPENAI_API_KEY=sk-your-actual-api-key-here

# AI Model Settings (optional, these are defaults)
AI_MODEL=gpt-3.5-turbo
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=500
```

### Important Notes
- **Never commit `.env` file** to version control
- Add `.env` to `.gitignore`
- Keep your API key secret
- Use different keys for development and production

## Step 4: Verify Installation

### Check Python Packages
```bash
# Verify all packages are installed
pip list | grep -E "openai|scikit-learn|numpy|pandas"
```

### Test OpenAI Connection
```bash
# Create a test script to verify API key works
python -c "
import openai
openai.api_key = 'your-api-key-here'
try:
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[{'role': 'user', 'content': 'Hello'}],
        max_tokens=10
    )
    print('✓ OpenAI API connection successful')
except Exception as e:
    print(f'✗ Error: {e}')
"
```

## Step 5: Start the Application

```bash
# Run the Flask application
flask run

# Or with Python
python app.py
```

### Verify AI Features are Enabled
1. Open http://localhost:5000 in your browser
2. Log in to your account
3. Look for the robot icon (🤖) in the bottom-right corner
4. Click it to open the AI chat interface

## Step 6: Test AI Features

### Test 1: AI Chat
1. Click the robot icon to open the chat
2. Type: "What tasks do I have pending?"
3. You should get a response from the AI assistant

### Test 2: Task Estimation
1. Go to create a new task
2. Enter a task title
3. Click "⏱️ Estimate Duration" button
4. The AI should estimate how long the task will take

### Test 3: Natural Language Task Creation
1. Go to the dashboard
2. Click "Quick Add Task"
3. Type: "Remind me to follow up with client by Friday"
4. The AI should parse this and create a task automatically

### Test 4: AI Summary
1. Go to the dashboard
2. Look for "AI Project Summary" card
3. It should show an AI-generated summary of your projects

## Troubleshooting

### Issue: "OpenAI API key not configured"
**Solution:**
- Verify `OPENAI_API_KEY` is set in `.env`
- Restart the Flask application
- Check that the key is valid and not expired

### Issue: "OpenAI library not installed"
**Solution:**
```bash
pip install openai>=0.27.0
```

### Issue: AI chat not responding
**Solution:**
1. Check server logs for errors
2. Verify API key is valid
3. Check OpenAI account has available credits
4. Verify network connectivity

### Issue: "ENABLE_AI_FEATURES not working"
**Solution:**
- Ensure `ENABLE_AI_FEATURES=true` in `.env`
- Restart the Flask application
- Clear browser cache
- Check that you're logged in

### Issue: Task estimation showing "Not enough data"
**Solution:**
- Complete some tasks in the project first
- Ensure completed tasks have due dates set
- The system needs historical data to make estimates

## Production Deployment

### Security Checklist
- [ ] Use environment variables for all sensitive data
- [ ] Never hardcode API keys
- [ ] Use a secrets management system (AWS Secrets Manager, HashiCorp Vault, etc.)
- [ ] Rotate API keys regularly
- [ ] Monitor API usage and costs
- [ ] Implement rate limiting on AI endpoints
- [ ] Use HTTPS for all connections

### Environment Variables for Production
```env
# Production settings
FLASK_ENV=production
DEBUG=false
ENABLE_AI_FEATURES=true

# Use a production database
DATABASE_URL=postgresql://user:password@localhost/taskmanager

# Secure secret key (generate with: python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=your-secure-random-key-here

# OpenAI Configuration
OPENAI_API_KEY=sk-your-production-api-key

# Optional: Set spending limits
# AI_MAX_REQUESTS_PER_DAY=1000
# AI_MAX_COST_PER_DAY=10.00
```

### Monitoring
```bash
# Monitor API usage
# Check OpenAI dashboard: https://platform.openai.com/account/usage/overview

# Set up alerts for high usage
# Configure email notifications in OpenAI account settings
```

## Cost Estimation

### OpenAI API Pricing (as of May 2024)

**GPT-3.5-turbo** (used by default):
- Input: $0.0005 per 1K tokens
- Output: $0.0015 per 1K tokens

### Example Costs
- 100 chat messages per day: ~$0.10-0.50/day
- 1000 task estimations per month: ~$0.50-1.00/month
- 100 project summaries per month: ~$0.20-0.50/month

**Estimated Monthly Cost**: $5-20 for typical usage

### Cost Control
1. Set spending limits in OpenAI account
2. Monitor usage in OpenAI dashboard
3. Implement rate limiting
4. Use caching for repeated requests
5. Consider using GPT-4 only for critical tasks

## Advanced Configuration

### Custom AI Model
```env
# Use GPT-4 for better quality (more expensive)
AI_MODEL=gpt-4

# Adjust temperature (0.0 = deterministic, 1.0 = creative)
AI_TEMPERATURE=0.5

# Adjust max tokens (higher = longer responses)
AI_MAX_TOKENS=1000
```

### Disable Specific Features
```python
# In config.py, you can disable individual features
ENABLE_AI_CHAT=True
ENABLE_TASK_ESTIMATION=True
ENABLE_DEADLINE_PREDICTION=True
ENABLE_AI_SUMMARY=True
ENABLE_WORKLOAD_ANALYSIS=True
```

### Custom System Prompts
Edit `ai/__init__.py` to customize AI behavior:
```python
# Modify the system prompts for different features
TASK_ESTIMATION_PROMPT = "You are a task estimation expert..."
CHAT_SYSTEM_PROMPT = "You are a helpful task management assistant..."
```

## Next Steps

1. **Explore AI Features**
   - Try all the AI features in the dashboard
   - Test natural language task creation
   - Review AI suggestions

2. **Customize Settings**
   - Adjust AI temperature and max tokens
   - Enable/disable specific features
   - Configure rate limiting

3. **Monitor Usage**
   - Check OpenAI dashboard regularly
   - Review API costs
   - Optimize usage patterns

4. **Gather Feedback**
   - Get team feedback on AI features
   - Identify improvement areas
   - Plan future enhancements

## Support Resources

- **OpenAI Documentation**: https://platform.openai.com/docs
- **OpenAI API Reference**: https://platform.openai.com/docs/api-reference
- **OpenAI Community**: https://community.openai.com
- **TaskManager Documentation**: See `AI_FEATURES.md`

## FAQ

**Q: Is my data sent to OpenAI?**
A: Only the text you send to the AI is sent to OpenAI's servers. Task metadata is processed locally.

**Q: Can I use a different AI provider?**
A: Yes, you can modify the code to use other providers like Anthropic Claude or Google PaLM.

**Q: What if I run out of API credits?**
A: The AI features will stop working. Add more credits to your OpenAI account.

**Q: Can I use this with a free OpenAI account?**
A: No, you need a paid account with a valid payment method.

**Q: How do I disable AI features?**
A: Set `ENABLE_AI_FEATURES=false` in your `.env` file and restart the application.

---

**Last Updated**: May 2024
**Version**: 1.0
