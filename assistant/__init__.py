"""
AI Assistant System
Processes natural language queries and returns relevant data
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from models import db, User, Task
from assignment.models import TaskAssignment, UserSkillProfile
from performance.models import PerformanceLog
from recommendations import RecommendationEngine
from skills import SkillManager
import logging
import re

logger = logging.getLogger(__name__)

class AssistantQueryProcessor:
    """Processes natural language queries from users"""
    
    # Query patterns and handlers
    QUERY_PATTERNS = {
        'pending_tasks': [
            r'show.*pending.*task',
            r'pending.*task',
            r'what.*pending',
            r'list.*pending',
            r'my.*pending'
        ],
        'completed_tasks': [
            r'show.*completed.*task',
            r'completed.*task',
            r'what.*completed',
            r'list.*completed',
            r'my.*completed'
        ],
        'performance': [
            r'how.*performance',
            r'my.*performance',
            r'performance.*score',
            r'performance.*this.*week',
            r'performance.*this.*month',
            r'how.*am.*i.*doing'
        ],
        'assign_task': [
            r'assign.*task',
            r'give.*task',
            r'new.*task',
            r'assign.*me',
            r'frontend.*task',
            r'backend.*task',
            r'database.*task'
        ],
        'skills': [
            r'my.*skill',
            r'show.*skill',
            r'skill.*level',
            r'what.*skill',
            r'improve.*skill',
            r'skill.*recommendation'
        ],
        'workload': [
            r'my.*workload',
            r'how.*many.*task',
            r'task.*count',
            r'current.*task',
            r'active.*task'
        ],
        'help': [
            r'help',
            r'what.*can.*do',
            r'available.*command',
            r'command.*list'
        ]
    }
    
    @staticmethod
    def classify_query(query: str) -> str:
        """
        Classify query into a category
        
        Args:
            query: User query string
            
        Returns:
            Query category
        """
        query_lower = query.lower().strip()
        
        for category, patterns in AssistantQueryProcessor.QUERY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return category
        
        return 'unknown'
    
    @staticmethod
    def process_query(user_id: int, query: str) -> Dict:
        """
        Process user query and return relevant data
        
        Args:
            user_id: ID of the user
            query: User query string
            
        Returns:
            Dictionary with response data
        """
        try:
            category = AssistantQueryProcessor.classify_query(query)
            
            logger.info(f"Processing query for user {user_id}: {query} (category: {category})")
            
            if category == 'pending_tasks':
                return AssistantQueryProcessor._handle_pending_tasks(user_id)
            elif category == 'completed_tasks':
                return AssistantQueryProcessor._handle_completed_tasks(user_id)
            elif category == 'performance':
                return AssistantQueryProcessor._handle_performance(user_id, query)
            elif category == 'assign_task':
                return AssistantQueryProcessor._handle_assign_task(user_id, query)
            elif category == 'skills':
                return AssistantQueryProcessor._handle_skills(user_id)
            elif category == 'workload':
                return AssistantQueryProcessor._handle_workload(user_id)
            elif category == 'help':
                return AssistantQueryProcessor._handle_help()
            else:
                return AssistantQueryProcessor._handle_unknown(query)
        
        except Exception as exc:
            logger.error(f"Error processing query: {str(exc)}")
            return {
                'success': False,
                'message': 'Sorry, I encountered an error processing your query.',
                'error': str(exc)
            }
    
    @staticmethod
    def _handle_pending_tasks(user_id: int) -> Dict:
        """Handle pending tasks query"""
        try:
            tasks = db.session.query(TaskAssignment).filter_by(
                assigned_user_id=user_id,
                assignment_status='pending'
            ).all()
            
            if not tasks:
                return {
                    'success': True,
                    'category': 'pending_tasks',
                    'message': '✓ Great! You have no pending tasks.',
                    'data': {
                        'count': 0,
                        'tasks': []
                    }
                }
            
            task_list = []
            for assignment in tasks:
                if assignment.task:
                    task_list.append({
                        'id': assignment.task.id,
                        'title': assignment.task.title,
                        'priority': assignment.task.priority,
                        'due_date': assignment.task.due_date.isoformat() if assignment.task.due_date else None,
                        'status': assignment.assignment_status
                    })
            
            return {
                'success': True,
                'category': 'pending_tasks',
                'message': f'📋 You have {len(task_list)} pending task(s).',
                'data': {
                    'count': len(task_list),
                    'tasks': task_list
                }
            }
        
        except Exception as exc:
            logger.error(f"Error handling pending tasks: {str(exc)}")
            return {'success': False, 'message': 'Error fetching pending tasks'}
    
    @staticmethod
    def _handle_completed_tasks(user_id: int) -> Dict:
        """Handle completed tasks query"""
        try:
            # Get completed tasks from last 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            tasks = db.session.query(TaskAssignment).filter(
                TaskAssignment.assigned_user_id == user_id,
                TaskAssignment.assignment_status == 'completed',
                TaskAssignment.completed_at >= cutoff_date
            ).all()
            
            if not tasks:
                return {
                    'success': True,
                    'category': 'completed_tasks',
                    'message': '📊 No completed tasks in the last 30 days.',
                    'data': {
                        'count': 0,
                        'tasks': []
                    }
                }
            
            task_list = []
            for assignment in tasks:
                if assignment.task:
                    task_list.append({
                        'id': assignment.task.id,
                        'title': assignment.task.title,
                        'completed_at': assignment.completed_at.isoformat() if assignment.completed_at else None,
                        'priority': assignment.task.priority
                    })
            
            return {
                'success': True,
                'category': 'completed_tasks',
                'message': f'✅ You completed {len(task_list)} task(s) in the last 30 days.',
                'data': {
                    'count': len(task_list),
                    'tasks': task_list
                }
            }
        
        except Exception as exc:
            logger.error(f"Error handling completed tasks: {str(exc)}")
            return {'success': False, 'message': 'Error fetching completed tasks'}
    
    @staticmethod
    def _handle_performance(user_id: int, query: str) -> Dict:
        """Handle performance query"""
        try:
            perf_log = db.session.query(PerformanceLog).filter_by(
                user_id=user_id
            ).order_by(PerformanceLog.created_at.desc()).first()
            
            if not perf_log:
                return {
                    'success': True,
                    'category': 'performance',
                    'message': '📈 No performance data available yet.',
                    'data': {}
                }
            
            # Determine time period from query
            period = 'overall'
            if 'week' in query.lower():
                period = 'week'
            elif 'month' in query.lower():
                period = 'month'
            
            return {
                'success': True,
                'category': 'performance',
                'message': f'📊 Your performance score is {perf_log.performance_score:.1f}/100',
                'data': {
                    'performance_score': perf_log.performance_score,
                    'on_time_ratio': perf_log.on_time_ratio,
                    'skill_accuracy': perf_log.skill_accuracy,
                    'difficulty_factor': perf_log.difficulty_factor,
                    'tasks_completed': perf_log.tasks_completed,
                    'period': period,
                    'level': AssistantQueryProcessor._get_performance_level(perf_log.performance_score)
                }
            }
        
        except Exception as exc:
            logger.error(f"Error handling performance query: {str(exc)}")
            return {'success': False, 'message': 'Error fetching performance data'}
    
    @staticmethod
    def _handle_assign_task(user_id: int, query: str) -> Dict:
        """Handle task assignment query"""
        try:
            # Extract skill from query if present
            skill_keywords = ['frontend', 'backend', 'database', 'devops', 'mobile', 'design']
            requested_skill = None
            
            for skill in skill_keywords:
                if skill in query.lower():
                    requested_skill = skill
                    break
            
            # Get recommendations
            recommendations = RecommendationEngine.recommend_tasks_for_user(
                user_id,
                top_n=3
            )
            
            if not recommendations:
                return {
                    'success': True,
                    'category': 'assign_task',
                    'message': '🤔 No suitable tasks available right now.',
                    'data': {
                        'tasks': []
                    }
                }
            
            # Filter by skill if requested
            if requested_skill:
                recommendations = [
                    r for r in recommendations
                    if requested_skill.lower() in ' '.join(r.get('required_skills', [])).lower()
                ][:1]
            
            task_list = []
            for rec in recommendations:
                task_list.append({
                    'id': rec['task_id'],
                    'title': rec['task_title'],
                    'score': rec['recommendation_score'],
                    'difficulty': rec['difficulty'],
                    'priority': rec['priority']
                })
            
            return {
                'success': True,
                'category': 'assign_task',
                'message': f'🎯 I found {len(task_list)} suitable task(s) for you.',
                'data': {
                    'tasks': task_list,
                    'action': 'assign'
                }
            }
        
        except Exception as exc:
            logger.error(f"Error handling assign task: {str(exc)}")
            return {'success': False, 'message': 'Error finding tasks'}
    
    @staticmethod
    def _handle_skills(user_id: int) -> Dict:
        """Handle skills query"""
        try:
            top_skills = SkillManager.get_top_skills(user_id, limit=5)
            recommendations = RecommendationEngine.get_skill_recommendations(user_id, limit=3)
            
            if not top_skills:
                return {
                    'success': True,
                    'category': 'skills',
                    'message': '🎓 You haven\'t developed any skills yet.',
                    'data': {
                        'top_skills': [],
                        'recommendations': []
                    }
                }
            
            return {
                'success': True,
                'category': 'skills',
                'message': f'🎓 Your top skill is {top_skills[0][0]} at {top_skills[0][1]:.0f}%',
                'data': {
                    'top_skills': [
                        {
                            'skill': skill,
                            'proficiency': proficiency,
                            'level': SkillManager.get_skill_level_label(proficiency)
                        }
                        for skill, proficiency in top_skills
                    ],
                    'recommendations': recommendations
                }
            }
        
        except Exception as exc:
            logger.error(f"Error handling skills query: {str(exc)}")
            return {'success': False, 'message': 'Error fetching skills'}
    
    @staticmethod
    def _handle_workload(user_id: int) -> Dict:
        """Handle workload query"""
        try:
            active_tasks = db.session.query(TaskAssignment).filter(
                TaskAssignment.assigned_user_id == user_id,
                TaskAssignment.assignment_status.in_(['assigned', 'in_progress'])
            ).count()
            
            profile = UserSkillProfile.query.filter_by(user_id=user_id).first()
            capacity = profile.available_capacity() if profile else 0
            
            return {
                'success': True,
                'category': 'workload',
                'message': f'📊 You have {active_tasks} active task(s) with {capacity:.1f}h available capacity.',
                'data': {
                    'active_tasks': active_tasks,
                    'available_capacity': capacity,
                    'status': 'overloaded' if capacity < 5 else 'normal'
                }
            }
        
        except Exception as exc:
            logger.error(f"Error handling workload query: {str(exc)}")
            return {'success': False, 'message': 'Error fetching workload'}
    
    @staticmethod
    def _handle_help() -> Dict:
        """Handle help query"""
        return {
            'success': True,
            'category': 'help',
            'message': '💡 Here\'s what I can help you with:',
            'data': {
                'commands': [
                    'Show my pending tasks',
                    'Show my completed tasks',
                    'How was my performance this week?',
                    'Assign me a new task',
                    'Show my skills',
                    'What\'s my workload?',
                    'Recommend a frontend task'
                ]
            }
        }
    
    @staticmethod
    def _handle_unknown(query: str) -> Dict:
        """Handle unknown query"""
        return {
            'success': True,
            'category': 'unknown',
            'message': f'🤔 I didn\'t quite understand "{query}". Try asking for help!',
            'data': {}
        }
    
    @staticmethod
    def _get_performance_level(score: float) -> str:
        """Get performance level label"""
        if score >= 90:
            return 'Excellent'
        elif score >= 75:
            return 'Good'
        elif score >= 60:
            return 'Average'
        elif score >= 45:
            return 'Below Average'
        else:
            return 'Needs Improvement'
