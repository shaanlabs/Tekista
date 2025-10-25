"""
Performance Tracking Service
Automatically tracks user metrics and calculates performance scores
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from assignment.models import (AssignmentStatistics, TaskAssignment,
                               UserSkillProfile)
from models import Task, User, db

logger = logging.getLogger(__name__)

class PerformanceService:
    """Service for tracking and calculating user performance metrics"""
    
    @staticmethod
    def calculate_completion_speed(deadline: datetime, completion_time: datetime) -> float:
        """
        Calculate completion speed (days early/late)
        
        Args:
            deadline: Task deadline
            completion_time: Actual completion time
            
        Returns:
            Float representing days early (positive) or late (negative)
        """
        if not deadline or not completion_time:
            return 0.0
        
        delta = deadline - completion_time
        return delta.total_seconds() / (24 * 3600)  # Convert to days
    
    @staticmethod
    def calculate_on_time_ratio(user_id: int) -> float:
        """
        Calculate percentage of tasks completed on time
        
        Args:
            user_id: ID of the user
            
        Returns:
            Float between 0 and 1 representing on-time completion ratio
        """
        try:
            from assignment.models import TaskAssignment
            
            assignments = TaskAssignment.query.filter_by(
                assigned_user_id=user_id,
                assignment_status='completed'
            ).all()
            
            if not assignments:
                return 0.5  # Default to 50% if no completed tasks
            
            on_time_count = 0
            
            for assignment in assignments:
                if assignment.completed_at and assignment.task.due_date:
                    if assignment.completed_at <= assignment.task.due_date:
                        on_time_count += 1
            
            return on_time_count / len(assignments) if assignments else 0.5
        
        except Exception as exc:
            logger.error(f"Error calculating on-time ratio for user {user_id}: {str(exc)}")
            return 0.5
    
    @staticmethod
    def calculate_skill_accuracy(user_id: int) -> float:
        """
        Calculate skill match accuracy (how well tasks matched user skills)
        
        Args:
            user_id: ID of the user
            
        Returns:
            Float between 0 and 1 representing average skill match
        """
        try:
            from assignment.models import TaskAssignment
            
            assignments = TaskAssignment.query.filter_by(
                assigned_user_id=user_id,
                assignment_status='completed'
            ).all()
            
            if not assignments:
                return 0.5
            
            total_skill_match = sum(a.skill_match_score or 0 for a in assignments)
            return total_skill_match / len(assignments) if assignments else 0.5
        
        except Exception as exc:
            logger.error(f"Error calculating skill accuracy for user {user_id}: {str(exc)}")
            return 0.5
    
    @staticmethod
    def calculate_difficulty_factor(user_id: int) -> float:
        """
        Calculate average difficulty factor (how challenging tasks were)
        
        Args:
            user_id: ID of the user
            
        Returns:
            Float between 0 and 1 representing difficulty factor
        """
        try:
            from assignment.models import TaskAssignment
            
            assignments = TaskAssignment.query.filter_by(
                assigned_user_id=user_id,
                assignment_status='completed'
            ).all()
            
            if not assignments:
                return 0.5
            
            total_difficulty = 0
            count = 0
            
            for assignment in assignments:
                if assignment.task and assignment.task.difficulty:
                    # Normalize difficulty (1-10 scale to 0-1)
                    normalized_difficulty = assignment.task.difficulty / 10.0
                    total_difficulty += normalized_difficulty
                    count += 1
            
            return total_difficulty / count if count > 0 else 0.5
        
        except Exception as exc:
            logger.error(f"Error calculating difficulty factor for user {user_id}: {str(exc)}")
            return 0.5
    
    @staticmethod
    def calculate_performance_score(
        on_time_ratio: float,
        skill_accuracy: float,
        difficulty_factor: float
    ) -> float:
        """
        Calculate overall performance score using weighted formula
        
        Args:
            on_time_ratio: On-time completion ratio (0-1)
            skill_accuracy: Skill match accuracy (0-1)
            difficulty_factor: Average task difficulty (0-1)
            
        Returns:
            Float between 0 and 100 representing performance score
        """
        # Weighted formula
        score = (
            on_time_ratio * 0.5 +      # 50% weight on-time completion
            skill_accuracy * 0.3 +     # 30% weight skill accuracy
            difficulty_factor * 0.2    # 20% weight difficulty
        ) * 100
        
        return max(0, min(100, score))  # Clamp between 0-100
    
    @staticmethod
    def update_user_performance(user_id: int, assignment_id: Optional[int] = None) -> Dict:
        """
        Update user's performance metrics after task completion
        
        Args:
            user_id: ID of the user
            assignment_id: ID of the completed assignment (optional)
            
        Returns:
            Dictionary with updated metrics
        """
        try:
            from performance.models import PerformanceLog
            
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return {"success": False, "error": "User not found"}
            
            # Get user skill profile
            profile = UserSkillProfile.query.filter_by(user_id=user_id).first()
            if not profile:
                logger.warning(f"No skill profile for user {user_id}")
                return {"success": False, "error": "No skill profile"}
            
            # Calculate metrics
            on_time_ratio = PerformanceService.calculate_on_time_ratio(user_id)
            skill_accuracy = PerformanceService.calculate_skill_accuracy(user_id)
            difficulty_factor = PerformanceService.calculate_difficulty_factor(user_id)
            
            # Calculate performance score
            performance_score = PerformanceService.calculate_performance_score(
                on_time_ratio,
                skill_accuracy,
                difficulty_factor
            )
            
            # Get completion statistics
            from assignment.models import TaskAssignment
            
            assignments = TaskAssignment.query.filter_by(
                assigned_user_id=user_id,
                assignment_status='completed'
            ).all()
            
            tasks_completed = len(assignments)
            
            # Calculate average completion time
            total_hours = sum(a.actual_completion_hours or 0 for a in assignments)
            avg_completion_time = total_hours / tasks_completed if tasks_completed > 0 else 0
            
            # Calculate average speed (days early/late)
            speeds = []
            for assignment in assignments:
                if assignment.completed_at and assignment.task.due_date:
                    speed = PerformanceService.calculate_completion_speed(
                        assignment.task.due_date,
                        assignment.completed_at
                    )
                    speeds.append(speed)
            
            avg_completion_speed = sum(speeds) / len(speeds) if speeds else 0
            
            # Update skill profile
            old_score = profile.performance_score
            profile.performance_score = performance_score
            profile.tasks_completed = tasks_completed
            profile.avg_completion_time = avg_completion_time
            
            db.session.commit()
            
            # Create performance log entry
            log_entry = PerformanceLog(
                user_id=user_id,
                assignment_id=assignment_id,
                tasks_completed=tasks_completed,
                on_time_ratio=on_time_ratio,
                skill_accuracy=skill_accuracy,
                difficulty_factor=difficulty_factor,
                avg_completion_time=avg_completion_time,
                avg_completion_speed=avg_completion_speed,
                performance_score=performance_score,
                score_change=performance_score - old_score
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
            logger.info(
                f"Updated performance for user {user_id}: "
                f"{old_score:.1f} → {performance_score:.1f}"
            )
            
            return {
                "success": True,
                "user_id": user_id,
                "tasks_completed": tasks_completed,
                "on_time_ratio": on_time_ratio,
                "skill_accuracy": skill_accuracy,
                "difficulty_factor": difficulty_factor,
                "avg_completion_time": avg_completion_time,
                "avg_completion_speed": avg_completion_speed,
                "performance_score": performance_score,
                "score_change": performance_score - old_score
            }
        
        except Exception as exc:
            logger.error(f"Error updating performance for user {user_id}: {str(exc)}")
            return {"success": False, "error": str(exc)}
    
    @staticmethod
    def get_user_performance_history(user_id: int, days: int = 30) -> List[Dict]:
        """
        Get user's performance history for the last N days
        
        Args:
            user_id: ID of the user
            days: Number of days to look back
            
        Returns:
            List of performance log entries
        """
        try:
            from performance.models import PerformanceLog
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            logs = PerformanceLog.query.filter(
                PerformanceLog.user_id == user_id,
                PerformanceLog.created_at >= cutoff_date
            ).order_by(PerformanceLog.created_at.asc()).all()
            
            return [{
                "id": log.id,
                "created_at": log.created_at.isoformat(),
                "tasks_completed": log.tasks_completed,
                "on_time_ratio": log.on_time_ratio,
                "skill_accuracy": log.skill_accuracy,
                "difficulty_factor": log.difficulty_factor,
                "avg_completion_time": log.avg_completion_time,
                "avg_completion_speed": log.avg_completion_speed,
                "performance_score": log.performance_score,
                "score_change": log.score_change
            } for log in logs]
        
        except Exception as exc:
            logger.error(f"Error getting performance history for user {user_id}: {str(exc)}")
            return []
    
    @staticmethod
    def get_user_performance_summary(user_id: int) -> Dict:
        """
        Get comprehensive performance summary for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with performance summary
        """
        try:
            from performance.models import PerformanceLog
            
            user = User.query.get(user_id)
            if not user:
                return {"error": "User not found"}
            
            profile = UserSkillProfile.query.filter_by(user_id=user_id).first()
            if not profile:
                return {"error": "No skill profile"}
            
            # Get latest log entry
            latest_log = PerformanceLog.query.filter_by(
                user_id=user_id
            ).order_by(PerformanceLog.created_at.desc()).first()
            
            # Get 30-day history
            history = PerformanceService.get_user_performance_history(user_id, days=30)
            
            # Calculate trends
            if len(history) >= 2:
                first_score = history[0]["performance_score"]
                last_score = history[-1]["performance_score"]
                trend = last_score - first_score
                trend_direction = "↑" if trend > 0 else "↓" if trend < 0 else "→"
            else:
                trend = 0
                trend_direction = "→"
            
            return {
                "user_id": user_id,
                "username": user.username,
                "current_performance_score": profile.performance_score,
                "tasks_completed": profile.tasks_completed,
                "avg_completion_time": profile.avg_completion_time,
                "experience_level": profile.experience_level,
                "latest_metrics": {
                    "on_time_ratio": latest_log.on_time_ratio if latest_log else 0,
                    "skill_accuracy": latest_log.skill_accuracy if latest_log else 0,
                    "difficulty_factor": latest_log.difficulty_factor if latest_log else 0,
                    "avg_completion_speed": latest_log.avg_completion_speed if latest_log else 0
                } if latest_log else None,
                "trend": {
                    "direction": trend_direction,
                    "change": trend,
                    "period_days": 30
                },
                "history_count": len(history)
            }
        
        except Exception as exc:
            logger.error(f"Error getting performance summary for user {user_id}: {str(exc)}")
            return {"error": str(exc)}
    
    @staticmethod
    def get_team_performance_summary(organization_id: int) -> Dict:
        """
        Get team-wide performance summary
        
        Args:
            organization_id: ID of the organization
            
        Returns:
            Dictionary with team performance data
        """
        try:
            from enterprise.models import UserOrganizationRole
            
            users = User.query.join(
                UserOrganizationRole,
                User.id == UserOrganizationRole.user_id
            ).filter(
                UserOrganizationRole.organization_id == organization_id
            ).all()
            
            team_data = []
            total_score = 0
            
            for user in users:
                summary = PerformanceService.get_user_performance_summary(user.id)
                if "error" not in summary:
                    team_data.append(summary)
                    total_score += summary["current_performance_score"]
            
            avg_score = total_score / len(team_data) if team_data else 0
            
            # Sort by performance score
            team_data.sort(key=lambda x: x["current_performance_score"], reverse=True)
            
            return {
                "organization_id": organization_id,
                "team_size": len(team_data),
                "average_performance_score": avg_score,
                "top_performers": team_data[:5],
                "all_members": team_data
            }
        
        except Exception as exc:
            logger.error(f"Error getting team performance summary: {str(exc)}")
            return {"error": str(exc)}
    
    @staticmethod
    def get_performance_trends(user_id: int, days: int = 90) -> Dict:
        """
        Get performance trends for analytics
        
        Args:
            user_id: ID of the user
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend data
        """
        try:
            from performance.models import PerformanceLog
            
            history = PerformanceService.get_user_performance_history(user_id, days)
            
            if not history:
                return {"error": "No performance data"}
            
            # Extract data for charts
            dates = [h["created_at"] for h in history]
            scores = [h["performance_score"] for h in history]
            on_time_ratios = [h["on_time_ratio"] * 100 for h in history]
            skill_accuracies = [h["skill_accuracy"] * 100 for h in history]
            difficulty_factors = [h["difficulty_factor"] * 100 for h in history]
            
            # Calculate statistics
            avg_score = sum(scores) / len(scores) if scores else 0
            max_score = max(scores) if scores else 0
            min_score = min(scores) if scores else 0
            
            return {
                "user_id": user_id,
                "period_days": days,
                "data_points": len(history),
                "dates": dates,
                "performance_scores": scores,
                "on_time_ratios": on_time_ratios,
                "skill_accuracies": skill_accuracies,
                "difficulty_factors": difficulty_factors,
                "statistics": {
                    "average_score": avg_score,
                    "max_score": max_score,
                    "min_score": min_score,
                    "score_range": max_score - min_score
                }
            }
        
        except Exception as exc:
            logger.error(f"Error getting performance trends for user {user_id}: {str(exc)}")
            return {"error": str(exc)}
