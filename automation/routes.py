"""
Automation Routes and Endpoints
Provides API endpoints for task automation and performance tracking
"""

import logging

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from automation import (PerformanceCalculator, TaskAutomationEngine,
                        WorkloadBalancer)
from models import AuditLog, Task, db

logger = logging.getLogger(__name__)

automation_bp = Blueprint("automation", __name__, url_prefix="/automation")

# ============================================================================
# TASK COMPLETION ENDPOINTS
# ============================================================================


@automation_bp.route("/tasks/<int:task_id>/complete", methods=["POST"])
@login_required
def complete_task(task_id):
    """
    Mark task as completed and trigger automation

    Args:
        task_id: ID of the task to complete
    """
    task = db.session.get(Task, task_id) or abort(404)

    # Check authorization
    if task.assignees and current_user not in task.assignees:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json() or {}
    actual_hours = data.get("actual_hours")
    notes = data.get("notes")

    try:
        # Update task status
        old_status = task.status
        task.status = "Completed"

        if notes:
            task.notes = notes

        db.session.commit()

        # Trigger automation
        automation_result = TaskAutomationEngine.on_task_completed(
            task_id=task_id, actual_hours=actual_hours
        )

        # Audit log
        try:
            db.session.add(
                AuditLog(
                    actor_id=current_user.id,
                    action="complete",
                    target_type="task",
                    target_id=task_id,
                    meta=f"old={old_status}, new=Completed, actual_hours={actual_hours}",
                )
            )
            db.session.commit()
        except Exception:
            db.session.rollback()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Task completed",
                    "automation": automation_result,
                }
            ),
            200,
        )

    except Exception as exc:
        logger.error(f"Error completing task {task_id}: {str(exc)}")
        return jsonify({"error": str(exc)}), 500


@automation_bp.route("/tasks/<int:task_id>/status", methods=["PUT"])
@login_required
def update_task_status(task_id):
    """
    Update task status and trigger automation if completed
    """
    task = db.session.get(Task, task_id) or abort(404)

    data = request.get_json()
    new_status = data.get("status")

    if not new_status:
        return jsonify({"error": "Status is required"}), 400

    # Admin/Manager role check for status updates
    role_name = getattr(getattr(current_user, "role", None), "name", None)
    if role_name not in ("Admin", "Manager") and current_user not in task.assignees:
        return jsonify({"error": "forbidden"}), 403

    try:
        old_status = task.status
        # Normalize statuses
        if new_status.lower() in ("done", "completed"):
            new_status = "Completed"
        elif new_status.lower() in ("in progress", "in_progress"):
            new_status = "In Progress"
        task.status = new_status
        db.session.commit()

        # Trigger automation if task is completed
        automation_result = None
        if new_status == "Completed":
            automation_result = TaskAutomationEngine.on_task_status_changed(
                task_id=task_id, old_status=old_status, new_status=new_status
            )

        # Audit log
        try:
            db.session.add(
                AuditLog(
                    actor_id=current_user.id,
                    action="update",
                    target_type="task",
                    target_id=task_id,
                    meta=f"{old_status}->{new_status}",
                )
            )
            db.session.commit()
        except Exception:
            db.session.rollback()

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Task status updated to {new_status}",
                    "automation": automation_result,
                }
            ),
            200,
        )

    except Exception as exc:
        logger.error(f"Error updating task status: {str(exc)}")
        return jsonify({"error": str(exc)}), 500


# ============================================================================
# PERFORMANCE TRACKING ENDPOINTS
# ============================================================================


@automation_bp.route("/performance/user/<int:user_id>", methods=["GET"])
@login_required
def get_user_performance(user_id):
    """Get performance metrics for a user"""
    # Check authorization
    if user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    performance = PerformanceCalculator.calculate_performance_score(user_id)

    if "error" in performance:
        return jsonify(performance), 404

    return jsonify(performance), 200


@automation_bp.route("/performance/team", methods=["GET"])
@login_required
def get_team_performance():
    """Get performance metrics for entire team"""
    # Only Admin/Manager can access team performance
    role_name = getattr(getattr(current_user, "role", None), "name", None)
    if role_name not in ("Admin", "Manager"):
        return jsonify({"error": "forbidden"}), 403

    team_performance = PerformanceCalculator.calculate_team_performance(
        getattr(current_user, "organization_id", None)
    )

    return (
        jsonify(
            {
                "organization_id": current_user.organization_id,
                "team_members": team_performance,
                "average_performance": (
                    sum(p.get("performance_score", 0) for p in team_performance)
                    / len(team_performance)
                    if team_performance
                    else 0
                ),
            }
        ),
        200,
    )


@automation_bp.route("/performance/high-performers", methods=["GET"])
@login_required
def get_high_performers():
    """Get list of high-performing team members"""
    threshold = request.args.get("threshold", 80, type=int)

    # Only Admin/Manager
    role_name = getattr(getattr(current_user, "role", None), "name", None)
    if role_name not in ("Admin", "Manager"):
        return jsonify({"error": "forbidden"}), 403

    high_performers = PerformanceCalculator.identify_high_performers(
        getattr(current_user, "organization_id", None), threshold
    )

    return (
        jsonify(
            {
                "threshold": threshold,
                "high_performers": high_performers,
                "count": len(high_performers),
            }
        ),
        200,
    )


