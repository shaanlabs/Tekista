#!/usr/bin/env python3
"""
Database initialization script for TaskManager
Run this script to create the database tables and optionally create a sample user.
"""

from datetime import datetime, timedelta

from app import create_app
from models import Project, Task, User, db


def init_database():
    """Initialize the database with tables"""
    app = create_app()

    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

        # Check if we already have users
        if User.query.first() is None:
            print("Creating sample data...")

            # Create sample users
            admin = User(username="admin", email="admin@taskmanager.com")
            admin.set_password("admin123")

            user1 = User(username="john_doe", email="john@example.com")
            user1.set_password("password123")

            user2 = User(username="jane_smith", email="jane@example.com")
            user2.set_password("password123")

            db.session.add_all([admin, user1, user2])
            db.session.commit()

            # Create sample project
            project = Project(
                title="Website Redesign",
                description="Complete redesign of the company website with modern UI/UX",
                deadline=datetime.now().date() + timedelta(days=30),
            )
            project.users.extend([admin, user1, user2])

            db.session.add(project)
            db.session.commit()

            # Create sample tasks
            task1 = Task(
                title="Design Mockups",
                description="Create wireframes and mockups for the new website",
                due_date=datetime.now().date() + timedelta(days=7),
                priority="High",
                status="In Progress",
                project=project,
            )
            task1.assignees.extend([user1, user2])

            task2 = Task(
                title="Frontend Development",
                description="Implement the frontend using React and modern CSS",
                due_date=datetime.now().date() + timedelta(days=21),
                priority="High",
                status="To Do",
                project=project,
            )
            task2.assignees.append(user1)
            task2.predecessors.append(task1)

            task3 = Task(
                title="Backend API",
                description="Develop REST API endpoints for the website",
                due_date=datetime.now().date() + timedelta(days=14),
                priority="Normal",
                status="To Do",
                project=project,
            )
            task3.assignees.append(user2)

            db.session.add_all([task1, task2, task3])
            db.session.commit()

            print("Sample data created successfully!")
            print("\nSample Users Created:")
            print("  - admin / admin123 (admin@taskmanager.com)")
            print("  - john_doe / password123 (john@example.com)")
            print("  - jane_smith / password123 (jane@example.com)")
            print("\nSample Project: 'Website Redesign' with 3 tasks")
        else:
            print("Database already contains data, skipping sample data creation.")

        print("\nDatabase initialization complete!")
        print("You can now run the application with: flask run")


if __name__ == "__main__":
    init_database()
