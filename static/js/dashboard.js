// TaskManager - Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    initializeCharts();
    initializeRealTimeUpdates();
    initializeTaskManagement();
    initializeProjectManagement();
});

// Dashboard Initialization
function initializeDashboard() {
    // Animate stats cards on load
    animateStatsCards();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Setup quick actions
    setupQuickActions();
    
    // Initialize search and filters
    initializeSearchFilters();
}

// Animate stats cards
function animateStatsCards() {
    const statCards = document.querySelectorAll('.stat-card');
    
    statCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
            
            // Animate the number
            const numberElement = card.querySelector('.stat-number');
            if (numberElement) {
                animateNumber(numberElement);
            }
        }, index * 150);
    });
}

// Animate number counting
function animateNumber(element) {
    const target = parseInt(element.textContent);
    const duration = 1000;
    const start = performance.now();
    
    function updateNumber(currentTime) {
        const elapsed = currentTime - start;
        const progress = Math.min(elapsed / duration, 1);
        const current = Math.floor(progress * target);
        
        element.textContent = current;
        
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        }
    }
    
    requestAnimationFrame(updateNumber);
}

// Initialize tooltips
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            showTooltip(this, this.getAttribute('data-tooltip'));
        });
        
        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

function showTooltip(element, text) {
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: absolute;
        background: #1f2937;
        color: white;
        padding: 0.5rem 0.75rem;
        border-radius: 0.375rem;
        font-size: 0.875rem;
        z-index: 1000;
        pointer-events: none;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        max-width: 200px;
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
}

function hideTooltip() {
    const tooltip = document.querySelector('.custom-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Setup quick actions
function setupQuickActions() {
    const quickActionBtns = document.querySelectorAll('.quick-action-btn');
    
    quickActionBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const action = this.getAttribute('data-action');
            handleQuickAction(action);
        });
    });
}

function handleQuickAction(action) {
    switch (action) {
        case 'create-project':
            window.location.href = '/projects/create';
            break;
        case 'create-task':
            // Show task creation modal or redirect
            showTaskCreationModal();
            break;
        case 'view-projects':
            window.location.href = '/projects/';
            break;
        case 'view-tasks':
            window.location.href = '/tasks/';
            break;
        case 'export-data':
            exportDashboardData();
            break;
        case 'settings':
            window.location.href = '/settings';
            break;
    }
}

// Initialize charts
function initializeCharts() {
    // Progress rings animation
    animateProgressRings();
    
    // Activity timeline
    initializeActivityTimeline();
}

function animateProgressRings() {
    const progressRings = document.querySelectorAll('.progress-ring');
    
    progressRings.forEach(ring => {
        const circle = ring.querySelector('.progress');
        const percentage = parseInt(ring.getAttribute('data-percentage') || '0');
        
        if (circle) {
            const circumference = 2 * Math.PI * 45; // radius = 45
            circle.style.strokeDasharray = circumference;
            circle.style.strokeDashoffset = circumference;
            
            setTimeout(() => {
                circle.style.transition = 'stroke-dashoffset 1s ease-in-out';
                circle.style.strokeDashoffset = circumference - (percentage / 100) * circumference;
            }, 500);
        }
    });
}

function initializeActivityTimeline() {
    const activityItems = document.querySelectorAll('.activity-item');
    
    activityItems.forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateX(-20px)';
        
        setTimeout(() => {
            item.style.transition = 'all 0.5s ease';
            item.style.opacity = '1';
            item.style.transform = 'translateX(0)';
        }, index * 100);
    });
}

// Real-time updates
function initializeRealTimeUpdates() {
    // Auto-refresh dashboard data every 30 seconds
    setInterval(refreshDashboardData, 30000);
    
    // Setup WebSocket connection for real-time updates (if available)
    setupWebSocketConnection();
}

function refreshDashboardData() {
    // Only refresh if user is on dashboard
    if (window.location.pathname === '/' || window.location.pathname.includes('dashboard')) {
        fetch('/api/dashboard-data', {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            updateDashboardStats(data.stats);
            updateActivityFeed(data.activity);
            updateProjectCards(data.projects);
        })
        .catch(error => console.log('Dashboard refresh failed:', error));
    }
}

function updateDashboardStats(stats) {
    Object.keys(stats).forEach(key => {
        const element = document.querySelector(`[data-stat="${key}"]`);
        if (element) {
            animateNumber(element);
        }
    });
}

function updateActivityFeed(activities) {
    const activityList = document.querySelector('.activity-list');
    if (activityList && activities.length > 0) {
        // Update activity feed with new data
        // This would typically involve updating the DOM with new activity items
    }
}

function updateProjectCards(projects) {
    // Update project cards with new data
    // This would involve updating project progress, status, etc.
}

function setupWebSocketConnection() {
    // WebSocket connection for real-time updates
    // This would connect to a WebSocket server for live updates
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    try {
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = function() {
            console.log('WebSocket connected');
        };
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };
        
        ws.onclose = function() {
            console.log('WebSocket disconnected');
            // Attempt to reconnect after 5 seconds
            setTimeout(setupWebSocketConnection, 5000);
        };
    } catch (error) {
        console.log('WebSocket not available:', error);
    }
}

