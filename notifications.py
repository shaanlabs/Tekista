from flask import current_app
from flask_mail import Message

from app import mail


def send_email(subject, recipients, body):
    """Send an email if mail is configured. Recipients is a list."""
    if not recipients:
        return
    try:
        msg = Message(
            subject=subject,
            recipients=recipients,
            body=body,
            sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
        )
        mail.send(msg)
    except Exception:
        # fail silently (or log) if mail not configured or send fails
        current_app.logger.debug(
            "Email send failed or mail not configured.", exc_info=True
        )


def notify_task_assigned(task):
    """Notify assignees that a task was assigned."""
    subject = f"Assigned to task: {task.title}"
    body = f"You have been assigned to task '{task.title}' in project '{task.project.title}'. Due: {task.due_date}\n\nLink: {current_app.config.get('APP_BASE_URL','/')}tasks/{task.id}"
    recipients = [u.email for u in task.assignees if u.email]
    send_email(subject, recipients, body)


def notify_task_status_change(task, old_status, new_status):
    """Notify assignees about status change."""
    subject = f"Task status updated: {task.title}"
    body = f"Task '{task.title}' changed from {old_status} to {new_status}.\nProject: {task.project.title}\n\nLink: {current_app.config.get('APP_BASE_URL','/')}tasks/{task.id}"
    recipients = [u.email for u in task.assignees if u.email]
    send_email(subject, recipients, body)
