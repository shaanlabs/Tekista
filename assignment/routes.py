"""
Task Assignment Routes and API Endpoints
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Task, User
from enterprise import require_permission, audit_log
from enterprise.models import AuditLog
from assignment import AssignmentService, AssignmentStrategy
from assignment.models import (
    UserSkillProfile, TaskAssignment, SkillEndorsement,
    AssignmentFeedback, AssignmentStatistics
)
import logging

logger = logging.getLogger(__name__)

assignment_bp = Blueprint('assignment', __name__, url_prefix='/assignment')

# ============================================================================
# USER SKILL PROFILE ENDPOINTS
# ============================================================================

@assignment_bp.route('/profile', methods=['GET'])
@login_required
def get_skill_profile():
    """Get current user's skill profile"""
    profile = UserSkillProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        return jsonify({'error': 'Skill profile not found'}), 404
    
    return jsonify({
        'user_id': profile.user_id,
        'skills': profile.skills or [],
        'experience_level': profile.experience_level,
        'performance_score': profile.performance_score,
        'tasks_completed': profile.tasks_completed,
        'avg_completion_time': profile.avg_completion_time,
        'current_workload_hours': profile.current_workload_hours,
        'max_weekly_hours': profile.max_weekly_hours,
        'available_capacity': profile.available_capacity(),
        'is_overloaded': profile.is_overloaded(),
        'is_available': profile.is_available,
        'preferred_difficulty_min': profile.preferred_difficulty_min,
        'preferred_difficulty_max': profile.preferred_difficulty_max
    })

@assignment_bp.route('/profile', methods=['PUT'])
@login_required
@audit_log('update', 'skill_profile')
def update_skill_profile():
    """Update current user's skill profile"""
    profile = UserSkillProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        profile = UserSkillProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
    
    data = request.get_json()
    
    if 'skills' in data:
        profile.skills = data['skills']
    
    if 'experience_level' in data:
        profile.experience_level = max(1, min(10, data['experience_level']))
    
    if 'max_weekly_hours' in data:
        profile.max_weekly_hours = max(0, data['max_weekly_hours'])
    
    if 'is_available' in data:
        profile.is_available = data['is_available']
    
    if 'preferred_difficulty_min' in data:
        profile.preferred_difficulty_min = data['preferred_difficulty_min']
    
    if 'preferred_difficulty_max' in data:
        profile.preferred_difficulty_max = data['preferred_difficulty_max']
    
    db.session.commit()
    
    # Log the update
    AuditLog.log_action(
        current_user.id,
        current_user.organization_id,
        'update',
        'skill_profile',
        profile.id,
        new_values=data
    )
    
    return jsonify({'success': True, 'message': 'Profile updated'})

@assignment_bp.route('/profile/skills', methods=['POST'])
@login_required
def add_skill():
    """Add a skill to user's profile"""
    profile = UserSkillProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        profile = UserSkillProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
    
    data = request.get_json()
    skill = data.get('skill')
    
    if not skill:
        return jsonify({'error': 'Skill name required'}), 400
    
    profile.add_skill(skill)
    
    return jsonify({'success': True, 'message': f'Skill "{skill}" added'})

@assignment_bp.route('/profile/skills/<skill>', methods=['DELETE'])
@login_required
def remove_skill(skill):
    """Remove a skill from user's profile"""
    profile = UserSkillProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        return jsonify({'error': 'Skill profile not found'}), 404
    
    profile.remove_skill(skill)
    
    return jsonify({'success': True, 'message': f'Skill "{skill}" removed'})

# ============================================================================
# TASK ASSIGNMENT ENDPOINTS
# ============================================================================

@assignment_bp.route('/tasks/<int:task_id>/auto-assign', methods=['POST'])
@login_required
@require_permission('assign_tasks')
def auto_assign_task(task_id):
    """Automatically assign a task"""
    data = request.get_json() or {}
    strategy = data.get('strategy', 'hybrid')
    
    try:
        strategy_enum = AssignmentStrategy[strategy.upper()]
    except KeyError:
        return jsonify({'error': f'Invalid strategy: {strategy}'}), 400
    
    service = AssignmentService(strategy=strategy_enum)
    result = service.auto_assign_task(task_id, current_user.organization_id)
    
    if not result:
        return jsonify({'error': 'Failed to assign task'}), 400
    
    return jsonify(result), 201

