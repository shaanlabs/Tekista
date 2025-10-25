"""
AI Recommendation System Routes
Provides endpoints for task recommendations
"""

import logging

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from recommendations import RecommendationEngine

logger = logging.getLogger(__name__)

recommendations_bp = Blueprint('recommendations', __name__, url_prefix='/api/recommendations')

# ============================================================================
# RECOMMENDATION ENDPOINTS
# ============================================================================

@recommendations_bp.route('/tasks', methods=['GET'])
@login_required
def get_recommended_tasks():
    """
    Get recommended tasks for current user
    
    Query Parameters:
        top_n: Number of recommendations (default: 3)
    """
    top_n = request.args.get('top_n', 3, type=int)
    
    recommendations = RecommendationEngine.recommend_tasks_for_user(
        user_id=current_user.id,
        top_n=top_n,
        organization_id=current_user.organization_id
    )
    
    return jsonify({
        'user_id': current_user.id,
        'recommendations': recommendations,
        'total': len(recommendations)
    }), 200

@recommendations_bp.route('/tasks/personalized', methods=['GET'])
@login_required
def get_personalized_recommendations():
    """Get personalized recommendations with insights"""
    top_n = request.args.get('top_n', 5, type=int)
    
    result = RecommendationEngine.get_personalized_recommendations(
        user_id=current_user.id,
        top_n=top_n,
        organization_id=current_user.organization_id
    )
    
    return jsonify(result), 200

@recommendations_bp.route('/tasks/<int:task_id>/score', methods=['GET'])
@login_required
def get_task_recommendation_score(task_id):
    """Get recommendation score for a specific task"""
    score = RecommendationEngine.calculate_recommendation_score(
        current_user.id,
        task_id
    )
    
    # Get component scores
    components = {
        'skill_overlap': RecommendationEngine.calculate_skill_overlap(current_user.id, task_id),
        'completion_time_fit': RecommendationEngine.calculate_completion_time_similarity(current_user.id, task_id),
        'success_rate': RecommendationEngine.calculate_success_rate_on_similar_tasks(current_user.id, task_id),
        'workload_fit': RecommendationEngine.calculate_workload_fit(current_user.id, task_id),
        'experience_match': RecommendationEngine.calculate_experience_match(current_user.id, task_id)
    }
    
    return jsonify({
        'task_id': task_id,
        'user_id': current_user.id,
        'recommendation_score': score,
        'components': components
    }), 200

@recommendations_bp.route('/analysis', methods=['GET'])
@login_required
def get_recommendation_analysis():
    """Get detailed analysis of why tasks are recommended"""
    top_n = request.args.get('top_n', 3, type=int)
    
    recommendations = RecommendationEngine.recommend_tasks_for_user(
        current_user.id,
        top_n,
        current_user.organization_id
    )
    
    # Add explanations
    analysis = []
    
    for rec in recommendations:
        components = rec['components']
        
        # Generate explanation
        explanation = []
        
        if components['skill_overlap'] > 0.7:
            explanation.append(f"Strong skill match ({components['skill_overlap']*100:.0f}%)")
        elif components['skill_overlap'] > 0.4:
            explanation.append(f"Moderate skill match ({components['skill_overlap']*100:.0f}%)")
        
        if components['success_rate'] > 0.8:
            explanation.append(f"High success rate on similar tasks ({components['success_rate']*100:.0f}%)")
        
        if components['experience_match'] > 0.8:
            explanation.append("Good difficulty match for your experience level")
        
        if components['workload_fit'] > 0.8:
            explanation.append("Fits well with your current workload")
        
        if rec['priority'] == 'high':
            explanation.append("High priority task")
        
        analysis.append({
            'task_id': rec['task_id'],
            'task_title': rec['task_title'],
            'score': rec['recommendation_score'],
            'explanation': explanation,
            'components': components
        })
    
    return jsonify({
        'user_id': current_user.id,
        'analysis': analysis
    }), 200
