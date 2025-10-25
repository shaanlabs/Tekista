"""
Performance Tracking API Routes
Provides endpoints for performance metrics and analytics
"""

import logging

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from enterprise import require_permission
from enterprise.models import UserOrganizationRole
from models import User, db
from performance import PerformanceService
from performance.models import PerformanceLog, PerformanceSnapshot

logger = logging.getLogger(__name__)

performance_bp = Blueprint('performance', __name__, url_prefix='/api/performance')

# ============================================================================
# USER PERFORMANCE ENDPOINTS
# ============================================================================

@performance_bp.route('/user/<int:user_id>', methods=['GET'])
@login_required
def get_user_performance(user_id):
    """
    Get comprehensive performance data for a user
    
    Args:
        user_id: ID of the user
    """
    # Check authorization
    if user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    summary = PerformanceService.get_user_performance_summary(user_id)
    
    if 'error' in summary:
        return jsonify(summary), 404
    
    return jsonify(summary), 200

@performance_bp.route('/user/<int:user_id>/summary', methods=['GET'])
@login_required
def get_user_performance_summary(user_id):
    """Get performance summary for a user"""
    if user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    summary = PerformanceService.get_user_performance_summary(user_id)
    
    if 'error' in summary:
        return jsonify(summary), 404
    
    return jsonify(summary), 200

@performance_bp.route('/user/<int:user_id>/history', methods=['GET'])
@login_required
def get_user_performance_history(user_id):
    """
    Get performance history for a user
    
    Query Parameters:
        days: Number of days to look back (default: 30)
        limit: Maximum number of entries (default: 100)
    """
    if user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    days = request.args.get('days', 30, type=int)
    limit = request.args.get('limit', 100, type=int)
    
    history = PerformanceService.get_user_performance_history(user_id, days)
    
    return jsonify({
        'user_id': user_id,
        'period_days': days,
        'total_entries': len(history),
        'entries': history[:limit]
    }), 200

@performance_bp.route('/user/<int:user_id>/trends', methods=['GET'])
@login_required
def get_user_performance_trends(user_id):
    """
    Get performance trends for analytics and charts
    
    Query Parameters:
        days: Number of days to analyze (default: 90)
    """
    if user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    days = request.args.get('days', 90, type=int)
    
    trends = PerformanceService.get_performance_trends(user_id, days)
    
    if 'error' in trends:
        return jsonify(trends), 404
    
    return jsonify(trends), 200

@performance_bp.route('/user/<int:user_id>/metrics', methods=['GET'])
@login_required
def get_user_metrics(user_id):
    """
    Get detailed performance metrics for a user
    
    Returns:
        - Current performance score
        - On-time completion ratio
        - Skill accuracy
        - Difficulty factor
        - Average completion time
        - Tasks completed
    """
    if user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    summary = PerformanceService.get_user_performance_summary(user_id)
    
    if 'error' in summary:
        return jsonify(summary), 404
    
    return jsonify({
        'user_id': user_id,
        'performance_score': summary['current_performance_score'],
        'tasks_completed': summary['tasks_completed'],
        'avg_completion_time': summary['avg_completion_time'],
        'experience_level': summary['experience_level'],
        'metrics': summary['latest_metrics'],
        'trend': summary['trend']
    }), 200

# ============================================================================
# TEAM PERFORMANCE ENDPOINTS
# ============================================================================

@performance_bp.route('/team', methods=['GET'])
@login_required
@require_permission('view_team')
def get_team_performance():
    """Get team-wide performance summary"""
    team_summary = PerformanceService.get_team_performance_summary(
        current_user.organization_id
    )
    
    if 'error' in team_summary:
        return jsonify(team_summary), 404
    
    return jsonify(team_summary), 200

@performance_bp.route('/team/top-performers', methods=['GET'])
@login_required
@require_permission('view_team')
def get_top_performers():
    """Get top performing team members"""
    limit = request.args.get('limit', 10, type=int)
    
    team_summary = PerformanceService.get_team_performance_summary(
        current_user.organization_id
    )
    
    if 'error' in team_summary:
        return jsonify(team_summary), 404
    
    top_performers = team_summary['all_members'][:limit]
    
    return jsonify({
        'organization_id': current_user.organization_id,
        'limit': limit,
        'count': len(top_performers),
        'top_performers': top_performers
    }), 200

