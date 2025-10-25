"""
Skills Management System
Manages user skills, tracks proficiency, and provides recommendations
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from assignment.models import TaskAssignment, UserSkillProfile
from models import Task, User, db

logger = logging.getLogger(__name__)

class SkillManager:
    """Manages user skills and proficiency levels"""
    
    # Predefined skill categories
    SKILL_CATEGORIES = {
        'backend': ['Python', 'Django', 'Flask', 'Node.js', 'Express', 'Java', 'Spring', 'C#', '.NET', 'Go', 'Rust'],
        'frontend': ['JavaScript', 'React', 'Vue.js', 'Angular', 'HTML', 'CSS', 'TypeScript', 'Svelte', 'Next.js'],
        'database': ['SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch', 'Firebase'],
        'devops': ['Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'CI/CD', 'Jenkins', 'GitHub Actions'],
        'mobile': ['React Native', 'Flutter', 'Swift', 'Kotlin', 'iOS', 'Android'],
        'data': ['Data Analysis', 'Machine Learning', 'TensorFlow', 'PyTorch', 'Pandas', 'NumPy'],
        'design': ['UI Design', 'UX Design', 'Figma', 'Adobe XD', 'Sketch', 'Prototyping'],
        'soft': ['Communication', 'Leadership', 'Project Management', 'Problem Solving', 'Teamwork']
    }
    
    @staticmethod
    def initialize_user_skills(user_id: int, initial_skills: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """
        Initialize skills for a user
        
        Args:
            user_id: ID of the user
            initial_skills: Initial skills dictionary
            
        Returns:
            Dictionary of skills
        """
        try:
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return {}
            
            # Get or create skill profile
            profile = UserSkillProfile.query.filter_by(user_id=user_id).first()
            if not profile:
                profile = UserSkillProfile(user_id=user_id)
                db.session.add(profile)
            
            # Initialize skills
            if initial_skills:
                profile.skills = initial_skills
            else:
                profile.skills = {}
            
            db.session.commit()
            
            logger.info(f"Initialized skills for user {user_id}")
            return profile.skills or {}
        
        except Exception as exc:
            logger.error(f"Error initializing skills: {str(exc)}")
            return {}
    
    @staticmethod
    def add_skill(user_id: int, skill_name: str, proficiency: float = 1.0) -> bool:
        """
        Add a skill to user's profile
        
        Args:
            user_id: ID of the user
            skill_name: Name of the skill
            proficiency: Initial proficiency level
            
        Returns:
            True if successful
        """
        try:
            profile = UserSkillProfile.query.filter_by(user_id=user_id).first()
            if not profile:
                profile = UserSkillProfile(user_id=user_id, skills={})
                db.session.add(profile)
            
            if not profile.skills:
                profile.skills = {}
            
            # Add or update skill
            profile.skills[skill_name] = max(proficiency, profile.skills.get(skill_name, 0))
            
            db.session.commit()
            logger.info(f"Added skill '{skill_name}' to user {user_id}")
            return True
        
        except Exception as exc:
            logger.error(f"Error adding skill: {str(exc)}")
            return False
    
    @staticmethod
    def increment_skill(user_id: int, skill_name: str, increment: float = 1.0) -> float:
        """
        Increment skill proficiency
        
        Args:
            user_id: ID of the user
            skill_name: Name of the skill
            increment: Amount to increment
            
        Returns:
            New proficiency level
        """
        try:
            profile = UserSkillProfile.query.filter_by(user_id=user_id).first()
            if not profile:
                profile = UserSkillProfile(user_id=user_id, skills={})
                db.session.add(profile)
            
            if not profile.skills:
                profile.skills = {}
            
            # Increment skill with diminishing returns
            current = profile.skills.get(skill_name, 0)
            new_value = current + increment
            
            # Cap at 100 with diminishing returns
            if new_value > 100:
                # Diminishing returns after 100
                excess = new_value - 100
                new_value = 100 + (excess * 0.1)
            
            profile.skills[skill_name] = new_value
            db.session.commit()
            
            logger.info(f"Incremented '{skill_name}' for user {user_id}: {current:.1f} → {new_value:.1f}")
            return new_value
        
        except Exception as exc:
            logger.error(f"Error incrementing skill: {str(exc)}")
            return 0.0
    
    @staticmethod
    def update_skills_from_completed_task(user_id: int, task_id: int) -> Dict[str, float]:
        """
        Update user skills based on completed task
        
        Args:
            user_id: ID of the user
            task_id: ID of the completed task
            
        Returns:
            Updated skills dictionary
        """
        try:
            task = Task.query.get(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return {}
            
            # Get required skills
            required_skills = task.required_skills or []
            
            if not required_skills:
                logger.info(f"Task {task_id} has no required skills")
                return {}
            
            # Increment each required skill
            increment_amount = SkillManager._calculate_skill_increment(task)
            
            for skill in required_skills:
                SkillManager.increment_skill(user_id, skill, increment_amount)
            
            # Get updated skills
            profile = UserSkillProfile.query.filter_by(user_id=user_id).first()
            return profile.skills if profile else {}
        
        except Exception as exc:
            logger.error(f"Error updating skills from task: {str(exc)}")
            return {}
    
    @staticmethod
    def _calculate_skill_increment(task: Task) -> float:
        """
        Calculate skill increment based on task properties
        
        Args:
            task: Task object
            
        Returns:
            Increment amount
        """
        increment = 1.0
        
        # Increase based on difficulty
        if task.difficulty:
            difficulty_factor = task.difficulty / 10.0
            increment *= (1.0 + difficulty_factor)
        
        # Increase based on priority
        if task.priority:
            priority_multiplier = {
                'low': 1.0,
                'medium': 1.2,
                'high': 1.5
            }
            increment *= priority_multiplier.get(task.priority.lower(), 1.0)
        
        # Bonus for on-time completion
        if task.due_date:
            from datetime import datetime
            if datetime.utcnow().date() <= task.due_date:
                increment *= 1.2
        
        return increment
    
    @staticmethod
    def get_user_skills(user_id: int) -> Dict[str, float]:
        """
        Get all skills for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary of skills and proficiency levels
        """
        try:
            profile = UserSkillProfile.query.filter_by(user_id=user_id).first()
            if not profile:
                return {}
            
            return profile.skills or {}
        
        except Exception as exc:
            logger.error(f"Error getting skills: {str(exc)}")
            return {}
    
    @staticmethod
    def get_skill_proficiency(user_id: int, skill_name: str) -> float:
        """
        Get proficiency level for a specific skill
        
        Args:
            user_id: ID of the user
            skill_name: Name of the skill
            
        Returns:
            Proficiency level (0-100+)
        """
        skills = SkillManager.get_user_skills(user_id)
        return skills.get(skill_name, 0.0)
    
    @staticmethod
    def get_skill_level_label(proficiency: float) -> str:
        """
        Get label for skill proficiency level
        
        Args:
            proficiency: Proficiency level
            
        Returns:
            Label string
        """
        if proficiency < 10:
            return "Beginner"
        elif proficiency < 25:
            return "Novice"
        elif proficiency < 50:
            return "Intermediate"
        elif proficiency < 75:
            return "Advanced"
        elif proficiency < 100:
            return "Expert"
        else:
            return "Master"
    
    @staticmethod
    def get_skill_category(skill_name: str) -> Optional[str]:
        """
        Get category for a skill
        
        Args:
            skill_name: Name of the skill
            
        Returns:
            Category name or None
        """
        for category, skills in SkillManager.SKILL_CATEGORIES.items():
            if skill_name in skills:
                return category
        return None
    
    @staticmethod
    def get_skills_by_category(user_id: int) -> Dict[str, Dict[str, float]]:
        """
        Get user skills organized by category
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary of categories with skills
        """
        user_skills = SkillManager.get_user_skills(user_id)
        categorized = {}
        
        for skill_name, proficiency in user_skills.items():
            category = SkillManager.get_skill_category(skill_name)
            if not category:
                category = 'other'
            
            if category not in categorized:
                categorized[category] = {}
            
            categorized[category][skill_name] = proficiency
        
        return categorized
    
    @staticmethod
    def get_top_skills(user_id: int, limit: int = 5) -> List[Tuple[str, float]]:
        """
        Get top skills for a user
        
        Args:
            user_id: ID of the user
            limit: Maximum number of skills
            
        Returns:
            List of (skill_name, proficiency) tuples
        """
        skills = SkillManager.get_user_skills(user_id)
        sorted_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)
        return sorted_skills[:limit]
    
    @staticmethod
    def get_weakest_skills(user_id: int, limit: int = 5) -> List[Tuple[str, float]]:
        """
        Get weakest skills for a user
        
        Args:
            user_id: ID of the user
            limit: Maximum number of skills
            
        Returns:
            List of (skill_name, proficiency) tuples
        """
        skills = SkillManager.get_user_skills(user_id)
        sorted_skills = sorted(skills.items(), key=lambda x: x[1])
        return sorted_skills[:limit]

class SkillRecommendationEngine:
    """Generates skill recommendations based on user activity"""
    
    @staticmethod
    def get_skill_recommendations(user_id: int, limit: int = 3) -> List[Dict]:
        """
        Get skill recommendations for a user
        
        Args:
            user_id: ID of the user
            limit: Maximum number of recommendations
            
        Returns:
            List of skill recommendations
        """
        try:
            # Get user's completed tasks
            assignments = TaskAssignment.query.filter_by(
                assigned_user_id=user_id,
                assignment_status='completed'
            ).all()
            
            if not assignments:
                return []
            
            # Analyze required skills from completed tasks
            skill_frequency = {}
            
            for assignment in assignments:
                if assignment.task and assignment.task.required_skills:
                    for skill in assignment.task.required_skills:
                        skill_frequency[skill] = skill_frequency.get(skill, 0) + 1
            
            # Get user's current skills
            user_skills = SkillManager.get_user_skills(user_id)
            
            # Find skills that appear frequently but user is weak at
            recommendations = []
            
            for skill, frequency in sorted(skill_frequency.items(), key=lambda x: x[1], reverse=True):
                proficiency = user_skills.get(skill, 0)
                
                # Recommend if skill appears frequently but proficiency is low
                if frequency >= 3 and proficiency < 50:
                    recommendations.append({
                        'skill': skill,
                        'current_proficiency': proficiency,
                        'frequency': frequency,
                        'reason': f"You've used this skill {frequency} times but only have {proficiency:.0f}% proficiency",
                        'level': SkillManager.get_skill_level_label(proficiency),
                        'category': SkillManager.get_skill_category(skill)
                    })
            
            return recommendations[:limit]
        
        except Exception as exc:
            logger.error(f"Error generating recommendations: {str(exc)}")
            return []
    
    @staticmethod
    def get_skill_gaps(user_id: int) -> List[Dict]:
        """
        Identify skill gaps based on task requirements
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of skill gaps
        """
        try:
            # Get available tasks
            available_tasks = Task.query.filter(
                Task.status.in_(['To Do', 'Pending']),
                ~Task.assignees.any(User.id == user_id)
            ).all()
            
            if not available_tasks:
                return []
            
            # Analyze required skills
            skill_requirements = {}
            
            for task in available_tasks:
                if task.required_skills:
                    for skill in task.required_skills:
                        if skill not in skill_requirements:
                            skill_requirements[skill] = []
                        skill_requirements[skill].append({
                            'task_id': task.id,
                            'task_title': task.title,
                            'difficulty': task.difficulty
                        })
            
            # Get user's skills
            user_skills = SkillManager.get_user_skills(user_id)
            
            # Find gaps
            gaps = []
            
            for skill, tasks in skill_requirements.items():
                proficiency = user_skills.get(skill, 0)
                
                # If user doesn't have skill or has low proficiency
                if proficiency < 30:
                    avg_difficulty = sum(t['difficulty'] for t in tasks) / len(tasks) if tasks else 0
                    
                    gaps.append({
                        'skill': skill,
                        'current_proficiency': proficiency,
                        'required_tasks': len(tasks),
                        'avg_task_difficulty': avg_difficulty,
                        'tasks': tasks[:3],  # Top 3 tasks
                        'category': SkillManager.get_skill_category(skill)
                    })
            
            # Sort by number of tasks requiring the skill
            gaps.sort(key=lambda x: x['required_tasks'], reverse=True)
            
            return gaps
        
        except Exception as exc:
            logger.error(f"Error identifying skill gaps: {str(exc)}")
            return []
    
    @staticmethod
    def get_learning_path(user_id: int) -> Dict:
        """
        Generate a learning path for the user
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with learning path
        """
        try:
            recommendations = SkillRecommendationEngine.get_skill_recommendations(user_id, limit=5)
            gaps = SkillRecommendationEngine.get_skill_gaps(user_id)
            top_skills = SkillManager.get_top_skills(user_id, limit=3)
            
            return {
                'user_id': user_id,
                'top_skills': [{'skill': s[0], 'proficiency': s[1]} for s in top_skills],
                'recommendations': recommendations,
                'skill_gaps': gaps[:3],
                'suggested_focus': recommendations[0]['skill'] if recommendations else None,
                'generated_at': datetime.utcnow().isoformat()
            }
        
        except Exception as exc:
            logger.error(f"Error generating learning path: {str(exc)}")
            return {}