@automation_bp.route("/performance/at-risk", methods=["GET"])
@login_required
def get_at_risk_performers():
    """Get list of performers who need support"""
    threshold = request.args.get("threshold", 50, type=int)

    role_name = getattr(getattr(current_user, "role", None), "name", None)
    if role_name not in ("Admin", "Manager"):
        return jsonify({"error": "forbidden"}), 403
    at_risk = PerformanceCalculator.identify_at_risk_performers(
        getattr(current_user, "organization_id", None), threshold
    )

    return (
        jsonify(
            {
                "threshold": threshold,
                "at_risk_performers": at_risk,
                "count": len(at_risk),
            }
        ),
        200,
    )


# ============================================================================
# WORKLOAD MANAGEMENT ENDPOINTS
# ============================================================================


@automation_bp.route("/workload/user/<int:user_id>/capacity", methods=["GET"])
@login_required
def get_user_capacity(user_id):
    """Get available capacity for a user"""
    if user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    available_capacity = WorkloadBalancer.get_user_available_capacity(user_id)
    is_overloaded = WorkloadBalancer.is_user_overloaded(user_id)

    return (
        jsonify(
            {
                "user_id": user_id,
                "available_capacity_hours": available_capacity,
                "is_overloaded": is_overloaded,
            }
        ),
        200,
    )


@automation_bp.route("/workload/team/rebalance-suggestions", methods=["GET"])
@login_required
def get_rebalance_suggestions():
    """Get workload rebalancing suggestions for team"""
    role_name = getattr(getattr(current_user, "role", None), "name", None)
    if role_name not in ("Admin", "Manager"):
        return jsonify({"error": "forbidden"}), 403
    suggestions = WorkloadBalancer.suggest_workload_rebalancing(
        getattr(current_user, "organization_id", None)
    )

    return jsonify(suggestions), 200


@automation_bp.route("/workload/team/status", methods=["GET"])
@login_required
def get_team_workload_status():
    """Get overall team workload status"""
    from models import User

    try:
        from assignment.models import UserSkillProfile
        from enterprise.models import UserOrganizationRole
    except Exception:
        return jsonify({"error": "enterprise modules unavailable"}), 501

    users = (
        User.query.join(UserOrganizationRole, User.id == UserOrganizationRole.user_id)
        .filter(UserOrganizationRole.organization_id == current_user.organization_id)
        .all()
    )

    total_capacity = 0
    total_utilized = 0
    overloaded_count = 0

    for user in users:
        profile = UserSkillProfile.query.filter_by(user_id=user.id).first()
        if profile:
            total_capacity += profile.max_weekly_hours
            total_utilized += profile.current_workload_hours
            if profile.is_overloaded():
                overloaded_count += 1

    utilization_rate = (
        (total_utilized / total_capacity * 100) if total_capacity > 0 else 0
    )

    return (
        jsonify(
            {
                "total_team_members": len(users),
                "total_capacity_hours": total_capacity,
                "total_utilized_hours": total_utilized,
                "utilization_rate": utilization_rate,
                "overloaded_members": overloaded_count,
                "available_capacity": total_capacity - total_utilized,
            }
        ),
        200,
    )


# ============================================================================
# AUTOMATION STATUS ENDPOINTS
# ============================================================================


@automation_bp.route("/jobs/<job_id>/status", methods=["GET"])
@login_required
def get_job_status(job_id):
    """Get status of a background job"""
    try:
        from celery_app import celery_app

        task = celery_app.AsyncResult(job_id)

        return (
            jsonify(
                {
                    "job_id": job_id,
                    "status": task.status,
                    "result": task.result if task.status == "SUCCESS" else None,
                    "error": str(task.info) if task.status == "FAILURE" else None,
                }
            ),
            200,
        )

    except Exception as exc:
        logger.error(f"Error getting job status: {str(exc)}")
        return jsonify({"error": str(exc)}), 500


@automation_bp.route("/automation-log", methods=["GET"])
@login_required
def get_automation_log():
    """Get automation activity log"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    # Only Admin/Manager can view audit logs
    role_name = getattr(getattr(current_user, "role", None), "name", None)
    if role_name not in ("Admin", "Manager"):
        return jsonify({"error": "forbidden"}), 403

    logs = (
        AuditLog.query.filter(
            AuditLog.organization_id == getattr(current_user, "organization_id", None),
            AuditLog.action.in_(["complete", "assign", "update"]),
        )
        .order_by(AuditLog.created_at.desc())
        .paginate(page=page, per_page=per_page)
    )

    return (
        jsonify(
            {
                "total": logs.total,
                "pages": logs.pages,
                "current_page": page,
                "logs": [
                    {
                        "id": log.id,
                        "user": log.user.username if log.user else "System",
                        "action": log.action,
                        "resource_type": log.resource_type,
                        "resource_id": log.resource_id,
                        "status": log.status,
                        "created_at": log.created_at.isoformat(),
                    }
                    for log in logs.items
                ],
            }
        ),
        200,
    )
