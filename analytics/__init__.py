"""
Admin Analytics System
Provides comprehensive analytics for team and project monitoring
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy import func

from assignment.models import TaskAssignment, UserSkillProfile
from models import Project, Task, User, db
from performance.models import PerformanceLog

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Engine for generating analytics data"""

    @staticmethod
    def get_team_performance_summary(organization_id: int, days: int = 30) -> Dict:
        """
        Get team performance summary

        Args:
            organization_id: ID of the organization
            days: Number of days to analyze

        Returns:
            Dictionary with performance data
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Get completed tasks in period
            completed_tasks = (
                db.session.query(TaskAssignment)
                .join(Task)
                .join(Project)
                .filter(
                    Project.organization_id == organization_id,
                    TaskAssignment.assignment_status == "completed",
                    TaskAssignment.completed_at >= cutoff_date,
                )
                .all()
            )

            if not completed_tasks:
                return {
                    "organization_id": organization_id,
                    "period_days": days,
                    "total_tasks_completed": 0,
                    "on_time_tasks": 0,
                    "late_tasks": 0,
                    "on_time_ratio": 0,
                    "avg_completion_time": 0,
                    "team_performance_score": 0,
                }

            # Calculate metrics
            on_time_count = 0
            late_count = 0
            total_time_hours = 0

            for assignment in completed_tasks:
                if assignment.completed_at and assignment.task.due_date:
                    if assignment.completed_at.date() <= assignment.task.due_date:
                        on_time_count += 1
                    else:
                        late_count += 1

                if assignment.created_at and assignment.completed_at:
                    time_diff = (
                        assignment.completed_at - assignment.created_at
                    ).total_seconds() / 3600
                    total_time_hours += time_diff

            total_tasks = len(completed_tasks)
            on_time_ratio = on_time_count / total_tasks if total_tasks > 0 else 0
            avg_completion_time = (
                total_time_hours / total_tasks if total_tasks > 0 else 0
            )

            # Calculate team performance score
            team_score = (on_time_ratio * 100) * 0.7 + (
                100 - min(late_count / total_tasks * 100, 100)
            ) * 0.3

            return {
                "organization_id": organization_id,
                "period_days": days,
                "total_tasks_completed": total_tasks,
                "on_time_tasks": on_time_count,
                "late_tasks": late_count,
                "on_time_ratio": on_time_ratio,
                "on_time_percentage": on_time_ratio * 100,
                "avg_completion_time": avg_completion_time,
                "team_performance_score": team_score,
            }

        except Exception as exc:
            logger.error(f"Error getting team performance: {str(exc)}")
            return {}

    @staticmethod
    def get_task_distribution_by_skill(organization_id: int) -> Dict[str, int]:
        """
        Get task distribution by skill

        Args:
            organization_id: ID of the organization

        Returns:
            Dictionary with skill distribution
        """
        try:
            tasks = (
                db.session.query(Task)
                .join(Project)
                .filter(Project.organization_id == organization_id)
                .all()
            )

            skill_distribution = {}

            for task in tasks:
                if task.required_skills:
                    for skill in task.required_skills:
                        skill_distribution[skill] = skill_distribution.get(skill, 0) + 1

            # Sort by count
            sorted_distribution = dict(
                sorted(skill_distribution.items(), key=lambda x: x[1], reverse=True)
            )

            return sorted_distribution

        except Exception as exc:
            logger.error(f"Error getting task distribution: {str(exc)}")
            return {}

    @staticmethod
    def get_top_performers(organization_id: int, limit: int = 10) -> List[Dict]:
        """
        Get top performing users

        Args:
            organization_id: ID of the organization
            limit: Maximum number of performers

        Returns:
            List of top performers
        """
        try:
            # Get users in organization
            users = (
                db.session.query(User).filter_by(organization_id=organization_id).all()
            )

            performers = []

            for user in users:
                # Get performance log
                perf_log = (
                    db.session.query(PerformanceLog)
                    .filter_by(user_id=user.id)
                    .order_by(PerformanceLog.created_at.desc())
                    .first()
                )

                # Get completed tasks count
                completed_count = (
                    db.session.query(func.count(TaskAssignment.id))
                    .filter_by(assigned_user_id=user.id, assignment_status="completed")
                    .scalar()
                    or 0
                )

                score = perf_log.performance_score if perf_log else 0

                performers.append(
                    {
                        "user_id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "performance_score": score,
                        "tasks_completed": completed_count,
                        "experience_level": user.experience_level or 0,
                    }
                )

            # Sort by performance score
            performers.sort(key=lambda x: x["performance_score"], reverse=True)

            return performers[:limit]

        except Exception as exc:
            logger.error(f"Error getting top performers: {str(exc)}")
            return []

    @staticmethod
    def get_task_completion_ratio(organization_id: int, days: int = 30) -> Dict:
        """
        Get overdue vs completed task ratio

        Args:
            organization_id: ID of the organization
            days: Number of days to analyze

        Returns:
            Dictionary with completion data
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Get all tasks in period
            all_tasks = (
                db.session.query(Task)
                .join(Project)
                .filter(
                    Project.organization_id == organization_id,
                    Task.created_at >= cutoff_date,
                )
                .all()
            )

            completed = 0
            overdue = 0
            in_progress = 0
            pending = 0

            for task in all_tasks:
                if task.status == "Completed":
                    completed += 1
                elif task.status in ["To Do", "Pending"]:
                    if task.due_date and task.due_date < datetime.utcnow().date():
                        overdue += 1
                    else:
                        pending += 1
                elif task.status == "In Progress":
                    in_progress += 1

            total = len(all_tasks)

            return {
                "organization_id": organization_id,
                "period_days": days,
                "total_tasks": total,
                "completed": completed,
                "overdue": overdue,
                "in_progress": in_progress,
                "pending": pending,
                "completion_ratio": completed / total if total > 0 else 0,
                "completion_percentage": (completed / total * 100) if total > 0 else 0,
                "overdue_percentage": (overdue / total * 100) if total > 0 else 0,
            }

        except Exception as exc:
            logger.error(f"Error getting completion ratio: {str(exc)}")
            return {}

    @staticmethod
    def get_team_performance_trend(
        organization_id: int, days: int = 30, interval: str = "daily"
    ) -> List[Dict]:
        """
        Get team performance trend over time

        Args:
            organization_id: ID of the organization
            days: Number of days to analyze
            interval: 'daily' or 'weekly'

        Returns:
            List of performance data points
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Get performance logs in period
            logs = (
                db.session.query(PerformanceLog)
                .filter(PerformanceLog.created_at >= cutoff_date)
                .all()
            )

            if not logs:
                return []

            # Group by date
            date_groups = {}

            for log in logs:
                if interval == "daily":
                    date_key = log.created_at.date().isoformat()
                else:  # weekly
                    week_start = log.created_at.date() - timedelta(
                        days=log.created_at.weekday()
                    )
                    date_key = week_start.isoformat()

                if date_key not in date_groups:
                    date_groups[date_key] = []

                date_groups[date_key].append(log.performance_score)

            # Calculate averages
            trend_data = []

            for date_key in sorted(date_groups.keys()):
                scores = date_groups[date_key]
                avg_score = sum(scores) / len(scores) if scores else 0

                trend_data.append(
                    {
                        "date": date_key,
                        "average_score": avg_score,
                        "data_points": len(scores),
                        "min_score": min(scores) if scores else 0,
                        "max_score": max(scores) if scores else 0,
                    }
                )

            return trend_data

        except Exception as exc:
            logger.error(f"Error getting performance trend: {str(exc)}")
            return []

    @staticmethod
    def get_project_statistics(organization_id: int) -> List[Dict]:
        """
        Get statistics for each project

        Args:
            organization_id: ID of the organization

        Returns:
            List of project statistics
        """
        try:
            projects = (
                db.session.query(Project)
                .filter_by(organization_id=organization_id)
                .all()
            )

            project_stats = []

            for project in projects:
                # Get tasks
                tasks = db.session.query(Task).filter_by(project_id=project.id).all()

                completed = sum(1 for t in tasks if t.status == "Completed")
                in_progress = sum(1 for t in tasks if t.status == "In Progress")
                pending = sum(1 for t in tasks if t.status in ["To Do", "Pending"])
                overdue = sum(
                    1
                    for t in tasks
                    if t.due_date
                    and t.due_date < datetime.utcnow().date()
                    and t.status != "Completed"
                )

                total = len(tasks)

                project_stats.append(
                    {
                        "project_id": project.id,
                        "project_name": project.title,
                        "total_tasks": total,
                        "completed": completed,
                        "in_progress": in_progress,
                        "pending": pending,
                        "overdue": overdue,
                        "completion_percentage": (
                            (completed / total * 100) if total > 0 else 0
                        ),
                        "status": project.status,
                    }
                )

            return project_stats

        except Exception as exc:
            logger.error(f"Error getting project statistics: {str(exc)}")
            return []

    @staticmethod
    def get_productivity_metrics(organization_id: int, days: int = 30) -> Dict:
        """
        Get productivity metrics

        Args:
            organization_id: ID of the organization
            days: Number of days to analyze

        Returns:
            Dictionary with productivity metrics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Get completed tasks
            completed_tasks = (
                db.session.query(TaskAssignment)
                .join(Task)
                .join(Project)
                .filter(
                    Project.organization_id == organization_id,
                    TaskAssignment.assignment_status == "completed",
                    TaskAssignment.completed_at >= cutoff_date,
                )
                .all()
            )

            # Get total tasks
            total_tasks = (
                db.session.query(Task)
                .join(Project)
                .filter(
                    Project.organization_id == organization_id,
                    Task.created_at >= cutoff_date,
                )
                .count()
            )

            # Get users
            users = (
                db.session.query(User)
                .filter_by(organization_id=organization_id)
                .count()
            )

            # Calculate metrics
            completion_rate = (
                (len(completed_tasks) / total_tasks * 100) if total_tasks > 0 else 0
            )
            tasks_per_user = len(completed_tasks) / users if users > 0 else 0

            # Get average performance score
            perf_logs = (
                db.session.query(PerformanceLog)
                .filter(PerformanceLog.created_at >= cutoff_date)
                .all()
            )

            avg_performance = (
                sum(log.performance_score for log in perf_logs) / len(perf_logs)
                if perf_logs
                else 0
            )

            return {
                "organization_id": organization_id,
                "period_days": days,
                "total_tasks": total_tasks,
                "completed_tasks": len(completed_tasks),
                "completion_rate": completion_rate,
                "total_users": users,
                "tasks_per_user": tasks_per_user,
                "average_performance_score": avg_performance,
                "productivity_index": (completion_rate / 100)
                * (avg_performance / 100)
                * 100,
            }

        except Exception as exc:
            logger.error(f"Error getting productivity metrics: {str(exc)}")
            return {}

    @staticmethod
    def get_skill_proficiency_distribution(organization_id: int) -> Dict[str, Dict]:
        """
        Get skill proficiency distribution across team

        Args:
            organization_id: ID of the organization

        Returns:
            Dictionary with skill distributions
        """
        try:
            users = (
                db.session.query(User).filter_by(organization_id=organization_id).all()
            )

            skill_distribution = {}

            for user in users:
                profile = UserSkillProfile.query.filter_by(user_id=user.id).first()

                if profile and profile.skills:
                    for skill, proficiency in profile.skills.items():
                        if skill not in skill_distribution:
                            skill_distribution[skill] = {
                                "skill": skill,
                                "users_with_skill": 0,
                                "total_proficiency": 0,
                                "avg_proficiency": 0,
                                "max_proficiency": 0,
                                "min_proficiency": 100,
                            }

                        skill_distribution[skill]["users_with_skill"] += 1
                        skill_distribution[skill]["total_proficiency"] += proficiency
                        skill_distribution[skill]["max_proficiency"] = max(
                            skill_distribution[skill]["max_proficiency"], proficiency
                        )
                        skill_distribution[skill]["min_proficiency"] = min(
                            skill_distribution[skill]["min_proficiency"], proficiency
                        )

            # Calculate averages
            for skill in skill_distribution:
                users_count = skill_distribution[skill]["users_with_skill"]
                skill_distribution[skill]["avg_proficiency"] = (
                    skill_distribution[skill]["total_proficiency"] / users_count
                    if users_count > 0
                    else 0
                )

            return skill_distribution

        except Exception as exc:
            logger.error(f"Error getting skill distribution: {str(exc)}")
            return {}

    @staticmethod
    def get_comprehensive_analytics(organization_id: int, days: int = 30) -> Dict:
        """
        Get comprehensive analytics dashboard data

        Args:
            organization_id: ID of the organization
            days: Number of days to analyze

        Returns:
            Dictionary with all analytics
        """
        try:
            return {
                "organization_id": organization_id,
                "period_days": days,
                "generated_at": datetime.utcnow().isoformat(),
                "team_performance": AnalyticsEngine.get_team_performance_summary(
                    organization_id, days
                ),
                "task_completion": AnalyticsEngine.get_task_completion_ratio(
                    organization_id, days
                ),
                "productivity": AnalyticsEngine.get_productivity_metrics(
                    organization_id, days
                ),
                "top_performers": AnalyticsEngine.get_top_performers(
                    organization_id, limit=5
                ),
                "task_distribution": AnalyticsEngine.get_task_distribution_by_skill(
                    organization_id
                ),
                "performance_trend": AnalyticsEngine.get_team_performance_trend(
                    organization_id, days
                ),
                "projects": AnalyticsEngine.get_project_statistics(organization_id),
                "skill_distribution": AnalyticsEngine.get_skill_proficiency_distribution(
                    organization_id
                ),
            }

        except Exception as exc:
            logger.error(f"Error getting comprehensive analytics: {str(exc)}")
            return {}
