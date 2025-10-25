"""
AI Recommendation System
Suggests suitable tasks for users based on skills, history, and success rates
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from assignment.models import TaskAssignment, UserSkillProfile
from models import Project, Task, User

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Engine for generating task recommendations"""

    @staticmethod
    def calculate_skill_overlap(user_id: int, task_id: int) -> float:
        """
        Calculate skill overlap between user and task

        Args:
            user_id: ID of the user
            task_id: ID of the task

        Returns:
            Float between 0 and 1 representing skill match
        """
        try:
            user_profile = UserSkillProfile.query.filter_by(user_id=user_id).first()
            task = Task.query.get(task_id)

            if not user_profile or not task:
                return 0.0

            user_skills = set(skill.lower() for skill in (user_profile.skills or []))
            required_skills = set(
                skill.lower() for skill in (task.required_skills or [])
            )

            if not required_skills:
                return 0.5  # Default if no skills required

            if not user_skills:
                return 0.0  # User has no skills

            # Calculate intersection
            matched_skills = user_skills.intersection(required_skills)
            skill_overlap = len(matched_skills) / len(required_skills)

            return skill_overlap

        except Exception as exc:
            logger.error("Error calculating skill overlap: %s", exc)
            return 0.0

    @staticmethod
    def calculate_completion_time_similarity(user_id: int, task_id: int) -> float:
        """
        Calculate how well task difficulty matches user's completion speed

        Args:
            user_id: ID of the user
            task_id: ID of the task

        Returns:
            Float between 0 and 1 representing time match
        """
        try:
            user_profile = UserSkillProfile.query.filter_by(user_id=user_id).first()
            task = Task.query.get(task_id)

            if not user_profile or not task:
                return 0.5

            # Get user's average completion time
            user_avg_time = user_profile.avg_completion_time or 8.0

            # Estimate task time based on difficulty
            # Assume 1 hour per difficulty level as baseline
            estimated_task_time = task.difficulty or 5

            # Calculate ratio
            time_ratio = (
                estimated_task_time / user_avg_time if user_avg_time > 0 else 1.0
            )

            # Penalize if ratio is too extreme (too easy or too hard)
            # Optimal ratio is around 1.0
            if time_ratio < 0.5:
                # Task too easy
                similarity = 0.7 + (time_ratio * 0.3)
            elif time_ratio > 2.0:
                # Task too hard
                similarity = 0.5 - ((time_ratio - 2.0) * 0.1)
            else:
                # Good match
                similarity = 1.0 - abs(1.0 - time_ratio) * 0.2

            return max(0.0, min(1.0, similarity))

        except Exception as exc:
            logger.error("Error calculating completion time similarity: %s", exc)
            return 0.5

    @staticmethod
    def calculate_success_rate_on_similar_tasks(user_id: int, task_id: int) -> float:
        """
        Calculate user's success rate on similar tasks

        Args:
            user_id: ID of the user
            task_id: ID of the task

        Returns:
            Float between 0 and 1 representing success rate
        """
        try:
            task = Task.query.get(task_id)
            if not task:
                return 0.5

            # Find similar tasks (same project or similar difficulty)
            similar_tasks = Task.query.filter(
                Task.id != task_id,
                Task.project_id == task.project_id,
                Task.difficulty.between(
                    (task.difficulty or 5) - 2, (task.difficulty or 5) + 2
                ),
            ).all()

            if not similar_tasks:
                # No similar tasks, use general success rate
                assignments = TaskAssignment.query.filter_by(
                    assigned_user_id=user_id, assignment_status="completed"
                ).all()

                if not assignments:
                    return 0.5

                on_time_count = sum(
                    1
                    for a in assignments
                    if a.completed_at
                    and a.task.due_date
                    and a.completed_at <= a.task.due_date
                )

                return on_time_count / len(assignments) if assignments else 0.5

            # Calculate success rate on similar tasks
            successful_count = 0
            total_count = 0

            for similar_task in similar_tasks:
                assignment = TaskAssignment.query.filter_by(
                    assigned_user_id=user_id,
                    task_id=similar_task.id,
                    assignment_status="completed",
                ).first()

                if assignment:
                    total_count += 1
                    if assignment.completed_at and similar_task.due_date:
                        if assignment.completed_at <= similar_task.due_date:
                            successful_count += 1

            if total_count == 0:
                return 0.5

            return successful_count / total_count

        except Exception as exc:
            logger.error("Error calculating success rate: %s", exc)
            return 0.5

    @staticmethod
    def calculate_workload_fit(user_id: int, task_id: int) -> float:
        """
        Calculate how well task fits user's current workload

        Args:
            user_id: ID of the user
            task_id: ID of the task

        Returns:
            Float between 0 and 1 representing workload fit
        """
        try:
            user_profile = UserSkillProfile.query.filter_by(user_id=user_id).first()
            task = Task.query.get(task_id)

            if not user_profile or not task:
                return 0.5

            # Check if user is overloaded
            if user_profile.is_overloaded():
                return 0.0  # Don't recommend if overloaded

            # Calculate available capacity
            available_capacity = user_profile.available_capacity()
            estimated_task_time = task.difficulty or 5

            # If task fits in available capacity
            if estimated_task_time <= available_capacity:
                # Prefer tasks that use 50-80% of available capacity
                utilization = estimated_task_time / available_capacity
                if 0.5 <= utilization <= 0.8:
                    return 1.0
                elif utilization < 0.5:
                    return 0.7  # Task is small
                else:
                    return 0.9  # Task uses most capacity
            else:
                return 0.0  # Task doesn't fit

        except Exception as exc:
            logger.error("Error calculating workload fit: %s", exc)
            return 0.5

    @staticmethod
    def calculate_experience_match(user_id: int, task_id: int) -> float:
        """
        Calculate how well task difficulty matches user experience

        Args:
            user_id: ID of the user
            task_id: ID of the task

        Returns:
            Float between 0 and 1 representing experience match
        """
        try:
            user_profile = UserSkillProfile.query.filter_by(user_id=user_id).first()
            task = Task.query.get(task_id)

            if not user_profile or not task:
                return 0.5

            user_exp = user_profile.experience_level or 5
            task_diff = task.difficulty or 5

            # Normalize both to 1-10 scale
            exp_ratio = task_diff / user_exp

            # Optimal ratio is around 1.0 (task difficulty matches experience)
            if exp_ratio < 0.5:
                # Task too easy
                match = 0.6 + (exp_ratio * 0.4)
            elif exp_ratio > 1.5:
                # Task too hard
                match = 1.0 - ((exp_ratio - 1.5) * 0.2)
            else:
                # Good match
                match = 1.0 - abs(1.0 - exp_ratio) * 0.1

            return max(0.0, min(1.0, match))

        except Exception as exc:
            logger.error("Error calculating experience match: %s", exc)
            return 0.5

    @staticmethod
    def calculate_priority_boost(task_id: int) -> float:
        """
        Calculate priority boost for task

        Args:
            task_id: ID of the task

        Returns:
            Float representing priority boost (0.5-1.5)
        """
        try:
            task = Task.query.get(task_id)
            if not task:
                return 1.0

            # Boost based on priority
            priority_boost = {"low": 0.8, "medium": 1.0, "high": 1.3}

            boost = (
                priority_boost.get(task.priority.lower(), 1.0) if task.priority else 1.0
            )

            # Additional boost if task is overdue
            if task.due_date and task.due_date < datetime.utcnow().date():
                boost *= 1.2

            return min(boost, 1.5)  # Cap at 1.5

        except Exception as exc:
            logger.error("Error calculating priority boost: %s", exc)
            return 1.0

    @staticmethod
    def calculate_recommendation_score(
        user_id: int, task_id: int, weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate overall recommendation score for a task

        Args:
            user_id: ID of the user
            task_id: ID of the task
            weights: Custom weights for scoring components

        Returns:
            Float between 0 and 100 representing recommendation score
        """
        try:
            # Default weights
            if weights is None:
                weights = {
                    "skill_overlap": 0.30,
                    "completion_time": 0.20,
                    "success_rate": 0.20,
                    "workload_fit": 0.15,
                    "experience_match": 0.15,
                }

            # Calculate components
            skill_overlap = RecommendationEngine.calculate_skill_overlap(
                user_id, task_id
            )
            completion_time = RecommendationEngine.calculate_completion_time_similarity(
                user_id, task_id
            )
            success_rate = RecommendationEngine.calculate_success_rate_on_similar_tasks(
                user_id, task_id
            )
            workload_fit = RecommendationEngine.calculate_workload_fit(user_id, task_id)
            experience_match = RecommendationEngine.calculate_experience_match(
                user_id, task_id
            )

            # Calculate weighted score
            score = (
                skill_overlap * weights["skill_overlap"]
                + completion_time * weights["completion_time"]
                + success_rate * weights["success_rate"]
                + workload_fit * weights["workload_fit"]
                + experience_match * weights["experience_match"]
            )

            # Apply priority boost
            priority_boost = RecommendationEngine.calculate_priority_boost(task_id)
            score *= priority_boost

            return max(0, min(100, score * 100))

        except Exception as exc:
            logger.error("Error calculating recommendation score: %s", exc)
            return 0.0

    @staticmethod
    def recommend_tasks_for_user(
        user_id: int, top_n: int = 3, organization_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Get top N recommended tasks for a user

        Args:
            user_id: ID of the user
            top_n: Number of recommendations to return
            organization_id: Filter by organization (optional)

        Returns:
            List of recommended tasks with scores
        """
        try:
            user = User.query.get(user_id)
            if not user:
                logger.error("User %s not found", user_id)
                return []

            # Get available tasks (not completed, not assigned)
            query = Task.query.filter(
                Task.status.in_(["To Do", "Pending"]),
                ~Task.assignees.any(User.id == user_id),
            )

            # Filter by organization if provided
            if organization_id:
                query = query.join(Project).filter(
                    Project.organization_id == organization_id
                )

            available_tasks = query.all()

            if not available_tasks:
                logger.info("No available tasks for user %s", user_id)
                return []

            # Calculate scores for each task
            task_scores = []

            for task in available_tasks:
                score = RecommendationEngine.calculate_recommendation_score(
                    user_id, task.id
                )

                if score > 0:  # Only include tasks with positive score
                    task_scores.append(
                        {
                            "task_id": task.id,
                            "task_title": task.title,
                            "task_description": task.description,
                            "project_id": task.project_id,
                            "project_name": (
                                task.project.title if task.project else None
                            ),
                            "difficulty": task.difficulty,
                            "priority": task.priority,
                            "due_date": (
                                task.due_date.isoformat() if task.due_date else None
                            ),
                            "required_skills": task.required_skills or [],
                            "recommendation_score": score,
                            "components": {
                                "skill_overlap": RecommendationEngine.calculate_skill_overlap(
                                    user_id, task.id
                                ),
                                "completion_time_fit": RecommendationEngine.calculate_completion_time_similarity(
                                    user_id, task.id
                                ),
                                "success_rate": RecommendationEngine.calculate_success_rate_on_similar_tasks(
                                    user_id, task.id
                                ),
                                "workload_fit": RecommendationEngine.calculate_workload_fit(
                                    user_id, task.id
                                ),
                                "experience_match": RecommendationEngine.calculate_experience_match(
                                    user_id, task.id
                                ),
                            },
                        }
                    )

            # Sort by score (highest first)
            task_scores.sort(key=lambda x: x["recommendation_score"], reverse=True)

            logger.info(
                "Generated %s recommendations for user %s", len(task_scores), user_id
            )

            return task_scores[:top_n]

        except Exception as exc:
            logger.error(
                "Error generating recommendations for user %s: %s", user_id, exc
            )
            return []

    @staticmethod
    def get_personalized_recommendations(
        user_id: int, top_n: int = 5, organization_id: Optional[int] = None
    ) -> Dict:
        """
        Get personalized recommendations with explanations

        Args:
            user_id: ID of the user
            top_n: Number of recommendations
            organization_id: Filter by organization

        Returns:
            Dictionary with recommendations and insights
        """
        try:
            recommendations = RecommendationEngine.recommend_tasks_for_user(
                user_id, top_n, organization_id
            )

            user_profile = UserSkillProfile.query.filter_by(user_id=user_id).first()

            # Generate insights
            insights = []

            if user_profile:
                if user_profile.is_overloaded():
                    insights.append(
                        "You're currently overloaded. Consider completing some tasks first."
                    )

                if user_profile.performance_score < 60:
                    insights.append(
                        "Your performance score is below average. Try tasks with lower difficulty."
                    )
                elif user_profile.performance_score > 85:
                    insights.append(
                        "Great performance! You can handle more challenging tasks."
                    )

                available_capacity = user_profile.available_capacity()
                if available_capacity < 5:
                    insights.append(
                        "You have limited capacity. Focus on high-priority tasks."
                    )

            return {
                "user_id": user_id,
                "recommendations": recommendations,
                "insights": insights,
                "total_recommendations": len(recommendations),
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as exc:
            logger.error("Error getting personalized recommendations: %s", exc)
            return {
                "user_id": user_id,
                "recommendations": [],
                "insights": [],
                "error": str(exc),
            }
