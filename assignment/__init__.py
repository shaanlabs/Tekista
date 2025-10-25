"""
Skill-Based Task Assignment Engine
Implements intelligent task assignment based on skills, experience, and workload
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class SkillLevel(Enum):
    """Skill proficiency levels"""
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3

class AssignmentStrategy(Enum):
    """Task assignment strategies"""
    SKILL_MATCH = "skill_match"  # Prioritize skill match
    WORKLOAD_BALANCE = "workload_balance"  # Prioritize balanced workload
    PERFORMANCE = "performance"  # Prioritize high performers
    HYBRID = "hybrid"  # Combine all factors

class AssignmentMetrics:
    """Metrics for task assignment scoring"""
    
    # Weighting factors for hybrid scoring
    SKILL_MATCH_WEIGHT = 0.40  # 40% skill match
    WORKLOAD_WEIGHT = 0.30     # 30% workload balance
    PERFORMANCE_WEIGHT = 0.20  # 20% performance score
    EXPERIENCE_WEIGHT = 0.10   # 10% experience level
    
    # Thresholds
    MIN_SKILL_MATCH = 0.5      # Minimum 50% skill match required
    MAX_WORKLOAD_HOURS = 40    # Maximum hours per week
    
    @staticmethod
    def calculate_skill_match(user_skills: List[str], required_skills: List[str]) -> float:
        """
        Calculate skill match percentage
        
        Args:
            user_skills: List of user's skills
            required_skills: List of required skills for task
            
        Returns:
            Float between 0 and 1 representing skill match percentage
        """
        if not required_skills:
            return 1.0
        
        if not user_skills:
            return 0.0
        
        user_skills_set = set(skill.lower() for skill in user_skills)
        required_skills_set = set(skill.lower() for skill in required_skills)
        
        # Calculate intersection
        matched_skills = user_skills_set.intersection(required_skills_set)
        
        # Return percentage of required skills matched
        match_percentage = len(matched_skills) / len(required_skills_set)
        return match_percentage
    
    @staticmethod
    def calculate_workload_score(current_hours: float, max_hours: float = 40) -> float:
        """
        Calculate workload score (lower workload = higher score)
        
        Args:
            current_hours: Current hours assigned to user
            max_hours: Maximum hours per week
            
        Returns:
            Float between 0 and 1 (1 = no workload, 0 = overloaded)
        """
        if current_hours >= max_hours:
            return 0.0
        
        return 1.0 - (current_hours / max_hours)
    
    @staticmethod
    def calculate_experience_score(experience_level: int, max_level: int = 10) -> float:
        """
        Calculate experience score
        
        Args:
            experience_level: User's experience level (1-10)
            max_level: Maximum experience level
            
        Returns:
            Float between 0 and 1
        """
        if experience_level <= 0:
            return 0.0
        
        return min(experience_level / max_level, 1.0)
    
    @staticmethod
    def calculate_performance_score(performance: float) -> float:
        """
        Normalize performance score to 0-1 range
        
        Args:
            performance: Performance score (typically 0-100)
            
        Returns:
            Float between 0 and 1
        """
        if performance <= 0:
            return 0.0
        
        return min(performance / 100.0, 1.0)
    
    @staticmethod
    def calculate_difficulty_adjustment(task_difficulty: int, user_experience: int) -> float:
        """
        Calculate difficulty adjustment factor
        
        Args:
            task_difficulty: Task difficulty (1-10)
            user_experience: User experience level (1-10)
            
        Returns:
            Float adjustment factor (0.5-1.5)
        """
        difficulty_ratio = task_difficulty / user_experience
        
        if difficulty_ratio > 1.5:
            # Task too difficult for user
            return 0.5
        elif difficulty_ratio < 0.5:
            # Task too easy for user (underutilization)
            return 0.8
        else:
            # Good match
            return 1.0
    
    @staticmethod
    def calculate_completion_time_estimate(
        task_difficulty: int,
        user_avg_completion_time: float,
        user_experience: int
    ) -> float:
        """
        Estimate task completion time based on user's average and task difficulty
        
        Args:
            task_difficulty: Task difficulty (1-10)
            user_avg_completion_time: User's average completion time (hours)
            user_experience: User experience level (1-10)
            
        Returns:
            Estimated completion time in hours
        """
        if user_avg_completion_time <= 0:
            # Default estimate: 1 hour per difficulty level
            return float(task_difficulty)
        
        # Adjust based on difficulty and experience
        difficulty_factor = task_difficulty / 5.0  # Normalize to ~1.0 for medium difficulty
        experience_factor = 1.0 / (user_experience / 5.0)  # More experience = faster
        
        return user_avg_completion_time * difficulty_factor * experience_factor

class AssignmentService:
    """Service for intelligent task assignment"""
    
    def __init__(self, strategy: AssignmentStrategy = AssignmentStrategy.HYBRID):
        """
        Initialize assignment service
        
        Args:
            strategy: Assignment strategy to use
        """
        self.strategy = strategy
        self.metrics = AssignmentMetrics()
    
    def auto_assign_task(self, task_id: int, organization_id: int) -> Optional[Dict]:
        """
        Automatically assign a task to the best-suited user
        
        Args:
            task_id: ID of the task to assign
            organization_id: ID of the organization
            
        Returns:
            Dictionary with assignment details or None if assignment failed
        """
        from enterprise.models import UserOrganizationRole
        from models import Task, User, db

        # Fetch task
        task = Task.query.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return None
        
        # Fetch all active users in organization
        users = User.query.join(
            UserOrganizationRole,
            User.id == UserOrganizationRole.user_id
        ).filter(
            UserOrganizationRole.organization_id == organization_id
        ).all()
        
        if not users:
            logger.warning(f"No users found in organization {organization_id}")
            return None
        
        # Calculate scores for each user
        user_scores = []
        
        for user in users:
            score_data = self._calculate_user_score(user, task)
            
            if score_data['skill_match'] < AssignmentMetrics.MIN_SKILL_MATCH:
                logger.debug(f"User {user.id} skill match too low: {score_data['skill_match']}")
                continue
            
            user_scores.append(score_data)
        
        if not user_scores:
            logger.warning(f"No suitable users found for task {task_id}")
            return None
        
        # Sort by overall score (highest first)
        user_scores.sort(key=lambda x: x['overall_score'], reverse=True)
        
        # Assign to top-ranked user
        best_user_data = user_scores[0]
        best_user = User.query.get(best_user_data['user_id'])
        
        # Create assignment record
        from assignment.models import TaskAssignment
        
        assignment = TaskAssignment(
            task_id=task_id,
            assigned_user_id=best_user.id,
            assigned_by_id=None,  # System assignment
            assignment_strategy=self.strategy.value,
            skill_match_score=best_user_data['skill_match'],
            workload_score=best_user_data['workload_score'],
            performance_score=best_user_data['performance_score'],
            overall_score=best_user_data['overall_score'],
            estimated_completion_hours=best_user_data['estimated_completion_hours'],
            assignment_reason=best_user_data['reason']
        )
        
        db.session.add(assignment)
        
        # Update task
        task.assignees.append(best_user)
        task.status = 'In Progress'
        
        db.session.commit()
        
        logger.info(f"Task {task_id} assigned to user {best_user.id} with score {best_user_data['overall_score']:.2f}")
        
        return {
            'task_id': task_id,
            'assigned_user_id': best_user.id,
            'assigned_user_name': best_user.username,
            'overall_score': best_user_data['overall_score'],
            'skill_match': best_user_data['skill_match'],
            'workload_score': best_user_data['workload_score'],
            'performance_score': best_user_data['performance_score'],
            'estimated_completion_hours': best_user_data['estimated_completion_hours'],
            'reason': best_user_data['reason']
        }
    
    def _calculate_user_score(self, user, task) -> Dict:
        """
        Calculate assignment score for a user-task pair
        
        Args:
            user: User object
            task: Task object
            
        Returns:
            Dictionary with score components and overall score
        """
        from assignment.models import UserSkillProfile

        # Get user skill profile
        skill_profile = UserSkillProfile.query.filter_by(user_id=user.id).first()
        
        if not skill_profile:
            logger.warning(f"No skill profile found for user {user.id}")
            return {
                'user_id': user.id,
                'skill_match': 0.0,
                'workload_score': 0.0,
                'performance_score': 0.0,
                'overall_score': 0.0,
                'estimated_completion_hours': 0.0,
                'reason': 'No skill profile'
            }
        
        # Calculate individual scores
        skill_match = self.metrics.calculate_skill_match(
            skill_profile.skills or [],
            task.required_skills or []
        )
        
        workload_score = self.metrics.calculate_workload_score(
            skill_profile.current_workload_hours
        )
        
        performance_score = self.metrics.calculate_performance_score(
            skill_profile.performance_score
        )
        
        experience_score = self.metrics.calculate_experience_score(
            skill_profile.experience_level
        )
        
        difficulty_adjustment = self.metrics.calculate_difficulty_adjustment(
            task.difficulty,
            skill_profile.experience_level
        )
        
        estimated_completion = self.metrics.calculate_completion_time_estimate(
            task.difficulty,
            skill_profile.avg_completion_time,
            skill_profile.experience_level
        )
        
        # Calculate overall score based on strategy
        if self.strategy == AssignmentStrategy.SKILL_MATCH:
            overall_score = skill_match
        
        elif self.strategy == AssignmentStrategy.WORKLOAD_BALANCE:
            overall_score = workload_score
        
        elif self.strategy == AssignmentStrategy.PERFORMANCE:
            overall_score = performance_score
        
        else:  # HYBRID
            overall_score = (
                AssignmentMetrics.SKILL_MATCH_WEIGHT * skill_match +
                AssignmentMetrics.WORKLOAD_WEIGHT * workload_score +
                AssignmentMetrics.PERFORMANCE_WEIGHT * performance_score +
                AssignmentMetrics.EXPERIENCE_WEIGHT * experience_score
            ) * difficulty_adjustment
        
        # Determine reason
        reason = self._generate_assignment_reason(
            skill_match, workload_score, performance_score, experience_score
        )
        
        return {
            'user_id': user.id,
            'skill_match': skill_match,
            'workload_score': workload_score,
            'performance_score': performance_score,
            'experience_score': experience_score,
            'overall_score': overall_score,
            'estimated_completion_hours': estimated_completion,
            'reason': reason
        }
    
    def _generate_assignment_reason(
        self,
        skill_match: float,
        workload_score: float,
        performance_score: float,
        experience_score: float
    ) -> str:
        """Generate human-readable assignment reason"""
        reasons = []
        
        if skill_match > 0.8:
            reasons.append("Excellent skill match")
        elif skill_match > 0.6:
            reasons.append("Good skill match")
        
        if workload_score > 0.7:
            reasons.append("Low workload")
        elif workload_score > 0.4:
            reasons.append("Moderate workload")
        
        if performance_score > 0.8:
            reasons.append("High performer")
        
        if experience_score > 0.7:
            reasons.append("Experienced")
        
        return " | ".join(reasons) if reasons else "Suitable match"
    
    def reassign_task(self, task_id: int, organization_id: int, reason: str = None) -> Optional[Dict]:
        """
        Reassign a task to a different user
        
        Args:
            task_id: ID of the task to reassign
            organization_id: ID of the organization
            reason: Reason for reassignment
            
        Returns:
            Dictionary with new assignment details
        """
        from assignment.models import TaskAssignment
        from models import Task

        # Get current assignment
        current_assignment = TaskAssignment.query.filter_by(
            task_id=task_id
        ).order_by(TaskAssignment.assigned_at.desc()).first()
        
        if current_assignment:
            current_assignment.reassigned_at = datetime.utcnow()
            current_assignment.reassignment_reason = reason
        
        # Perform new assignment
        result = self.auto_assign_task(task_id, organization_id)
        
        return result
    
    def get_assignment_recommendations(self, task_id: int, organization_id: int, top_n: int = 5) -> List[Dict]:
        """
        Get top N user recommendations for a task
        
        Args:
            task_id: ID of the task
            organization_id: ID of the organization
            top_n: Number of recommendations to return
            
        Returns:
            List of user recommendations with scores
        """
        from enterprise.models import UserOrganizationRole
        from models import Task, User

        # Fetch task
        task = Task.query.get(task_id)
        if not task:
            return []
        
        # Fetch all active users in organization
        users = User.query.join(
            UserOrganizationRole,
            User.id == UserOrganizationRole.user_id
        ).filter(
            UserOrganizationRole.organization_id == organization_id
        ).all()
        
        # Calculate scores for each user
        user_scores = []
        
        for user in users:
            score_data = self._calculate_user_score(user, task)
            user_scores.append(score_data)
        
        # Sort by overall score (highest first)
        user_scores.sort(key=lambda x: x['overall_score'], reverse=True)
        
        # Return top N
        return user_scores[:top_n]
