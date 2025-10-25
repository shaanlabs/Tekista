"""
AI Assistant API Routes
Provides endpoints for assistant queries
"""

import logging

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from assistant import AssistantQueryProcessor

logger = logging.getLogger(__name__)

assistant_bp = Blueprint('assistant', __name__, url_prefix='/api/assistant')

# ============================================================================
# ASSISTANT ENDPOINTS
# ============================================================================

@assistant_bp.route('/query', methods=['POST'])
@login_required
def process_query():
    """
    Process natural language query from user
    
    Request Body:
        query: str - User query
        
    Response:
        {
            'success': bool,
            'category': str,
            'message': str,
            'data': dict
        }
    """
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({'error': 'Query required'}), 400
    
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'error': 'Query cannot be empty'}), 400
    
    if len(query) > 500:
        return jsonify({'error': 'Query too long (max 500 characters)'}), 400
    
    # Process query
    result = AssistantQueryProcessor.process_query(current_user.id, query)
    
    return jsonify(result), 200

@assistant_bp.route('/suggestions', methods=['GET'])
@login_required
def get_suggestions():
    """Get suggested queries for the user"""
    return jsonify({
        'suggestions': [
            'Show my pending tasks',
            'Show my completed tasks',
            'How was my performance this week?',
            'Assign me a new task',
            'Show my skills',
            'What\'s my workload?',
            'Recommend a frontend task',
            'Help'
        ]
    }), 200

@assistant_bp.route('/history', methods=['GET'])
@login_required
def get_query_history():
    """
    Get query history for current user
    
    Query Parameters:
        limit: Maximum number of queries (default: 20)
    """
    limit = request.args.get('limit', 20, type=int)
    
    # In a real implementation, you would fetch from a database
    # For now, return empty history
    return jsonify({
        'user_id': current_user.id,
        'history': [],
        'total': 0
    }), 200