function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'task_created':
            showNotification('New task created: ' + data.task.title, 'info');
            refreshDashboardData();
            break;
        case 'task_updated':
            showNotification('Task updated: ' + data.task.title, 'info');
            refreshDashboardData();
            break;
        case 'project_created':
            showNotification('New project created: ' + data.project.title, 'success');
            refreshDashboardData();
            break;
    }
}

// Task management
function initializeTaskManagement() {
    // Task status updates
    setupTaskStatusUpdates();
    
    // Task filtering and sorting
    setupTaskFiltering();
    
    // Task drag and drop (if implemented)
    setupTaskDragDrop();
}

function setupTaskStatusUpdates() {
    const statusButtons = document.querySelectorAll('[data-task-status]');
    
    statusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.getAttribute('data-task-id');
            const newStatus = this.getAttribute('data-task-status');
            
            updateTaskStatus(taskId, newStatus);
        });
    });
}

function updateTaskStatus(taskId, status) {
    fetch(`/api/tasks/${taskId}/status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ status: status })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Task status updated successfully!', 'success');
            // Update the UI
            updateTaskStatusUI(taskId, status);
        } else {
            showNotification('Failed to update task status', 'error');
        }
    })
    .catch(error => {
        showNotification('Network error occurred', 'error');
        console.error('Task status update error:', error);
    });
}

function updateTaskStatusUI(taskId, status) {
    const taskElement = document.querySelector(`[data-task-id="${taskId}"]`);
    if (taskElement) {
        const statusBadge = taskElement.querySelector('.task-status');
        if (statusBadge) {
            statusBadge.className = `task-status ${status.toLowerCase().replace(' ', '-')}`;
            statusBadge.textContent = status;
        }
    }
}

function setupTaskFiltering() {
    const filterInputs = document.querySelectorAll('.task-filter');
    
    filterInputs.forEach(input => {
        input.addEventListener('input', debounce(function() {
            filterTasks();
        }, 300));
    });
}

function filterTasks() {
    const filters = {
        status: document.querySelector('[data-filter="status"]')?.value,
        priority: document.querySelector('[data-filter="priority"]')?.value,
        assignee: document.querySelector('[data-filter="assignee"]')?.value,
        search: document.querySelector('[data-filter="search"]')?.value
    };
    
    const taskItems = document.querySelectorAll('.task-item');
    
    taskItems.forEach(item => {
        const shouldShow = matchesFilters(item, filters);
        item.style.display = shouldShow ? 'flex' : 'none';
    });
}

function matchesFilters(item, filters) {
    // Check status filter
    if (filters.status && filters.status !== 'all') {
        const status = item.getAttribute('data-status');
        if (status !== filters.status) return false;
    }
    
    // Check priority filter
    if (filters.priority && filters.priority !== 'all') {
        const priority = item.getAttribute('data-priority');
        if (priority !== filters.priority) return false;
    }
    
    // Check assignee filter
    if (filters.assignee && filters.assignee !== 'all') {
        const assignee = item.getAttribute('data-assignee');
        if (assignee !== filters.assignee) return false;
    }
    
    // Check search filter
    if (filters.search) {
        const text = item.textContent.toLowerCase();
        if (!text.includes(filters.search.toLowerCase())) return false;
    }
    
    return true;
}

function setupTaskDragDrop() {
    // Implement drag and drop for task reordering
    // This would require additional HTML structure and drag/drop API
}

// Project management
function initializeProjectManagement() {
    // Project progress updates
    updateProjectProgress();
    
    // Project deadline warnings
    checkProjectDeadlines();
}

function updateProjectProgress() {
    const projectCards = document.querySelectorAll('.project-card');
    
    projectCards.forEach(card => {
        const progressBar = card.querySelector('.progress-fill');
        const percentage = parseInt(card.getAttribute('data-progress') || '0');
        
        if (progressBar) {
            setTimeout(() => {
                progressBar.style.width = percentage + '%';
            }, 500);
        }
    });
}

function checkProjectDeadlines() {
    const projectCards = document.querySelectorAll('.project-card');
    const today = new Date();
    
    projectCards.forEach(card => {
        const deadlineElement = card.querySelector('.project-deadline');
        if (deadlineElement) {
            const deadline = new Date(deadlineElement.getAttribute('data-deadline'));
            const daysUntilDeadline = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24));
            
            if (daysUntilDeadline < 0) {
                deadlineElement.classList.add('overdue');
            } else if (daysUntilDeadline <= 3) {
                deadlineElement.classList.add('due-soon');
            }
        }
    });
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function showNotification(message, type = 'info') {
    if (window.TaskManager && window.TaskManager.showNotification) {
        window.TaskManager.showNotification(message, type);
    } else {
        // Fallback notification
        alert(message);
    }
}

function exportDashboardData() {
    // Export dashboard data as CSV or PDF
    fetch('/api/export/dashboard', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'dashboard-export.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        showNotification('Export failed', 'error');
        console.error('Export error:', error);
    });
}

function showTaskCreationModal() {
    // Show a modal for quick task creation
    // This would be implemented with a modal component
    window.location.href = '/tasks/create';
}