@assignment_bp.route('/tasks/<int:task_id>/recommendations', methods=['GET'])
@login_required
def get_assignment_recommendations(task_id):
    """Get top user recommendations for a task"""
    top_n = request.args.get('top_n', 5, type=int)
    
    service = AssignmentService()
    recommendations = service.get_assignment_recommendations(
        task_id,
        current_user.organization_id,
        top_n
    )
    
    return jsonify({
        'task_id': task_id,
        'recommendations': [
            {
                'user_id': rec['user_id'],
                'overall_score': rec['overall_score'],
                'skill_match': rec['skill_match'],
                'workload_score': rec['workload_score'],
                'performance_score': rec['performance_score'],
                'estimated_completion_hours': rec['estimated_completion_hours'],
                'reason': rec['reason']
            }
            for rec in recommendations
        ]
    })

@assignment_bp.route('/tasks/<int:task_id>/reassign', methods=['POST'])
@login_required
@require_permission('assign_tasks')
def reassign_task(task_id):
    """Reassign a task to a different user"""
    data = request.get_json() or {}
    reason = data.get('reason', 'Manual reassignment')
    
    service = AssignmentService()
    result = service.reassign_task(task_id, current_user.organization_id, reason)
    
    if not result:
        return jsonify({'error': 'Failed to reassign task'}), 400
    
    return jsonify(result)

@assignment_bp.route('/assignments/<int:assignment_id>/complete', methods=['POST'])
@login_required
def complete_assignment(assignment_id):
    """Mark assignment as completed"""
    assignment = TaskAssignment.query.get_or_404(assignment_id)
    
    # Check authorization
    if assignment.assigned_user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json() or {}
    actual_hours = data.get('actual_hours')
    
    assignment.mark_completed(actual_hours)
    
    # Update user statistics
    stats = AssignmentStatistics.query.filter_by(
        user_id=current_user.id
    ).first()
    
    if stats:
        stats.update_metrics()
    
    return jsonify({'success': True, 'message': 'Assignment completed'})

@assignment_bp.route('/assignments/<int:assignment_id>/feedback', methods=['POST'])
@login_required
def submit_assignment_feedback(assignment_id):
    """Submit feedback on an assignment"""
    assignment = TaskAssignment.query.get_or_404(assignment_id)
    
    # Check authorization
    if assignment.assigned_user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    feedback = AssignmentFeedback(
        assignment_id=assignment_id,
        difficulty_rating=data.get('difficulty_rating'),
        skill_match_rating=data.get('skill_match_rating'),
        workload_rating=data.get('workload_rating'),
        comments=data.get('comments'),
        suggestions=data.get('suggestions')
    )
    
    db.session.add(feedback)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Feedback submitted'}), 201

# ============================================================================
# SKILL ENDORSEMENT ENDPOINTS
# ============================================================================

@assignment_bp.route('/users/<int:user_id>/endorse', methods=['POST'])
@login_required
def endorse_skill(user_id):
    """Endorse a skill for another user"""
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot endorse your own skills'}), 400
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    skill = data.get('skill')
    level = data.get('level', 1)
    
    if not skill:
        return jsonify({'error': 'Skill name required'}), 400
    
    # Check if endorsement already exists
    existing = SkillEndorsement.query.filter_by(
        user_id=user_id,
        endorsed_by_id=current_user.id,
        skill=skill
    ).first()
    
    if existing:
        existing.endorsement_level = max(1, min(5, level))
        db.session.commit()
        return jsonify({'success': True, 'message': 'Endorsement updated'})
    
    endorsement = SkillEndorsement(
        user_id=user_id,
        endorsed_by_id=current_user.id,
        skill=skill,
        endorsement_level=max(1, min(5, level))
    )
    
    db.session.add(endorsement)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Skill endorsed'}), 201

