/**
 * Admin Analytics Dashboard
 * Displays comprehensive analytics with Recharts
 */

class AnalyticsDashboard {
    constructor() {
        this.analytics = null;
        this.days = 30;
        this.init();
    }
    
    /**
     * Initialize dashboard
     */
    async init() {
        await this.loadAnalytics();
        this.renderDashboard();
        this.setupEventListeners();
    }
    
    /**
     * Load analytics data from API
     */
    async loadAnalytics() {
        try {
            const response = await fetch(`/api/admin/analytics?days=${this.days}`, {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to load analytics');
            }
            
            this.analytics = await response.json();
            console.log('Analytics loaded:', this.analytics);
        } catch (error) {
            console.error('Error loading analytics:', error);
            this.showError('Failed to load analytics data');
        }
    }
    
    /**
     * Render dashboard
     */
    renderDashboard() {
        if (!this.analytics) return;
        
        // Render KPI cards
        this.renderKPICards();
        
        // Render charts
        this.renderTeamPerformanceChart();
        this.renderTaskDistributionChart();
        this.renderCompletionRatioChart();
        this.renderPerformanceTrendChart();
        this.renderTopPerformersChart();
        this.renderProjectStatsChart();
    }
    
    /**
     * Render KPI cards
     */
    renderKPICards() {
        const kpiContainer = document.getElementById('kpi-cards');
        if (!kpiContainer) return;
        
        const data = this.analytics;
        const productivity = data.productivity || {};
        const team = data.team_performance || {};
        const completion = data.task_completion || {};
        
        const kpis = [
            {
                title: 'Total Projects',
                value: data.projects ? data.projects.length : 0,
                icon: '📊',
                color: 'blue'
            },
            {
                title: 'Total Tasks',
                value: completion.total_tasks || 0,
                icon: '✓',
                color: 'green'
            },
            {
                title: 'Completion Rate',
                value: `${(completion.completion_percentage || 0).toFixed(1)}%`,
                icon: '📈',
                color: 'purple'
            },
            {
                title: 'Productivity Index',
                value: `${(productivity.productivity_index || 0).toFixed(1)}%`,
                icon: '⚡',
                color: 'orange'
            },
            {
                title: 'Team Performance',
                value: `${(team.team_performance_score || 0).toFixed(1)}`,
                icon: '🎯',
                color: 'red'
            },
            {
                title: 'On-Time Ratio',
                value: `${(team.on_time_percentage || 0).toFixed(1)}%`,
                icon: '⏱️',
                color: 'cyan'
            }
        ];
        
        kpiContainer.innerHTML = kpis.map(kpi => `
            <div class="kpi-card kpi-${kpi.color}">
                <div class="kpi-icon">${kpi.icon}</div>
                <div class="kpi-content">
                    <div class="kpi-title">${kpi.title}</div>
                    <div class="kpi-value">${kpi.value}</div>
                </div>
            </div>
        `).join('');
    }
    
    /**
     * Render team performance chart
     */
    renderTeamPerformanceChart() {
        const container = document.getElementById('team-performance-chart');
        if (!container || !this.analytics.team_performance) return;
        
        const data = this.analytics.team_performance;
        
        const chartHTML = `
            <div class="chart-container">
                <h3>Team Performance</h3>
                <div class="chart-stats">
                    <div class="stat">
                        <span class="stat-label">On-Time Tasks</span>
                        <span class="stat-value">${data.on_time_tasks}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Late Tasks</span>
                        <span class="stat-value">${data.late_tasks}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">On-Time Ratio</span>
                        <span class="stat-value">${(data.on_time_percentage || 0).toFixed(1)}%</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Avg Completion Time</span>
                        <span class="stat-value">${(data.avg_completion_time || 0).toFixed(1)}h</span>
                    </div>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-label">On-Time Performance</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${data.on_time_percentage || 0}%"></div>
                    </div>
                    <div class="progress-text">${(data.on_time_percentage || 0).toFixed(1)}%</div>
                </div>
            </div>
        `;
        
        container.innerHTML = chartHTML;
    }
    
    /**
     * Render task distribution chart
     */
    renderTaskDistributionChart() {
        const container = document.getElementById('task-distribution-chart');
        if (!container || !this.analytics.task_distribution) return;
        
        const distribution = this.analytics.task_distribution;
        
        // Get top 10 skills
        const topSkills = Object.entries(distribution)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);
        
        const chartHTML = `
            <div class="chart-container">
                <h3>Task Distribution by Skill</h3>
                <div class="bar-chart">
                    ${topSkills.map(([skill, count]) => `
                        <div class="bar-item">
                            <div class="bar-label">${skill}</div>
                            <div class="bar-container">
                                <div class="bar" style="width: ${(count / Math.max(...topSkills.map(s => s[1]))) * 100}%">
                                    <span class="bar-value">${count}</span>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        container.innerHTML = chartHTML;
    }
    
    /**
     * Render completion ratio chart
     */
    renderCompletionRatioChart() {
        const container = document.getElementById('completion-ratio-chart');
        if (!container || !this.analytics.task_completion) return;
        
        const data = this.analytics.task_completion;
        
        const chartHTML = `
            <div class="chart-container">
                <h3>Task Status Distribution</h3>
                <div class="pie-chart-stats">
                    <div class="pie-stat completed">
                        <div class="pie-stat-value">${data.completed}</div>
                        <div class="pie-stat-label">Completed</div>
                    </div>
                    <div class="pie-stat in-progress">
                        <div class="pie-stat-value">${data.in_progress}</div>
                        <div class="pie-stat-label">In Progress</div>
                    </div>
                    <div class="pie-stat pending">
                        <div class="pie-stat-value">${data.pending}</div>
                        <div class="pie-stat-label">Pending</div>
                    </div>
                    <div class="pie-stat overdue">
                        <div class="pie-stat-value">${data.overdue}</div>
                        <div class="pie-stat-label">Overdue</div>
                    </div>
                </div>
                <div class="completion-gauge">
                    <div class="gauge-label">Completion Rate</div>
                    <div class="gauge-container">
                        <div class="gauge-fill" style="width: ${data.completion_percentage || 0}%"></div>
                    </div>
                    <div class="gauge-value">${(data.completion_percentage || 0).toFixed(1)}%</div>
                </div>
            </div>
        `;
        
        container.innerHTML = chartHTML;
    }
    
