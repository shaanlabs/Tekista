"""
Integration API Routes
Connects all systems together
"""

import logging

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from integration import DashboardDataProvider, TaskWorkflow

logger = logging.getLogger(__name__)

integration_bp = Blueprint("integration", __name__, url_prefix="/api/integration")

# ============================================================================
# TASK WORKFLOW ENDPOINTS
# ============================================================================


@integration_bp.route("/tasks/create-and-assign", methods=["POST"])
@login_required
def create_and_assign_task():
    """
    Create a task and auto-assign it

    Request Body:
        title: str
        description: str
        project_id: int
        required_skills: list
        difficulty: int (1-10)
        priority: str (low, medium, high)
        due_date: str (ISO format, optional)
    """
    data = request.get_json()

    required_fields = ["title", "description", "project_id", "required_skills"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    result = TaskWorkflow.create_and_assign_task(
        title=data["title"],
        description=data["description"],
        project_id=data["project_id"],
        required_skills=data["required_skills"],
        difficulty=data.get("difficulty", 5),
        priority=data.get("priority", "medium"),
        due_date=data.get("due_date"),
        created_by_id=current_user.id,
    )

    if result["success"]:
        return jsonify(result), 201
    else:
        return jsonify(result), 500


@integration_bp.route("/tasks/<int:task_id>/complete", methods=["POST"])
@login_required
def complete_task(task_id):
    """
    Mark task as complete and trigger next assignment

    Request Body:
        notes: str (optional)
    """
    data = request.get_json() or {}

    result = TaskWorkflow.complete_task(
        task_id=task_id, user_id=current_user.id, notes=data.get("notes")
    )

    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 500


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================


@integration_bp.route("/dashboard/user", methods=["GET"])
@login_required
def get_user_dashboard():
    """Get user dashboard data"""
    data = DashboardDataProvider.get_user_dashboard_data(current_user.id)

    if "error" in data:
        return jsonify(data), 500

    return jsonify(data), 200


@integration_bp.route("/dashboard/team", methods=["GET"])
@login_required
def get_team_dashboard():
    """Get team dashboard data"""
    data = DashboardDataProvider.get_team_dashboard_data(current_user.organization_id)

    if "error" in data:
        return jsonify(data), 500

    return jsonify(data), 200


# ============================================================================
# TEST ENDPOINTS
# ============================================================================


@integration_bp.route("/test/create-sample-data", methods=["POST"])
@login_required
def create_sample_data():
    """Create sample data for testing"""
    try:
        from models import Project, db

        # Create sample project
        project = Project(
            title="Sample Project",
            description="Sample project for testing",
            organization_id=current_user.organization_id,
            status="Active",
        )
        db.session.add(project)
        db.session.commit()

        # Create sample tasks
        sample_tasks = [
            {
                "title": "Build User Authentication",
                "description": "Implement user login and registration",
                "required_skills": ["Python", "Django", "Security"],
                "difficulty": 7,
                "priority": "high",
            },
            {
                "title": "Design Dashboard UI",
                "description": "Create responsive dashboard interface",
                "required_skills": ["React", "CSS", "UI Design"],
                "difficulty": 6,
                "priority": "high",
            },
            {
                "title": "Setup Database Schema",
                "description": "Design and implement database tables",
                "required_skills": ["SQL", "Database Design", "PostgreSQL"],
                "difficulty": 5,
                "priority": "medium",
            },
            {
                "title": "API Documentation",
                "description": "Write comprehensive API documentation",
                "required_skills": ["Technical Writing", "API Design"],
                "difficulty": 3,
                "priority": "low",
            },
            {
                "title": "Performance Optimization",
                "description": "Optimize database queries and caching",
                "required_skills": ["Python", "Database", "Performance Tuning"],
                "difficulty": 8,
                "priority": "medium",
            },
        ]

        created_tasks = []
        for task_data in sample_tasks:
            result = TaskWorkflow.create_and_assign_task(
                title=task_data["title"],
                description=task_data["description"],
                project_id=project.id,
                required_skills=task_data["required_skills"],
                difficulty=task_data["difficulty"],
                priority=task_data["priority"],
                created_by_id=current_user.id,
            )
            created_tasks.append(result)

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Created {len(created_tasks)} sample tasks",
                    "project_id": project.id,
                    "tasks": created_tasks,
                }
            ),
            201,
        )

    except Exception as exc:
        logger.error(f"Error creating sample data: {str(exc)}")
        return jsonify({"error": str(exc)}), 500


@integration_bp.route("/test/complete-random-task", methods=["POST"])
@login_required
def complete_random_task():
    """Complete a random assigned task for testing"""
    try:
        from assignment.models import TaskAssignment

        # Get a random assigned task
        assignment = TaskAssignment.query.filter_by(
            assigned_user_id=current_user.id, assignment_status="assigned"
        ).first()

        if not assignment:
            return jsonify({"error": "No assigned tasks found"}), 404

        result = TaskWorkflow.complete_task(
            task_id=assignment.task_id, user_id=current_user.id, notes="Test completion"
        )

        return jsonify(result), 200

    except Exception as exc:
        logger.error(f"Error completing task: {str(exc)}")
        return jsonify({"error": str(exc)}), 500


@integration_bp.route("/test/workflow", methods=["GET"])
@login_required
def test_workflow():
    """Test the entire workflow"""
    try:
        from models import Project, db

        # 1. Create project
        project = Project(
            title="Workflow Test Project",
            description="Testing the complete workflow",
            organization_id=current_user.organization_id,
            status="Active",
        )
        db.session.add(project)
        db.session.commit()

        # 2. Create and assign task
        task_result = TaskWorkflow.create_and_assign_task(
            title="Test Task",
            description="This is a test task",
            project_id=project.id,
            required_skills=["Python", "Testing"],
            difficulty=5,
            priority="medium",
            created_by_id=current_user.id,
        )

        if not task_result["success"]:
            return jsonify({"error": "Failed to create task"}), 500

        task_id = task_result["task_id"]

        # 3. Get dashboard data
        dashboard_data = DashboardDataProvider.get_user_dashboard_data(current_user.id)

        return (
            jsonify(
                {
                    "success": True,
                    "workflow_test": {
                        "project_created": project.id,
                        "task_created": task_id,
                        "task_assigned": task_result["assignment"]["assigned_to"],
                        "dashboard_data": dashboard_data,
                    },
                }
            ),
            200,
        )

    except Exception as exc:
        logger.error(f"Error in workflow test: {str(exc)}")
        return jsonify({"error": str(exc)}), 500