@assignment_bp.route('/users/<int:user_id>/endorsements', methods=['GET'])
@login_required
def get_skill_endorsements(user_id):
    """Get skill endorsements for a user"""
    endorsements = SkillEndorsement.query.filter_by(user_id=user_id).all()
    
    # Group by skill
    skills_dict = {}
    for endorsement in endorsements:
        skill = endorsement.skill
        if skill not in skills_dict:
            skills_dict[skill] = {
                'skill': skill,
                'endorsements': [],
                'avg_level': 0.0,
                'total_endorsements': 0
            }
        
        skills_dict[skill]['endorsements'].append({
            'endorsed_by': endorsement.endorsed_by.username,
            'level': endorsement.endorsement_level
        })
    
    # Calculate averages
    for skill_data in skills_dict.values():
        levels = [e['level'] for e in skill_data['endorsements']]
        skill_data['avg_level'] = sum(levels) / len(levels) if levels else 0
        skill_data['total_endorsements'] = len(levels)
    
    return jsonify(list(skills_dict.values()))

# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@assignment_bp.route('/statistics', methods=['GET'])
@login_required
def get_assignment_statistics():
    """Get assignment statistics for current user"""
    stats = AssignmentStatistics.query.filter_by(user_id=current_user.id).first()
    
    if not stats:
        return jsonify({'error': 'No statistics available'}), 404
    
    return jsonify({
        'total_assignments': stats.total_assignments,
        'completed_assignments': stats.completed_assignments,
        'cancelled_assignments': stats.cancelled_assignments,
        'avg_estimation_accuracy': stats.avg_estimation_accuracy,
        'avg_skill_match_score': stats.avg_skill_match_score,
        'avg_difficulty_assigned': stats.avg_difficulty_assigned,
        'avg_completion_time': stats.avg_completion_time,
        'avg_workload_utilization': stats.avg_workload_utilization,
        'avg_difficulty_rating': stats.avg_difficulty_rating,
        'avg_skill_match_rating': stats.avg_skill_match_rating,
        'avg_workload_rating': stats.avg_workload_rating
    })

@assignment_bp.route('/assignments', methods=['GET'])
@login_required
def list_assignments():
    """List assignments for current user"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    query = TaskAssignment.query.filter_by(assigned_user_id=current_user.id)
    
    if status:
        query = query.filter_by(assignment_status=status)
    
    assignments = query.order_by(TaskAssignment.assigned_at.desc()).paginate(
        page=page,
        per_page=per_page
    )
    
    return jsonify({
        'total': assignments.total,
        'pages': assignments.pages,
        'current_page': page,
        'assignments': [
            {
                'id': a.id,
                'task_id': a.task_id,
                'task_title': a.task.title,
                'assigned_at': a.assigned_at.isoformat(),
                'status': a.assignment_status,
                'skill_match_score': a.skill_match_score,
                'overall_score': a.overall_score,
                'estimated_completion_hours': a.estimated_completion_hours,
                'actual_completion_hours': a.actual_completion_hours
            }
            for a in assignments.items
        ]
    })

@assignment_bp.route('/team-statistics', methods=['GET'])
@login_required
@require_permission('view_team')
def get_team_statistics():
    """Get assignment statistics for team"""
    from enterprise.models import UserOrganizationRole
    
    users = User.query.join(
        UserOrganizationRole,
        User.id == UserOrganizationRole.user_id
    ).filter(
        UserOrganizationRole.organization_id == current_user.organization_id
    ).all()
    
    team_stats = []
    
    for user in users:
        stats = AssignmentStatistics.query.filter_by(user_id=user.id).first()
        
        if stats:
            team_stats.append({
                'user_id': user.id,
                'username': user.username,
                'total_assignments': stats.total_assignments,
                'completed_assignments': stats.completed_assignments,
                'avg_estimation_accuracy': stats.avg_estimation_accuracy,
                'avg_skill_match_score': stats.avg_skill_match_score,
                'avg_completion_time': stats.avg_completion_time,
                'avg_workload_utilization': stats.avg_workload_utilization
            })
    
    return jsonify(team_stats)
