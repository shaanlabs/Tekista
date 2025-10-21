from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from . import ai_assistant
from models import db, Task, Project, User, task_assignees
from datetime import datetime
try:
	import ollama
except ImportError:
	ollama = None
try:
	import openai
except ImportError:
	openai = None

aibp = Blueprint('ai', __name__)

@aibp.route('/api/ai/estimate-duration', methods=['POST'])
@login_required
def estimate_duration():
    """Estimate task duration based on similar tasks"""
    data = request.get_json()
    project_id = data.get('project_id')
    title = data.get('title', '')
    description = data.get('description', '')
    
    if not title:
        return jsonify({"error": "Task title is required"}), 400
    
    days = ai_assistant.estimate_task_duration(title, description, project_id)
    return jsonify({"estimated_days": days})

@aibp.route('/api/ai/risks')
@login_required
def get_risks():
    """Get tasks at risk of missing deadlines"""
    project_id = request.args.get('project_id')
    at_risk = ai_assistant.predict_deadline_risks(project_id)
    
    # Convert to serializable format
    result = [{
        'task_id': item['task'].id,
        'task_title': item['task'].title,
        'risk_score': item['risk_score'],
        'days_remaining': item['days_remaining']
    } for item in at_risk]
    
    return jsonify(result)

@aibp.route('/api/ai/summary')
@login_required
def get_summary():
    """Get AI-generated project summary"""
    project_id = request.args.get('project_id')
    summary = ai_assistant.generate_ai_summary(project_id)
    return jsonify({"summary": summary})

@aibp.route('/api/ai/create-task', methods=['POST'])
@login_required
def create_task_from_nl():
    """Create task from natural language input"""
    data = request.get_json()
    text = data.get('text')
    project_id = data.get('project_id')
    
    if not text:
        return jsonify({"error": "Text input is required"}), 400
    
    result = ai_assistant.process_natural_language_task(
        text, 
        project_id=project_id,
        user_id=current_user.id
    )
    
    if 'error' in result:
        return jsonify({"error": result['error']}), 400
        
    return jsonify({
        "success": True,
        "task_id": result['task_id']
    })

@aibp.route('/api/ai/workload')
@login_required
def get_workload():
    """Get workload balance analysis"""
    project_id = request.args.get('project_id')
    workload = ai_assistant.analyze_workload_balance(project_id)
    return jsonify(workload)

@aibp.route('/api/ai/suggestions')
@login_required
def get_suggestions():
    """Get personalized AI suggestions"""
    user_id = request.args.get('user_id', current_user.id)
    suggestions = ai_assistant.get_ai_suggestions(user_id)
    return jsonify({"suggestions": suggestions})

@aibp.route('/api/ai/chat', methods=['POST'])
@login_required
def chat():
	"""Chat with the AI assistant (Ollama by default, OpenAI as fallback if configured)"""
	data = request.get_json()
	message = data.get('message')
	if not message:
		return jsonify({"error": "Message is required"}), 400

	try:
		# Get user context
		user = User.query.get(current_user.id)
		if not user:
			return jsonify({"error": "User not found"}), 404
		# Get recent tasks for context
		tasks = Task.query.join(
			task_assignees, Task.id == task_assignees.c.task_id
		).filter(
			task_assignees.c.user_id == user.id,
			Task.status != 'Done'
		).order_by(Task.due_date.asc()).limit(5).all()
		# Prepare context
		context = f"Current user: {user.username}\n"
		context += f"Current time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\n"
		if tasks:
			context += "=== Your Upcoming Tasks ===\n"
			for task in tasks:
				context += f"- {task.title} (Due: {task.due_date}, Priority: {task.priority})\n"

		provider = current_app.config.get('AI_PROVIDER', 'ollama').lower()
		temperature = float(current_app.config.get('AI_TEMPERATURE', 0.7))
		max_tokens = int(current_app.config.get('AI_MAX_TOKENS', 500))

		if provider == 'ollama':
			if not ollama:
				return jsonify({"error": "Ollama library not installed"}), 500
			host = current_app.config.get('OLLAMA_HOST', 'http://localhost:11434')
			model = current_app.config.get('OLLAMA_MODEL', 'llama3')
			client = ollama.Client(host=host)
			result = client.chat(
				model=model,
				messages=[
					{"role": "system", "content": "You are a helpful task management assistant. Use the provided context. Be concise and helpful.\n\n" + context},
					{"role": "user", "content": message},
				],
				options={
					"temperature": temperature,
					"num_predict": max_tokens,
				},
			)
			return jsonify({"response": result["message"]["content"].strip()})

		# Fallback to OpenAI if configured
		if not openai:
			return jsonify({"error": "OpenAI library not installed and Ollama not selected"}), 500
		api_key = current_app.config.get('OPENAI_API_KEY')
		if not api_key:
			return jsonify({"error": "OpenAI API key not configured and Ollama not selected"}), 500
		openai.api_key = api_key
		model = current_app.config.get('AI_MODEL', 'gpt-3.5-turbo')
		response = openai.ChatCompletion.create(
			model=model,
			messages=[
				{"role": "system", "content": "You are a helpful task management assistant. Use the following context to provide relevant responses. Be concise and helpful.\n\n" + context},
				{"role": "user", "content": message}
			],
			max_tokens=max_tokens
		)
		return jsonify({"response": response.choices[0].message['content'].strip()})

	except Exception as e:
		current_app.logger.error(f"Chat error: {str(e)}")
		return jsonify({"error": "Failed to process your request"}), 500
