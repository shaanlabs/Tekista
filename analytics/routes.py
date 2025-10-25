"""
Admin Analytics API Routes
Provides endpoints for analytics data
"""

import logging

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from analytics import AnalyticsEngine
from enterprise import require_permission
from models import User

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/admin/analytics')

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@analytics_bp.route('', methods=['GET'])
@login_required
@require_permission('view_analytics')
def get_comprehensive_analytics():
    """
    Get comprehensive analytics dashboard data
    
    Query Parameters:
        days: Number of days to analyze (default: 30)
    """
    days = request.args.get('days', 30, type=int)
    
    analytics = AnalyticsEngine.get_comprehensive_analytics(
        current_user.organization_id,
        days
    )
    
    return jsonify(analytics), 200

@analytics_bp.route('/team-performance', methods=['GET'])
@login_required
@require_permission('view_analytics')
def get_team_performance():
    """Get team performance summary"""
    days = request.args.get('days', 30, type=int)
    
    performance = AnalyticsEngine.get_team_performance_summary(
        current_user.organization_id,
        days
    )
    
    return jsonify(performance), 200

@analytics_bp.route('/task-distribution', methods=['GET'])
@login_required
@require_permission('view_analytics')
def get_task_distribution():
    """Get task distribution by skill"""
    distribution = AnalyticsEngine.get_task_distribution_by_skill(
        current_user.organization_id
    )
    
    # Convert to list format for charts
    chart_data = [
        {'skill': skill, 'count': count}
        for skill, count in distribution.items()
    ]
    
    return jsonify({
        'organization_id': current_user.organization_id,
        'distribution': chart_data,
        'total_skills': len(distribution)
    }), 200

@analytics_bp.route('/top-performers', methods=['GET'])
@login_required
@require_permission('view_analytics')
def get_top_performers():
    """Get top performing users"""
    limit = request.args.get('limit', 10, type=int)
    
    performers = AnalyticsEngine.get_top_performers(
        current_user.organization_id,
        limit
    )
    
    return jsonify({
        'organization_id': current_user.organization_id,
        'top_performers': performers,
        'total': len(performers)
    }), 200

@analytics_bp.route('/task-completion', methods=['GET'])
@login_required
@require_permission('view_analytics')
def get_task_completion():
    """Get overdue vs completed task ratio"""
    days = request.args.get('days', 30, type=int)
    
    completion = AnalyticsEngine.get_task_completion_ratio(
        current_user.organization_id,
        days
    )
    
    return jsonify(completion), 200

@analytics_bp.route('/performance-trend', methods=['GET'])
@login_required
@require_permission('view_analytics')
def get_performance_trend():
    """Get team performance trend over time"""
    days = request.args.get('days', 30, type=int)
    interval = request.args.get('interval', 'daily')
    
    trend = AnalyticsEngine.get_team_performance_trend(
        current_user.organization_id,
        days,
        interval
    )
    
    return jsonify({
        'organization_id': current_user.organization_id,
        'period_days': days,
        'interval': interval,
        'trend_data': trend
    }), 200

@analytics_bp.route('/projects', methods=['GET'])
@login_required
@require_permission('view_analytics')
def get_projects():
    """Get project statistics"""
    projects = AnalyticsEngine.get_project_statistics(
        current_user.organization_id
    )
    
    return jsonify({
        'organization_id': current_user.organization_id,
        'projects': projects,
        'total_projects': len(projects)
    }), 200

@analytics_bp.route('/productivity', methods=['GET'])
@login_required
@require_permission('view_analytics')
def get_productivity():
    """Get productivity metrics"""
    days = request.args.get('days', 30, type=int)
    
    metrics = AnalyticsEngine.get_productivity_metrics(
        current_user.organization_id,
        days
    )
    
    return jsonify(metrics), 200

@analytics_bp.route('/skill-distribution', methods=['GET'])
@login_required
@require_permission('view_analytics')
def get_skill_distribution():
    """Get skill proficiency distribution"""
    distribution = AnalyticsEngine.get_skill_proficiency_distribution(
        current_user.organization_id
    )
    
    # Convert to list format
    chart_data = [
        {
            'skill': data['skill'],
            'users': data['users_with_skill'],
            'avg_proficiency': data['avg_proficiency'],
            'max_proficiency': data['max_proficiency'],
            'min_proficiency': data['min_proficiency']
        }
        for data in distribution.values()
    ]
    
    # Sort by average proficiency
    chart_data.sort(key=lambda x: x['avg_proficiency'], reverse=True)
    
    return jsonify({
        'organization_id': current_user.organization_id,
        'skills': chart_data,
        'total_skills': len(chart_data)
    }), 200

# ============================================================================
# KPI ENDPOINTS
# ============================================================================

@analytics_bp.route('/kpis', methods=['GET'])
@login_required
@require_permission('view_analytics')
def get_kpis():
    """Get key performance indicators"""
    days = request.args.get('days', 30, type=int)
    
    productivity = AnalyticsEngine.get_productivity_metrics(
        current_user.organization_id,
        days
    )
    
    team_perf = AnalyticsEngine.get_team_performance_summary(
        current_user.organization_id,
        days
    )
    
    completion = AnalyticsEngine.get_task_completion_ratio(
        current_user.organization_id,
        days
    )
    
    projects = AnalyticsEngine.get_project_statistics(
        current_user.organization_id
    )
    
    return jsonify({
        'organization_id': current_user.organization_id,
        'kpis': {
            'total_projects': len(projects),
            'total_tasks': productivity.get('total_tasks', 0),
            'completed_tasks': productivity.get('completed_tasks', 0),
            'completion_rate': productivity.get('completion_rate', 0),
            'productivity_index': productivity.get('productivity_index', 0),
            'team_performance_score': team_perf.get('team_performance_score', 0),
            'on_time_ratio': team_perf.get('on_time_percentage', 0),
            'overdue_tasks': completion.get('overdue', 0),
            'total_users': productivity.get('total_users', 0),
            'avg_performance_score': productivity.get('average_performance_score', 0)
        }
    }), 200

# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================

@analytics_bp.route('/export', methods=['GET'])
@login_required
@require_permission('view_analytics')
def export_analytics():
    """Export analytics data as JSON"""
    days = request.args.get('days', 30, type=int)
    
    analytics = AnalyticsEngine.get_comprehensive_analytics(
        current_user.organization_id,
        days
    )
    
    return jsonify({
        'export_date': analytics.get('generated_at'),
        'data': analytics
    }), 200