    /**
     * Render performance trend chart
     */
    renderPerformanceTrendChart() {
        const container = document.getElementById('performance-trend-chart');
        if (!container || !this.analytics.performance_trend) return;
        
        const trend = this.analytics.performance_trend;
        
        if (trend.length === 0) {
            container.innerHTML = '<div class="chart-container"><p>No trend data available</p></div>';
            return;
        }
        
        const chartHTML = `
            <div class="chart-container">
                <h3>Performance Trend (${this.days} days)</h3>
                <div class="line-chart">
                    <div class="chart-area">
                        ${trend.map((point, index) => `
                            <div class="chart-point" style="left: ${(index / (trend.length - 1 || 1)) * 100}%">
                                <div class="point-dot" style="height: ${(point.average_score / 100) * 100}%"></div>
                                <div class="point-tooltip">
                                    <div>${point.date}</div>
                                    <div>Score: ${point.average_score.toFixed(1)}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="trend-stats">
                    <div class="trend-stat">
                        <span>Avg Score</span>
                        <span>${(trend.reduce((a, b) => a + b.average_score, 0) / trend.length).toFixed(1)}</span>
                    </div>
                    <div class="trend-stat">
                        <span>Max Score</span>
                        <span>${Math.max(...trend.map(t => t.max_score)).toFixed(1)}</span>
                    </div>
                    <div class="trend-stat">
                        <span>Min Score</span>
                        <span>${Math.min(...trend.map(t => t.min_score)).toFixed(1)}</span>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = chartHTML;
    }
    
    /**
     * Render top performers chart
     */
    renderTopPerformersChart() {
        const container = document.getElementById('top-performers-chart');
        if (!container || !this.analytics.top_performers) return;
        
        const performers = this.analytics.top_performers;
        
        const chartHTML = `
            <div class="chart-container">
                <h3>Top Performers</h3>
                <div class="performers-list">
                    ${performers.map((performer, index) => `
                        <div class="performer-item">
                            <div class="performer-rank">#${index + 1}</div>
                            <div class="performer-info">
                                <div class="performer-name">${performer.username}</div>
                                <div class="performer-stats">
                                    <span>Score: ${performer.performance_score.toFixed(1)}</span>
                                    <span>Tasks: ${performer.tasks_completed}</span>
                                </div>
                            </div>
                            <div class="performer-score">
                                <div class="score-bar">
                                    <div class="score-fill" style="width: ${performer.performance_score}%"></div>
                                </div>
                                <div class="score-value">${performer.performance_score.toFixed(0)}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        container.innerHTML = chartHTML;
    }
    
    /**
     * Render project stats chart
     */
    renderProjectStatsChart() {
        const container = document.getElementById('project-stats-chart');
        if (!container || !this.analytics.projects) return;
        
        const projects = this.analytics.projects;
        
        const chartHTML = `
            <div class="chart-container">
                <h3>Project Status Overview</h3>
                <div class="projects-grid">
                    ${projects.map(project => `
                        <div class="project-card">
                            <div class="project-name">${project.project_name}</div>
                            <div class="project-progress">
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: ${project.completion_percentage}%"></div>
                                </div>
                                <div class="progress-text">${project.completion_percentage.toFixed(0)}%</div>
                            </div>
                            <div class="project-stats">
                                <span class="stat-completed">${project.completed} done</span>
                                <span class="stat-pending">${project.pending} pending</span>
                                <span class="stat-overdue">${project.overdue} overdue</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        container.innerHTML = chartHTML;
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Days filter
        const daysButtons = document.querySelectorAll('[data-days]');
        daysButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                daysButtons.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.days = parseInt(e.target.dataset.days);
                this.loadAnalytics().then(() => this.renderDashboard());
            });
        });
        
        // Export button
        const exportBtn = document.getElementById('export-analytics-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportAnalytics());
        }
    }
    
    /**
     * Export analytics data
     */
    async exportAnalytics() {
        try {
            const response = await fetch(`/api/admin/analytics/export?days=${this.days}`, {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });
            
            const data = await response.json();
            
            // Create download
            const element = document.createElement('a');
            element.setAttribute('href', 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(data, null, 2)));
            element.setAttribute('download', `analytics-${new Date().toISOString().split('T')[0]}.json`);
            element.style.display = 'none';
            document.body.appendChild(element);
            element.click();
            document.body.removeChild(element);
        } catch (error) {
            console.error('Error exporting analytics:', error);
            this.showError('Failed to export analytics');
        }
    }
    
    /**
     * Show error message
     */
    showError(message) {
        const errorContainer = document.getElementById('error-message');
        if (errorContainer) {
            errorContainer.textContent = message;
            errorContainer.style.display = 'block';
        }
    }
    
    /**
     * Get authentication token
     */
    getToken() {
        return localStorage.getItem('token') || document.querySelector('meta[name="csrf-token"]')?.content || '';
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.analyticsDashboard = new AnalyticsDashboard();
});