@performance_bp.route('/team/comparison', methods=['GET'])
@login_required
@require_permission('view_team')
def compare_team_performance():
    """
    Compare performance between two users
    
    Query Parameters:
        user_id_1: First user ID
        user_id_2: Second user ID
        days: Period to compare (default: 30)
    """
    user_id_1 = request.args.get('user_id_1', type=int)
    user_id_2 = request.args.get('user_id_2', type=int)
    days = request.args.get('days', 30, type=int)
    
    if not user_id_1 or not user_id_2:
        return jsonify({'error': 'user_id_1 and user_id_2 required'}), 400
    
    summary_1 = PerformanceService.get_user_performance_summary(user_id_1)
    summary_2 = PerformanceService.get_user_performance_summary(user_id_2)
    
    if 'error' in summary_1 or 'error' in summary_2:
        return jsonify({'error': 'One or both users not found'}), 404
    
    return jsonify({
        'comparison_period_days': days,
        'user_1': summary_1,
        'user_2': summary_2,
        'difference': {
            'score_difference': summary_1['current_performance_score'] - summary_2['current_performance_score'],
            'winner': 'user_1' if summary_1['current_performance_score'] > summary_2['current_performance_score'] else 'user_2'
        }
    }), 200

# ============================================================================
# PERFORMANCE ANALYTICS ENDPOINTS
# ============================================================================

@performance_bp.route('/analytics/distribution', methods=['GET'])
@login_required
@require_permission('view_team')
def get_performance_distribution():
    """
    Get performance score distribution for team
    
    Returns distribution data for histogram/chart
    """
    team_summary = PerformanceService.get_team_performance_summary(
        current_user.organization_id
    )
    
    if 'error' in team_summary:
        return jsonify(team_summary), 404
    
    all_members = team_summary['all_members']
    scores = [m['current_performance_score'] for m in all_members]
    
    # Create distribution buckets
    buckets = {
        '0-20': 0,
        '20-40': 0,
        '40-60': 0,
        '60-80': 0,
        '80-100': 0
    }
    
    for score in scores:
        if score < 20:
            buckets['0-20'] += 1
        elif score < 40:
            buckets['20-40'] += 1
        elif score < 60:
            buckets['40-60'] += 1
        elif score < 80:
            buckets['60-80'] += 1
        else:
            buckets['80-100'] += 1
    
    return jsonify({
        'organization_id': current_user.organization_id,
        'total_members': len(all_members),
        'average_score': team_summary['average_performance_score'],
        'distribution': buckets,
        'scores': scores
    }), 200

@performance_bp.route('/analytics/trends', methods=['GET'])
@login_required
@require_permission('view_team')
def get_team_performance_trends():
    """
    Get team-wide performance trends
    
    Query Parameters:
        days: Number of days to analyze (default: 30)
    """
    days = request.args.get('days', 30, type=int)
    
    # Get all team members
    users = User.query.join(
        UserOrganizationRole,
        User.id == UserOrganizationRole.user_id
    ).filter(
        UserOrganizationRole.organization_id == current_user.organization_id
    ).all()
    
    # Collect trends for each user
    all_trends = []
    
    for user in users:
        trends = PerformanceService.get_performance_trends(user.id, days)
        if 'error' not in trends:
            all_trends.append({
                'user_id': user.id,
                'username': user.username,
                'trends': trends
            })
    
    return jsonify({
        'organization_id': current_user.organization_id,
        'period_days': days,
        'team_members': len(all_trends),
        'trends': all_trends
    }), 200

# ============================================================================
# PERFORMANCE LOGS ENDPOINTS
# ============================================================================

