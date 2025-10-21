// TaskManager - Enterprise JavaScript

class EnterpriseTaskManager {
    constructor() {
        this.init();
        this.setupEventListeners();
        this.initializeAdvancedFeatures();
    }

    init() {
        this.sidebarOpen = false;
        this.notifications = [];
        this.analytics = new AnalyticsManager();
        this.realtime = new RealtimeManager();
        this.search = new SearchManager();
        this.filters = new FilterManager();
    }

    setupEventListeners() {
        // Sidebar toggle
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-sidebar-toggle]')) {
                this.toggleSidebar();
            }
        });

        // Search functionality
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce((e) => {
                this.search.performSearch(e.target.value);
            }, 300));
        }

        // Notification system
        this.setupNotificationSystem();

        // Keyboard shortcuts
        this.setupKeyboardShortcuts();

        // Real-time updates
        this.setupRealtimeUpdates();
    }

    initializeAdvancedFeatures() {
        this.initializeAnalytics();
        this.initializeAdvancedCharts();
        this.initializeDataTables();
        this.initializeAdvancedFilters();
        this.initializeDragAndDrop();
        this.initializeAdvancedModals();
    }

    toggleSidebar() {
        const sidebar = document.querySelector('.enterprise-sidebar');
        const main = document.querySelector('.enterprise-main');
        
        this.sidebarOpen = !this.sidebarOpen;
        
        if (this.sidebarOpen) {
            sidebar.classList.add('open');
            main.style.marginLeft = '280px';
        } else {
            sidebar.classList.remove('open');
            main.style.marginLeft = '0';
        }
    }

    setupNotificationSystem() {
        // Create notification container
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'fixed top-4 right-4 z-50 space-y-2';
        document.body.appendChild(container);

        // Listen for real-time notifications
        this.realtime.on('notification', (data) => {
            this.showNotification(data.message, data.type, data.duration);
        });
    }

    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">
                    <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                </div>
                <div class="notification-body">
                    <div class="notification-title">${this.getNotificationTitle(type)}</div>
                    <div class="notification-message">${message}</div>
                </div>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        document.getElementById('notification-container').appendChild(notification);

        // Animate in
        setTimeout(() => notification.classList.add('show'), 100);

        // Auto remove
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    getNotificationTitle(type) {
        const titles = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Information'
        };
        return titles[type] || 'Notification';
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K for search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                document.querySelector('.search-input')?.focus();
            }

            // Ctrl/Cmd + / for help
            if ((e.ctrlKey || e.metaKey) && e.key === '/') {
                e.preventDefault();
                this.showKeyboardShortcuts();
            }

            // Escape to close modals
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
    }

    showKeyboardShortcuts() {
        const shortcuts = [
            { key: 'Ctrl+K', description: 'Focus search' },
            { key: 'Ctrl+/', description: 'Show shortcuts' },
            { key: 'Escape', description: 'Close modals' },
            { key: 'Ctrl+N', description: 'New project' },
            { key: 'Ctrl+T', description: 'New task' }
        ];

        const modal = this.createModal('Keyboard Shortcuts', `
            <div class="shortcuts-list">
                ${shortcuts.map(s => `
                    <div class="shortcut-item">
                        <kbd>${s.key}</kbd>
                        <span>${s.description}</span>
                    </div>
                `).join('')}
            </div>
        `);

        this.showModal(modal);
    }

    setupRealtimeUpdates() {
        // WebSocket connection for real-time updates
        this.realtime.connect();
        
        // Auto-refresh data
        setInterval(() => {
            this.refreshDashboardData();
        }, 30000);
    }

    initializeAnalytics() {
        this.analytics.init();
        this.analytics.loadDashboardMetrics();
        this.analytics.setupCharts();
    }

    initializeAdvancedCharts() {
        // Initialize Chart.js or similar charting library
        this.setupPerformanceChart();
        this.setupTaskDistributionChart();
        this.setupTimelineChart();
    }

    setupPerformanceChart() {
        const ctx = document.getElementById('performance-chart');
        if (!ctx) return;

        // This would integrate with Chart.js
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Tasks Completed',
                    data: [12, 19, 3, 5, 2, 3],
                    borderColor: '#4f46e5',
                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                }
            }
        });
    }

    initializeDataTables() {
        // Initialize advanced data tables with sorting, filtering, pagination
        const tables = document.querySelectorAll('.table-enterprise');
        tables.forEach(table => {
            this.enhanceDataTable(table);
        });
    }

    enhanceDataTable(table) {
        // Add sorting functionality
        const headers = table.querySelectorAll('th[data-sortable]');
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                this.sortTable(table, header);
            });
        });

        // Add row selection
        this.addRowSelection(table);
    }

    sortTable(table, header) {
        const column = header.cellIndex;
        const rows = Array.from(table.querySelectorAll('tbody tr'));
        const isAscending = header.classList.contains('sort-asc');
        
        // Remove existing sort classes
        table.querySelectorAll('th').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
        });

        // Add sort class
        header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');

        // Sort rows
        rows.sort((a, b) => {
            const aVal = a.cells[column].textContent.trim();
            const bVal = b.cells[column].textContent.trim();
            
            if (isAscending) {
                return bVal.localeCompare(aVal);
            } else {
                return aVal.localeCompare(bVal);
            }
        });

        // Reorder rows
        const tbody = table.querySelector('tbody');
        rows.forEach(row => tbody.appendChild(row));
    }

    addRowSelection(table) {
        const tbody = table.querySelector('tbody');
        if (!tbody) return;

        // Add checkbox column header
        const headerRow = table.querySelector('thead tr');
        const selectAllTh = document.createElement('th');
        selectAllTh.innerHTML = '<input type="checkbox" class="select-all">';
        headerRow.insertBefore(selectAllTh, headerRow.firstChild);

        // Add checkboxes to each row
        tbody.querySelectorAll('tr').forEach(row => {
            const checkbox = document.createElement('td');
            checkbox.innerHTML = '<input type="checkbox" class="row-select">';
            row.insertBefore(checkbox, row.firstChild);
        });

        // Handle select all
        const selectAll = table.querySelector('.select-all');
        selectAll.addEventListener('change', (e) => {
            const rowCheckboxes = table.querySelectorAll('.row-select');
            rowCheckboxes.forEach(checkbox => {
                checkbox.checked = e.target.checked;
            });
        });
    }

    initializeAdvancedFilters() {
        this.filters.init();
        this.setupAdvancedSearch();
        this.setupDateRangeFilters();
        this.setupStatusFilters();
    }

    setupAdvancedSearch() {
        const searchContainer = document.querySelector('.search-box');
        if (!searchContainer) return;

        // Add search suggestions
        const suggestions = document.createElement('div');
        suggestions.className = 'search-suggestions';
        searchContainer.appendChild(suggestions);

        const searchInput = searchContainer.querySelector('.search-input');
        searchInput.addEventListener('input', (e) => {
            this.showSearchSuggestions(e.target.value, suggestions);
        });
    }

    showSearchSuggestions(query, container) {
        if (query.length < 2) {
            container.style.display = 'none';
            return;
        }

        // Mock suggestions - in real app, this would be an API call
        const suggestions = [
            { type: 'project', title: 'Website Redesign', id: 1 },
            { type: 'task', title: 'Design Mockups', id: 2 },
            { type: 'user', title: 'John Doe', id: 3 }
        ].filter(item => 
            item.title.toLowerCase().includes(query.toLowerCase())
        );

        container.innerHTML = suggestions.map(item => `
            <div class="suggestion-item" data-type="${item.type}" data-id="${item.id}">
                <i class="fas fa-${this.getSuggestionIcon(item.type)}"></i>
                <span>${item.title}</span>
            </div>
        `).join('');

        container.style.display = 'block';
    }

    getSuggestionIcon(type) {
        const icons = {
            project: 'folder',
            task: 'tasks',
            user: 'user'
        };
        return icons[type] || 'search';
    }

    initializeDragAndDrop() {
        // Initialize drag and drop for tasks and projects
        this.setupTaskDragDrop();
        this.setupProjectDragDrop();
    }

    setupTaskDragDrop() {
        const taskContainers = document.querySelectorAll('.task-container');
        taskContainers.forEach(container => {
            this.makeSortable(container);
        });
    }

    makeSortable(container) {
        let draggedElement = null;

        container.addEventListener('dragstart', (e) => {
            draggedElement = e.target;
            e.target.style.opacity = '0.5';
        });

        container.addEventListener('dragend', (e) => {
            e.target.style.opacity = '1';
            draggedElement = null;
        });

        container.addEventListener('dragover', (e) => {
            e.preventDefault();
        });

        container.addEventListener('drop', (e) => {
            e.preventDefault();
            if (draggedElement && e.target !== draggedElement) {
                container.insertBefore(draggedElement, e.target);
                this.updateTaskOrder(container);
            }
        });
    }

    updateTaskOrder(container) {
        const tasks = Array.from(container.querySelectorAll('.task-item'));
        const order = tasks.map((task, index) => ({
            id: task.dataset.taskId,
            order: index
        }));

        // Send update to server
        fetch('/api/tasks/reorder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ order })
        });
    }

    initializeAdvancedModals() {
        this.setupModalSystem();
        this.setupQuickActions();
    }

    setupModalSystem() {
        // Create modal container
        const modalContainer = document.createElement('div');
        modalContainer.id = 'modal-container';
        modalContainer.className = 'modal-container';
        document.body.appendChild(modalContainer);
    }

    createModal(title, content, actions = []) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">${title}</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    ${actions.map(action => `
                        <button class="btn btn-${action.type || 'secondary'}" onclick="${action.onclick || ''}">
                            ${action.text}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
        return modal;
    }

    showModal(modal) {
        document.getElementById('modal-container').appendChild(modal);
        setTimeout(() => modal.classList.add('show'), 100);
    }

    closeAllModals() {
        document.querySelectorAll('.modal-overlay').forEach(modal => {
            modal.classList.remove('show');
            setTimeout(() => modal.remove(), 300);
        });
    }

    setupQuickActions() {
        // Quick action buttons
        const quickActions = [
            {
                key: 'n',
                action: () => this.showNewProjectModal(),
                description: 'New Project'
            },
            {
                key: 't',
                action: () => this.showNewTaskModal(),
                description: 'New Task'
            }
        ];

        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                const action = quickActions.find(a => a.key === e.key.toLowerCase());
                if (action) {
                    e.preventDefault();
                    action.action();
                }
            }
        });
    }

    showNewProjectModal() {
        const modal = this.createModal('New Project', `
            <form id="new-project-form">
                <div class="form-group">
                    <label for="project-title">Project Title</label>
                    <input type="text" id="project-title" class="form-control" required>
                </div>
                <div class="form-group">
                    <label for="project-description">Description</label>
                    <textarea id="project-description" class="form-control" rows="3"></textarea>
                </div>
                <div class="form-group">
                    <label for="project-deadline">Deadline</label>
                    <input type="date" id="project-deadline" class="form-control">
                </div>
            </form>
        `, [
            { text: 'Cancel', type: 'secondary', onclick: 'this.closest(".modal-overlay").remove()' },
            { text: 'Create', type: 'primary', onclick: 'this.createProject()' }
        ]);

        this.showModal(modal);
    }

    refreshDashboardData() {
        // Refresh dashboard metrics
        this.analytics.refreshMetrics();
        
        // Refresh activity feed
        this.refreshActivityFeed();
        
        // Refresh project cards
        this.refreshProjectCards();
    }

    refreshActivityFeed() {
        fetch('/api/activity')
            .then(response => response.json())
            .then(data => {
                this.updateActivityFeed(data);
            })
            .catch(error => console.error('Failed to refresh activity:', error));
    }

    updateActivityFeed(activities) {
        const container = document.querySelector('.activity-list');
        if (!container) return;

        container.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon ${activity.type}">
                    <i class="fas fa-${this.getActivityIcon(activity.type)}"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-text">${activity.text}</div>
                    <div class="activity-time">${activity.time}</div>
                </div>
            </div>
        `).join('');
    }

    getActivityIcon(type) {
        const icons = {
            created: 'plus',
            updated: 'edit',
            completed: 'check',
            assigned: 'user-plus'
        };
        return icons[type] || 'info';
    }

    debounce(func, wait) {
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
}

// Analytics Manager
class AnalyticsManager {
    constructor() {
        this.metrics = {};
        this.charts = {};
    }

    init() {
        this.loadMetrics();
        this.setupCharts();
    }

    loadMetrics() {
        // Load dashboard metrics
        fetch('/api/analytics/metrics')
            .then(response => response.json())
            .then(data => {
                this.metrics = data;
                this.updateMetricCards();
            })
            .catch(error => console.error('Failed to load metrics:', error));
    }

    updateMetricCards() {
        Object.keys(this.metrics).forEach(key => {
            const element = document.querySelector(`[data-metric="${key}"]`);
            if (element) {
                this.animateNumber(element, this.metrics[key].value);
            }
        });
    }

    animateNumber(element, target) {
        const start = parseInt(element.textContent) || 0;
        const duration = 1000;
        const startTime = performance.now();

        const update = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const current = Math.floor(start + (target - start) * progress);
            
            element.textContent = current;
            
            if (progress < 1) {
                requestAnimationFrame(update);
            }
        };

        requestAnimationFrame(update);
    }

    setupCharts() {
        // Initialize various charts
        this.setupPerformanceChart();
        this.setupTaskDistributionChart();
        this.setupTimelineChart();
    }

    refreshMetrics() {
        this.loadMetrics();
    }
}

// Realtime Manager
class RealtimeManager {
    constructor() {
        this.ws = null;
        this.listeners = {};
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                setTimeout(() => this.connect(), 5000);
            };
        } catch (error) {
            console.log('WebSocket not available:', error);
        }
    }

    handleMessage(data) {
        if (this.listeners[data.type]) {
            this.listeners[data.type].forEach(callback => callback(data));
        }
    }

    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }
}

// Search Manager
class SearchManager {
    constructor() {
        this.results = [];
        this.history = [];
    }

    performSearch(query) {
        if (query.length < 2) return;

        fetch(`/api/search?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                this.results = data;
                this.displayResults();
            })
            .catch(error => console.error('Search failed:', error));
    }

    displayResults() {
        // Display search results in a dropdown or modal
        console.log('Search results:', this.results);
    }
}

// Filter Manager
class FilterManager {
    constructor() {
        this.activeFilters = {};
    }

    init() {
        this.setupFilterControls();
    }

    setupFilterControls() {
        const filterControls = document.querySelectorAll('.filter-control');
        filterControls.forEach(control => {
            control.addEventListener('change', (e) => {
                this.applyFilter(e.target.name, e.target.value);
            });
        });
    }

    applyFilter(name, value) {
        this.activeFilters[name] = value;
        this.updateResults();
    }

    updateResults() {
        // Apply filters to current view
        console.log('Active filters:', this.activeFilters);
    }
}

// Initialize Enterprise Task Manager
document.addEventListener('DOMContentLoaded', () => {
    window.enterpriseTM = new EnterpriseTaskManager();
});

// Export for global use
window.EnterpriseTaskManager = EnterpriseTaskManager;
