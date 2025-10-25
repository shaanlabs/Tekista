"""
Task Automation Engine
Handles automatic task assignment and performance tracking when tasks are completed
"""

import logging
from datetime import datetime

from assignment.models import (AssignmentStatistics, TaskAssignment,
                               UserSkillProfile)
from models import Task, db

logger = logging.getLogger(__name__)


class TaskAutomationEngine:
    """Handles automation triggers for task completion"""

    @staticmethod
    def on_task_completed(task_id, actual_hours=None):
        """
        Handle task completion and trigger automation

        Args:
            task_id: ID of the completed task
            actual_hours: Actual hours spent on the task

        Returns:
            Dictionary with automation results
        """
        try:
            from celery_app import (assign_next_task_for_user,
                                    send_performance_update_notification,
                                    update_user_performance_metrics)

            task = Task.query.get(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return {"success": False, "error": "Task not found"}

            # Get the assignment
            assignment = TaskAssignment.query.filter_by(
                task_id=task_id, assignment_status="active"
            ).first()

            if not assignment:
                logger.warning(f"No active assignment found for task {task_id}")
                return {"success": False, "error": "No active assignment"}

            user_id = assignment.assigned_user_id

            # Mark assignment as completed
            assignment.mark_completed(actual_hours)

            # Update user's workload
            user_profile = UserSkillProfile.query.filter_by(user_id=user_id).first()
            if user_profile and actual_hours:
                new_workload = max(
                    0, user_profile.current_workload_hours - actual_hours
                )
                user_profile.update_workload(new_workload)

            db.session.commit()

            # Trigger background jobs
            results = {
                "success": True,
                "task_id": task_id,
                "user_id": user_id,
                "jobs": {},
            }

            # 1. Update performance metrics
            perf_job = update_user_performance_metrics.delay(user_id, assignment.id)
            results["jobs"]["performance_update"] = str(perf_job.id)
            logger.info(f"Queued performance update job for user {user_id}")

            # 2. Assign next task
            next_task_job = assign_next_task_for_user.delay(user_id)
            results["jobs"]["next_task_assignment"] = str(next_task_job.id)
            logger.info(f"Queued next task assignment job for user {user_id}")

            return results

        except Exception as exc:
            logger.error(f"Error in task completion automation: {str(exc)}")
            return {"success": False, "error": str(exc)}

    @staticmethod
    def on_task_status_changed(task_id, old_status, new_status):
        """
        Handle task status changes

        Args:
            task_id: ID of the task
            old_status: Previous status
            new_status: New status
        """
        try:
            # Trigger automation only for completion
            if new_status.lower() == "done" or new_status.lower() == "completed":
                return TaskAutomationEngine.on_task_completed(task_id)

            return {
                "success": True,
                "message": f"Status changed from {old_status} to {new_status}",
            }

        except Exception as exc:
            logger.error(f"Error handling task status change: {str(exc)}")
            return {"success": False, "error": str(exc)}

    @staticmethod
    def on_task_created(task_id):
        """
        Handle new task creation

        Args:
            task_id: ID of the newly created task
        """
        try:
            from celery_app import find_and_assign_tasks_for_available_users

            task = Task.query.get(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return {"success": False, "error": "Task not found"}

            # Queue task assignment job
            job = find_and_assign_tasks_for_available_users.delay(
                task.project.organization_id
            )

            logger.info(f"Queued task assignment job for new task {task_id}")
            return {"success": True, "task_id": task_id, "job_id": str(job.id)}

        except Exception as exc:
            logger.error(f"Error handling task creation: {str(exc)}")
            return {"success": False, "error": str(exc)}


class PerformanceCalculator:
    """Calculates and updates user performance metrics"""

    @staticmethod
    def calculate_performance_score(user_id):
        """
        Calculate comprehensive performance score for a user

        Args:
            user_id: ID of the user

        Returns:
            Dictionary with performance metrics
        """
        try:
            from models import User

            user = User.query.get(user_id)
            if not user:
                return {"error": "User not found"}

            stats = AssignmentStatistics.query.filter_by(user_id=user_id).first()
            profile = UserSkillProfile.query.filter_by(user_id=user_id).first()

            if not stats or not profile:
                return {"error": "User profile or statistics not found"}

            # Calculate components
            completion_rate = (
                stats.completed_assignments / stats.total_assignments
                if stats.total_assignments > 0
                else 0
            )

            estimation_accuracy = stats.avg_estimation_accuracy or 0.5

            workload_balance = 1.0 - (
                profile.current_workload_hours / profile.max_weekly_hours
                if profile.max_weekly_hours > 0
                else 0
            )

            skill_utilization = stats.avg_skill_match_score or 0.5

            # Weighted performance score
            performance_score = (
                completion_rate * 0.35
                + estimation_accuracy * 0.25  # 35% completion rate
                + workload_balance * 0.20  # 25% estimation accuracy
                + skill_utilization  # 20% workload balance
                * 0.20  # 20% skill utilization
            ) * 100

            return {
                "user_id": user_id,
                "performance_score": max(0, min(100, performance_score)),
                "completion_rate": completion_rate * 100,
                "estimation_accuracy": estimation_accuracy * 100,
                "workload_balance": workload_balance * 100,
                "skill_utilization": skill_utilization * 100,
                "total_assignments": stats.total_assignments,
                "completed_assignments": stats.completed_assignments,
            }

        except Exception as exc:
            logger.error(f"Error calculating performance score: {str(exc)}")
            return {"error": str(exc)}

    @staticmethod
    def calculate_team_performance(organization_id):
        """
        Calculate performance metrics for entire team

        Args:
            organization_id: ID of the organization

        Returns:
            List of team member performance data
        """
        try:
            from enterprise.models import UserOrganizationRole
            from models import User

            users = (
                User.query.join(
                    UserOrganizationRole, User.id == UserOrganizationRole.user_id
                )
                .filter(UserOrganizationRole.organization_id == organization_id)
                .all()
            )

            team_performance = []

            for user in users:
                perf = PerformanceCalculator.calculate_performance_score(user.id)
                if "error" not in perf:
                    perf["username"] = user.username
                    team_performance.append(perf)

            # Sort by performance score (descending)
            team_performance.sort(
                key=lambda x: x.get("performance_score", 0), reverse=True
            )

            return team_performance

        except Exception as exc:
            logger.error(f"Error calculating team performance: {str(exc)}")
            return []

    @staticmethod
    def identify_high_performers(organization_id, threshold=80):
        """
        Identify high-performing team members

        Args:
            organization_id: ID of the organization
            threshold: Performance score threshold (0-100)

        Returns:
            List of high performers
        """
        team_perf = PerformanceCalculator.calculate_team_performance(organization_id)
        return [p for p in team_perf if p.get("performance_score", 0) >= threshold]

    @staticmethod
    def identify_at_risk_performers(organization_id, threshold=50):
        """
        Identify performers who need support

        Args:
            organization_id: ID of the organization
            threshold: Performance score threshold (0-100)

        Returns:
            List of at-risk performers
        """
        team_perf = PerformanceCalculator.calculate_team_performance(organization_id)
        return [p for p in team_perf if p.get("performance_score", 0) < threshold]


class WorkloadBalancer:
    """Manages workload distribution and balancing"""

    @staticmethod
    def get_user_available_capacity(user_id):
        """
        Get available capacity for a user

        Args:
            user_id: ID of the user

        Returns:
            Available hours for task assignment
        """
        profile = UserSkillProfile.query.filter_by(user_id=user_id).first()

        if not profile:
            return 0

        return profile.available_capacity()

    @staticmethod
    def is_user_overloaded(user_id):
        """
        Check if user is overloaded

        Args:
            user_id: ID of the user

        Returns:
            Boolean indicating if user is overloaded
        """
        profile = UserSkillProfile.query.filter_by(user_id=user_id).first()

        if not profile:
            return False

        return profile.is_overloaded()

    @staticmethod
    def suggest_workload_rebalancing(organization_id):
        """
        Suggest workload rebalancing for team

        Args:
            organization_id: ID of the organization

        Returns:
            List of rebalancing suggestions
        """
        try:
            from enterprise.models import UserOrganizationRole
            from models import User

            users = (
                User.query.join(
                    UserOrganizationRole, User.id == UserOrganizationRole.user_id
                )
                .filter(UserOrganizationRole.organization_id == organization_id)
                .all()
            )

            overloaded = []
            underutilized = []

            for user in users:
                profile = UserSkillProfile.query.filter_by(user_id=user.id).first()
                if not profile:
                    continue

                utilization = profile.current_workload_hours / profile.max_weekly_hours

                if utilization > 0.9:
                    overloaded.append(
                        {
                            "user_id": user.id,
                            "username": user.username,
                            "utilization": utilization * 100,
                            "current_hours": profile.current_workload_hours,
                            "max_hours": profile.max_weekly_hours,
                        }
                    )
                elif utilization < 0.5:
                    underutilized.append(
                        {
                            "user_id": user.id,
                            "username": user.username,
                            "utilization": utilization * 100,
                            "available_capacity": profile.available_capacity(),
                        }
                    )

            return {
                "overloaded_users": overloaded,
                "underutilized_users": underutilized,
                "rebalancing_needed": len(overloaded) > 0 and len(underutilized) > 0,
            }

        except Exception as exc:
            logger.error(f"Error suggesting workload rebalancing: {str(exc)}")
            return {"error": str(exc)}
