// TaskManager - Dashboard Data Population

// Sample data for demonstration
const dashboardData = {
    stats: {
        projects: 3,
        tasks: 12,
        completed: 8,
        overdue: 1
    },
    activities: [
        {
            type: 'created',
            text: 'New project "Website Redesign" created',
            time: '2 hours ago'
        },
        {
            type: 'updated',
            text: 'Task "Design Mockups" updated',
            time: '4 hours ago'
        },
        {
            type: 'completed',
            text: 'Task "Research Phase" completed',
            time: '1 day ago'
        },
        {
            type: 'created',
            text: 'New task "API Development" created',
            time: '2 days ago'
        }
    ],
    projects: [
        {
            id: 1,
            title: 'Website Redesign',
            description: 'Complete redesign of the company website with modern UI/UX',
            progress: 65,
            deadline: '2024-02-15',
            status: 'active',
            tasks: 8,
            completed: 5
        },
        {
            id: 2,
            title: 'Mobile App Development',
            description: 'Development of a mobile application for iOS and Android',
            progress: 30,
            deadline: '2024-03-20',
            status: 'active',
            tasks: 12,
            completed: 3
        },
        {
            id: 3,
            title: 'Database Migration',
            description: 'Migrate legacy database to new cloud infrastructure',
            progress: 90,
            deadline: '2024-01-30',
            status: 'active',
            tasks: 5,
            completed: 4
        }
    ]
};

// Populate dashboard with data
function populateDashboard() {
    populateStats();
    populateActivities();
    populateProjects();
}

function populateStats() {
    const stats = dashboardData.stats;
    
    // Animate numbers
    animateNumber(document.querySelector('[data-stat="projects"]'), stats.projects);
    animateNumber(document.querySelector('[data-stat="tasks"]'), stats.tasks);
    animateNumber(document.querySelector('[data-stat="completed"]'), stats.completed);
    animateNumber(document.querySelector('[data-stat="overdue"]'), stats.overdue);
}

function populateActivities() {
    const activityList = document.querySelector('.activity-list');
    if (!activityList) return;
    
    // Clear existing activities
    activityList.innerHTML = '';
    
    dashboardData.activities.forEach((activity, index) => {
        const activityItem = createActivityItem(activity, index);
        activityList.appendChild(activityItem);
    });
}

function createActivityItem(activity, index) {
    const item = document.createElement('div');
    item.className = 'activity-item';
    item.style.opacity = '0';
    item.style.transform = 'translateX(-20px)';
    
    const iconClass = getActivityIconClass(activity.type);
    
    item.innerHTML = `
        <div class="activity-icon ${activity.type}">
            <i class="${iconClass}"></i>
        </div>
        <div class="activity-content">
            <div class="activity-text">${activity.text}</div>
            <div class="activity-time">${activity.time}</div>
        </div>
    `;
    
    // Animate in
    setTimeout(() => {
        item.style.transition = 'all 0.5s ease';
        item.style.opacity = '1';
        item.style.transform = 'translateX(0)';
    }, index * 100);
    
    return item;
}

function getActivityIconClass(type) {
    const icons = {
        created: 'fas fa-plus',
        updated: 'fas fa-edit',
        completed: 'fas fa-check',
        deleted: 'fas fa-trash',
        assigned: 'fas fa-user-plus'
    };
    return icons[type] || 'fas fa-info';
}

function populateProjects() {
    // This would populate project cards if they exist on the page
    const projectCards = document.querySelectorAll('.project-card');
    
    projectCards.forEach((card, index) => {
        const project = dashboardData.projects[index];
        if (project) {
            updateProjectCard(card, project);
        }
    });
}

function updateProjectCard(card, project) {
    const titleElement = card.querySelector('.project-title');
    const descriptionElement = card.querySelector('.project-description');
    const progressElement = card.querySelector('.progress-fill');
    const deadlineElement = card.querySelector('.project-deadline');
    
    if (titleElement) titleElement.textContent = project.title;
    if (descriptionElement) descriptionElement.textContent = project.description;
    if (progressElement) {
        progressElement.style.width = project.progress + '%';
    }
    if (deadlineElement) {
        deadlineElement.textContent = formatDate(project.deadline);
        deadlineElement.setAttribute('data-deadline', project.deadline);
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = date - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) {
        return `${Math.abs(diffDays)} days overdue`;
    } else if (diffDays === 0) {
        return 'Due today';
    } else if (diffDays === 1) {
        return 'Due tomorrow';
    } else {
        return `Due in ${diffDays} days`;
    }
}

function animateNumber(element, target) {
    if (!element) return;
    
    const duration = 1000;
    const start = performance.now();
    const startValue = parseInt(element.textContent) || 0;
    
    function updateNumber(currentTime) {
        const elapsed = currentTime - start;
        const progress = Math.min(elapsed / duration, 1);
        const current = Math.floor(startValue + (target - startValue) * progress);
        
        element.textContent = current;
        
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        }
    }
    
    requestAnimationFrame(updateNumber);
}

// Initialize dashboard data when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only populate if we're on the dashboard/home page
    if (window.location.pathname === '/' || window.location.pathname.includes('dashboard')) {
        setTimeout(populateDashboard, 500); // Delay to allow animations to start
    }
});

// Export for use in other scripts
window.DashboardData = {
    populateDashboard,
    animateNumber,
    formatDate
};
