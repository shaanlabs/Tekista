"""
Integration Layer
Connects all systems together: tasks, assignments, performance, notifications, skills
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from assignment import AssignmentService
from assignment.models import TaskAssignment, UserSkillProfile
from models import Project, Task, User, db
from notifications_service import NotificationEvents, NotificationService
from performance import PerformanceService
from performance.models import PerformanceLog
from recommendations import RecommendationEngine
from skills import SkillManager
from socket_events import (emit_performance_update, emit_task_assigned,
                           emit_task_completed)

logger = logging.getLogger(__name__)


class TaskWorkflow:
    """Manages task creation and assignment workflow"""

    @staticmethod
    def create_and_assign_task(
        title: str,
        description: str,
        project_id: int,
        required_skills: List[str],
        difficulty: int = 5,
        priority: str = "medium",
        due_date: Optional[str] = None,
        created_by_id: Optional[int] = None,
    ) -> Dict:
        """
        Create a task and auto-assign it

        Args:
            title: Task title
            description: Task description
            project_id: Project ID
            required_skills: List of required skills
            difficulty: Task difficulty (1-10)
            priority: Task priority (low, medium, high)
            due_date: Due date (ISO format)
            created_by_id: User who created the task

        Returns:
            Dictionary with task and assignment data
        """
        try:
            # Create task
            task = Task(
                title=title,
                description=description,
                project_id=project_id,
                required_skills=required_skills,
                difficulty=difficulty,
                priority=priority,
                due_date=due_date,
                status="To Do",
                created_by=created_by_id,
            )

            db.session.add(task)
            db.session.commit()

            logger.info(f"Created task {task.id}: {title}")

            # Auto-assign task
            assignment_result = TaskWorkflow.auto_assign_task(task.id)

            return {
                "success": True,
                "task_id": task.id,
                "task_title": title,
                "assignment": assignment_result,
                "message": f'Task created and assigned to {assignment_result.get("assigned_to", "queue")}',
            }

        except Exception as exc:
            logger.error(f"Error creating and assigning task: {str(exc)}")
            return {"success": False, "error": str(exc)}

    @staticmethod
    def auto_assign_task(task_id: int) -> Dict:
        """
        Auto-assign a task to the best user

        Args:
            task_id: ID of the task

        Returns:
            Dictionary with assignment data
        """
        try:
            task = Task.query.get(task_id)
            if not task:
                return {"success": False, "error": "Task not found"}

            # Get best user for task
            best_user_id = AssignmentService.find_best_user_for_task(task_id)

            if not best_user_id:
                logger.warning(f"No suitable user found for task {task_id}")
                return {"success": False, "message": "No suitable user available"}

            # Create assignment
            assignment = TaskAssignment(
                task_id=task_id,
                assigned_user_id=best_user_id,
                assignment_status="assigned",
            )

            db.session.add(assignment)
            db.session.commit()

            # Get user details
            user = User.query.get(best_user_id)

            logger.info(f"Assigned task {task_id} to user {best_user_id}")

            # Send notification
            NotificationEvents.task_assigned(
                user_id=best_user_id,
                task_id=task_id,
                task_title=task.title,
                assigned_by_id=task.created_by or 1,
            )

            # Emit real-time notification
            emit_task_assigned(
                user_id=best_user_id,
                task_id=task_id,
                task_title=task.title,
                assigned_by_id=task.created_by or 1,
            )

            return {
                "success": True,
                "assignment_id": assignment.id,
                "assigned_to": user.username if user else "Unknown",
                "assigned_user_id": best_user_id,
            }

        except Exception as exc:
            logger.error(f"Error auto-assigning task: {str(exc)}")
            return {"success": False, "error": str(exc)}

    @staticmethod
    def complete_task(task_id: int, user_id: int, notes: Optional[str] = None) -> Dict:
        """
        Mark task as complete and trigger next assignment

        Args:
            task_id: ID of the task
            user_id: ID of the user completing it
            notes: Completion notes

        Returns:
            Dictionary with completion data
        """
        try:
            # Get assignment
            assignment = TaskAssignment.query.filter_by(
                task_id=task_id, assigned_user_id=user_id
            ).first()

            if not assignment:
                return {"success": False, "error": "Assignment not found"}

            # Mark as complete
            assignment.assignment_status = "completed"
            assignment.completed_at = datetime.utcnow()
            assignment.notes = notes

            db.session.commit()

            task = Task.query.get(task_id)
            task.status = "Completed"
            db.session.commit()

            logger.info(f"Completed task {task_id} by user {user_id}")

            # Update skills
            SkillManager.update_skills_from_completed_task(user_id, task_id)

            # Update performance
            PerformanceService.update_user_performance(user_id, task_id)

            # Get updated performance
            perf_log = (
                PerformanceLog.query.filter_by(user_id=user_id)
                .order_by(PerformanceLog.created_at.desc())
                .first()
            )

            # Send notifications
            NotificationEvents.task_completed(
                user_id=user_id,
                task_id=task_id,
                task_title=task.title,
                completed_by_id=user_id,
            )

            # Emit real-time notification
            emit_task_completed(
                user_id=user_id,
                task_id=task_id,
                task_title=task.title,
                completed_by_id=user_id,
            )

            # Emit performance update
            if perf_log:
                emit_performance_update(
                    user_id=user_id,
                    new_score=perf_log.performance_score,
                    old_score=perf_log.performance_score - (perf_log.score_change or 0),
                )

            # Trigger next task assignment (via Celery)
            from celery_app import assign_next_task

            assign_next_task.delay(user_id)

            return {
                "success": True,
                "task_id": task_id,
                "user_id": user_id,
                "message": "Task completed successfully",
                "performance_updated": True,
                "next_task_queued": True,
            }

        except Exception as exc:
            logger.error(f"Error completing task: {str(exc)}")
            return {"success": False, "error": str(exc)}


class DashboardDataProvider:
    """Provides comprehensive dashboard data"""

    @staticmethod
    def get_user_dashboard_data(user_id: int) -> Dict:
        """
        Get all dashboard data for a user

        Args:
            user_id: ID of the user

        Returns:
            Dictionary with dashboard data
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {"error": "User not found"}

            # Active projects
            projects = (
                db.session.query(Project)
                .filter_by(organization_id=user.organization_id)
                .all()
            )

            active_projects = [
                {
                    "id": p.id,
                    "title": p.title,
                    "status": p.status,
                    "progress": DashboardDataProvider._calculate_project_progress(p.id),
                }
                for p in projects
            ]

            # Active tasks
            active_tasks = (
                db.session.query(TaskAssignment)
                .filter_by(assigned_user_id=user_id, assignment_status="assigned")
                .all()
            )

            active_tasks_data = [
                {
                    "id": a.task.id,
                    "title": a.task.title,
                    "priority": a.task.priority,
                    "due_date": (
                        a.task.due_date.isoformat() if a.task.due_date else None
                    ),
                }
                for a in active_tasks
            ]

            # AI Suggested tasks
            suggestions = RecommendationEngine.recommend_tasks_for_user(
                user_id, top_n=3
            )

            # Performance stats
            perf_log = (
                PerformanceLog.query.filter_by(user_id=user_id)
                .order_by(PerformanceLog.created_at.desc())
                .first()
            )

            performance_stats = {
                "score": perf_log.performance_score if perf_log else 0,
                "on_time_ratio": (perf_log.on_time_ratio * 100) if perf_log else 0,
                "tasks_completed": perf_log.tasks_completed if perf_log else 0,
                "level": DashboardDataProvider._get_performance_level(
                    perf_log.performance_score if perf_log else 0
                ),
            }

            # Skills
            top_skills = SkillManager.get_top_skills(user_id, limit=5)

            # Workload
            profile = UserSkillProfile.query.filter_by(user_id=user_id).first()
            workload = {
                "active_tasks": len(active_tasks),
                "available_capacity": profile.available_capacity() if profile else 0,
                "is_overloaded": profile.is_overloaded() if profile else False,
            }

            return {
                "success": True,
                "user_id": user_id,
                "username": user.username,
                "active_projects": active_projects,
                "active_tasks": active_tasks_data,
                "ai_suggestions": suggestions,
                "performance": performance_stats,
                "top_skills": [
                    {
                        "skill": skill,
                        "proficiency": proficiency,
                        "level": SkillManager.get_skill_level_label(proficiency),
                    }
                    for skill, proficiency in top_skills
                ],
                "workload": workload,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as exc:
            logger.error(f"Error getting dashboard data: {str(exc)}")
            return {"error": str(exc)}

    @staticmethod
    def _calculate_project_progress(project_id: int) -> float:
        """Calculate project completion percentage"""
        try:
            tasks = Task.query.filter_by(project_id=project_id).all()
            if not tasks:
                return 0.0

            completed = sum(1 for t in tasks if t.status == "Completed")
            return (completed / len(tasks)) * 100
        except:
            return 0.0

    @staticmethod
    def _get_performance_level(score: float) -> str:
        """Get performance level label"""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Average"
        elif score >= 45:
            return "Below Average"
        else:
            return "Needs Improvement"

    @staticmethod
    def get_team_dashboard_data(organization_id: int) -> Dict:
        """
        Get team dashboard data

        Args:
            organization_id: ID of the organization

        Returns:
            Dictionary with team data
        """
        try:
            from analytics import AnalyticsEngine

            analytics = AnalyticsEngine.get_comprehensive_analytics(
                organization_id, days=30
            )

            return {
                "success": True,
                "organization_id": organization_id,
                "analytics": analytics,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as exc:
            logger.error(f"Error getting team dashboard data: {str(exc)}")
            return {"error": str(exc)}
