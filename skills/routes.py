"""
Skills Management API Routes
Provides endpoints for skill management and recommendations
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db
from assignment.models import UserSkillProfile
from skills import SkillManager, SkillRecommendationEngine
import logging

logger = logging.getLogger(__name__)

skills_bp = Blueprint('skills', __name__, url_prefix='/api/skills')

# ============================================================================
# SKILL MANAGEMENT ENDPOINTS
# ============================================================================

@skills_bp.route('', methods=['GET'])
@login_required
def get_skills():
    """Get all skills for current user"""
    skills = SkillManager.get_user_skills(current_user.id)
    
    # Add level labels
    skills_with_levels = []
    for skill_name, proficiency in skills.items():
        skills_with_levels.append({
            'skill': skill_name,
            'proficiency': proficiency,
            'level': SkillManager.get_skill_level_label(proficiency),
            'category': SkillManager.get_skill_category(skill_name),
            'percentage': min(proficiency / 100 * 100, 100)
        })
    
    return jsonify({
        'user_id': current_user.id,
        'total_skills': len(skills),
        'skills': sorted(skills_with_levels, key=lambda x: x['proficiency'], reverse=True)
    }), 200

@skills_bp.route('/by-category', methods=['GET'])
@login_required
def get_skills_by_category():
    """Get skills organized by category"""
    categorized = SkillManager.get_skills_by_category(current_user.id)
    
    result = {}
    for category, skills in categorized.items():
        result[category] = [
            {
                'skill': skill_name,
                'proficiency': proficiency,
                'level': SkillManager.get_skill_level_label(proficiency),
                'percentage': min(proficiency / 100 * 100, 100)
            }
            for skill_name, proficiency in sorted(skills.items(), key=lambda x: x[1], reverse=True)
        ]
    
    return jsonify({
        'user_id': current_user.id,
        'categories': result
    }), 200

@skills_bp.route('/top', methods=['GET'])
@login_required
def get_top_skills():
    """Get top skills for current user"""
    limit = request.args.get('limit', 5, type=int)
    
    top_skills = SkillManager.get_top_skills(current_user.id, limit)
    
    return jsonify({
        'user_id': current_user.id,
        'top_skills': [
            {
                'skill': skill,
                'proficiency': proficiency,
                'level': SkillManager.get_skill_level_label(proficiency),
                'percentage': min(proficiency / 100 * 100, 100)
            }
            for skill, proficiency in top_skills
        ]
    }), 200

@skills_bp.route('/weakest', methods=['GET'])
@login_required
def get_weakest_skills():
    """Get weakest skills for current user"""
    limit = request.args.get('limit', 5, type=int)
    
    weakest_skills = SkillManager.get_weakest_skills(current_user.id, limit)
    
    return jsonify({
        'user_id': current_user.id,
        'weakest_skills': [
            {
                'skill': skill,
                'proficiency': proficiency,
                'level': SkillManager.get_skill_level_label(proficiency),
                'percentage': min(proficiency / 100 * 100, 100)
            }
            for skill, proficiency in weakest_skills
        ]
    }), 200

@skills_bp.route('/<skill_name>', methods=['GET'])
@login_required
def get_skill_proficiency(skill_name):
    """Get proficiency for a specific skill"""
    proficiency = SkillManager.get_skill_proficiency(current_user.id, skill_name)
    
    return jsonify({
        'user_id': current_user.id,
        'skill': skill_name,
        'proficiency': proficiency,
        'level': SkillManager.get_skill_level_label(proficiency),
        'percentage': min(proficiency / 100 * 100, 100),
        'category': SkillManager.get_skill_category(skill_name)
    }), 200

@skills_bp.route('', methods=['POST'])
@login_required
def add_skill():
    """Add a new skill"""
    data = request.get_json()
    
    skill_name = data.get('skill')
    proficiency = data.get('proficiency', 1.0)
    
    if not skill_name:
        return jsonify({'error': 'Skill name required'}), 400
    
    success = SkillManager.add_skill(current_user.id, skill_name, proficiency)
    
    if success:
        return jsonify({
            'success': True,
            'skill': skill_name,
            'proficiency': proficiency
        }), 201
    else:
        return jsonify({'error': 'Failed to add skill'}), 500

@skills_bp.route('/<skill_name>', methods=['PUT'])
@login_required
def update_skill(skill_name):
    """Update skill proficiency"""
    data = request.get_json()
    
    proficiency = data.get('proficiency')
    
    if proficiency is None:
        return jsonify({'error': 'Proficiency value required'}), 400
    
    # Get profile and update
    profile = UserSkillProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = UserSkillProfile(user_id=current_user.id, skills={})
        db.session.add(profile)
    
    if not profile.skills:
        profile.skills = {}
    
    profile.skills[skill_name] = proficiency
    db.session.commit()
    
    return jsonify({
        'success': True,
        'skill': skill_name,
        'proficiency': proficiency,
        'level': SkillManager.get_skill_level_label(proficiency)
    }), 200

@skills_bp.route('/<skill_name>/increment', methods=['POST'])
@login_required
def increment_skill(skill_name):
    """Increment skill proficiency"""
    data = request.get_json() or {}
    
    increment = data.get('increment', 1.0)
    
    new_proficiency = SkillManager.increment_skill(current_user.id, skill_name, increment)
    
    return jsonify({
        'success': True,
        'skill': skill_name,
        'new_proficiency': new_proficiency,
        'level': SkillManager.get_skill_level_label(new_proficiency)
    }), 200

@skills_bp.route('/<skill_name>', methods=['DELETE'])
@login_required
def remove_skill(skill_name):
    """Remove a skill"""
    profile = UserSkillProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile or not profile.skills:
        return jsonify({'error': 'Skill not found'}), 404
    
    if skill_name in profile.skills:
        del profile.skills[skill_name]
        db.session.commit()
        
        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': 'Skill not found'}), 404

# ============================================================================
# SKILL RECOMMENDATIONS ENDPOINTS
# ============================================================================

@skills_bp.route('/recommendations', methods=['GET'])
@login_required
def get_recommendations():
    """Get skill recommendations for current user"""
    limit = request.args.get('limit', 3, type=int)
    
    recommendations = SkillRecommendationEngine.get_skill_recommendations(
        current_user.id,
        limit
    )
    
    return jsonify({
        'user_id': current_user.id,
        'recommendations': recommendations,
        'total': len(recommendations)
    }), 200

@skills_bp.route('/gaps', methods=['GET'])
@login_required
def get_skill_gaps():
    """Get skill gaps based on available tasks"""
    gaps = SkillRecommendationEngine.get_skill_gaps(current_user.id)
    
    return jsonify({
        'user_id': current_user.id,
        'gaps': gaps,
        'total': len(gaps)
    }), 200

@skills_bp.route('/learning-path', methods=['GET'])
@login_required
def get_learning_path():
    """Get personalized learning path"""
    path = SkillRecommendationEngine.get_learning_path(current_user.id)
    
    return jsonify(path), 200

# ============================================================================
# SKILL STATISTICS ENDPOINTS
# ============================================================================

@skills_bp.route('/statistics', methods=['GET'])
@login_required
def get_skill_statistics():
    """Get skill statistics for current user"""
    skills = SkillManager.get_user_skills(current_user.id)
    
    if not skills:
        return jsonify({
            'user_id': current_user.id,
            'total_skills': 0,
            'average_proficiency': 0,
            'max_proficiency': 0,
            'min_proficiency': 0
        }), 200
    
    proficiencies = list(skills.values())
    
    return jsonify({
        'user_id': current_user.id,
        'total_skills': len(skills),
        'average_proficiency': sum(proficiencies) / len(proficiencies),
        'max_proficiency': max(proficiencies),
        'min_proficiency': min(proficiencies),
        'master_level_skills': sum(1 for p in proficiencies if p >= 100),
        'expert_level_skills': sum(1 for p in proficiencies if 75 <= p < 100),
        'advanced_level_skills': sum(1 for p in proficiencies if 50 <= p < 75)
    }), 200

# ============================================================================
# SKILL CATEGORIES ENDPOINTS
# ============================================================================

@skills_bp.route('/categories', methods=['GET'])
@login_required
def get_skill_categories():
    """Get available skill categories"""
    return jsonify({
        'categories': SkillManager.SKILL_CATEGORIES
    }), 200

@skills_bp.route('/categories/<category>', methods=['GET'])
@login_required
def get_category_skills(category):
    """Get skills in a specific category"""
    if category not in SkillManager.SKILL_CATEGORIES:
        return jsonify({'error': 'Category not found'}), 404
    
    available_skills = SkillManager.SKILL_CATEGORIES[category]
    user_skills = SkillManager.get_user_skills(current_user.id)
    
    category_skills = []
    for skill in available_skills:
        proficiency = user_skills.get(skill, 0)
        category_skills.append({
            'skill': skill,
            'proficiency': proficiency,
            'level': SkillManager.get_skill_level_label(proficiency),
            'percentage': min(proficiency / 100 * 100, 100),
            'has_skill': skill in user_skills
        })
    
    return jsonify({
        'category': category,
        'skills': category_skills,
        'user_skills_in_category': sum(1 for s in category_skills if s['has_skill'])
    }), 200