@performance_bp.route('/logs', methods=['GET'])
@login_required
@require_permission('view_audit_log')
def get_performance_logs():
    """
    Get performance logs for organization
    
    Query Parameters:
        page: Page number (default: 1)
        per_page: Entries per page (default: 50)
        user_id: Filter by user (optional)
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    user_id = request.args.get('user_id', type=int)
    
    query = PerformanceLog.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    # Filter by organization
    query = query.join(User).filter(
        User.organization_id == current_user.organization_id
    )
    
    logs = query.order_by(PerformanceLog.created_at.desc()).paginate(
        page=page,
        per_page=per_page
    )
    
    return jsonify({
        'total': logs.total,
        'pages': logs.pages,
        'current_page': page,
        'logs': [log.to_dict() for log in logs.items]
    }), 200

# ============================================================================
# PERFORMANCE SNAPSHOTS ENDPOINTS
# ============================================================================

@performance_bp.route('/snapshots/<int:user_id>', methods=['GET'])
@login_required
def get_performance_snapshots(user_id):
    """
    Get daily performance snapshots for a user
    
    Query Parameters:
        days: Number of days to look back (default: 30)
    """
    if user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    days = request.args.get('days', 30, type=int)
    
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow().date() - timedelta(days=days)
    
    snapshots = PerformanceSnapshot.query.filter(
        PerformanceSnapshot.user_id == user_id,
        PerformanceSnapshot.snapshot_date >= cutoff_date
    ).order_by(PerformanceSnapshot.snapshot_date.asc()).all()
    
    return jsonify({
        'user_id': user_id,
        'period_days': days,
        'snapshots': [{
            'date': s.snapshot_date.isoformat(),
            'tasks_completed_today': s.tasks_completed_today,
            'cumulative_tasks': s.cumulative_tasks,
            'daily_on_time_ratio': s.daily_on_time_ratio,
            'cumulative_on_time_ratio': s.cumulative_on_time_ratio,
            'daily_performance_score': s.daily_performance_score,
            'cumulative_performance_score': s.cumulative_performance_score
        } for s in snapshots]
    }), 200

# ============================================================================
# PERFORMANCE EXPORT ENDPOINTS
# ============================================================================

@performance_bp.route('/export/user/<int:user_id>', methods=['GET'])
@login_required
def export_user_performance(user_id):
    """
    Export user performance data as JSON
    
    Query Parameters:
        format: Export format (json, csv) - default: json
    """
    if user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    export_format = request.args.get('format', 'json')
    
    summary = PerformanceService.get_user_performance_summary(user_id)
    history = PerformanceService.get_user_performance_history(user_id, days=90)
    trends = PerformanceService.get_performance_trends(user_id, days=90)
    
    export_data = {
        'summary': summary,
        'history': history,
        'trends': trends,
        'export_date': datetime.utcnow().isoformat()
    }
    
    if export_format == 'csv':
        # TODO: Implement CSV export
        return jsonify({'error': 'CSV export not yet implemented'}), 501
    
    return jsonify(export_data), 200

# ============================================================================
# PERFORMANCE STATISTICS ENDPOINTS
# ============================================================================

@performance_bp.route('/statistics', methods=['GET'])
@login_required
@require_permission('view_team')
def get_performance_statistics():
    """Get comprehensive performance statistics for organization"""
    team_summary = PerformanceService.get_team_performance_summary(
        current_user.organization_id
    )
    
    if 'error' in team_summary:
        return jsonify(team_summary), 404
    
    all_members = team_summary['all_members']
    scores = [m['current_performance_score'] for m in all_members]
    
    # Calculate statistics
    import statistics
    
    avg_score = statistics.mean(scores) if scores else 0
    median_score = statistics.median(scores) if scores else 0
    stdev_score = statistics.stdev(scores) if len(scores) > 1 else 0
    
    return jsonify({
        'organization_id': current_user.organization_id,
        'total_members': len(all_members),
        'statistics': {
            'average_score': avg_score,
            'median_score': median_score,
            'std_deviation': stdev_score,
            'min_score': min(scores) if scores else 0,
            'max_score': max(scores) if scores else 0,
            'score_range': (max(scores) - min(scores)) if scores else 0
        }
    }), 200
