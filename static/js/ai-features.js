class AIChat {
    constructor() {
        this.chatContainer = document.getElementById('ai-chat-container');
        this.chatMessages = document.getElementById('ai-chat-messages');
        this.chatInput = document.getElementById('ai-chat-input');
        this.sendButton = document.getElementById('ai-chat-send');
        this.toggleButton = document.getElementById('ai-chat-toggle');
        this.isOpen = false;
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        // Toggle chat window
        if (this.toggleButton) {
            this.toggleButton.addEventListener('click', () => this.toggleChat());
        }
        
        // Send message on button click or Enter key
        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => this.sendMessage());
        }
        
        if (this.chatInput) {
            this.chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendMessage();
                }
            });
        }
    }
    
    toggleChat() {
        this.isOpen = !this.isOpen;
        if (this.chatContainer) {
            this.chatContainer.style.display = this.isOpen ? 'block' : 'none';
            this.toggleButton.textContent = this.isOpen ? '✕' : '🤖 AI Assistant';
        }
        
        if (this.isOpen) {
            this.chatInput.focus();
        }
    }
    
    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        this.addMessage('user', message);
        this.chatInput.value = '';
        
        try {
            // Show typing indicator
            const typingId = this.addTypingIndicator();
            
            // Send to server
            const response = await fetch('/ai/api/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
                },
                body: JSON.stringify({ message })
            });
            
            // Remove typing indicator
            this.removeTypingIndicator(typingId);
            
            if (!response.ok) {
                throw new Error('Failed to get response from AI');
            }
            
            const data = await response.json();
            this.addMessage('assistant', data.response);
            
            // Auto-scroll to bottom
            this.scrollToBottom();
            
        } catch (error) {
            console.error('AI Chat Error:', error);
            this.addMessage('error', 'Sorry, I encountered an error. Please try again later.');
        }
    }
    
    addMessage(sender, text) {
        if (!this.chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `ai-message ${sender}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = text;
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        
        // Auto-scroll to bottom
        this.scrollToBottom();
    }
    
    addTypingIndicator() {
        if (!this.chatMessages) return null;
        
        const typingId = 'typing-' + Date.now();
        const typingDiv = document.createElement('div');
        typingDiv.id = typingId;
        typingDiv.className = 'ai-message assistant-message typing-indicator';
        typingDiv.innerHTML = '<div class="typing-animation"><span></span><span></span><span></span></div>';
        
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
        
        return typingId;
    }
    
    removeTypingIndicator(id) {
        if (!id) return;
        const element = document.getElementById(id);
        if (element) {
            element.remove();
        }
    }
    
    scrollToBottom() {
        if (this.chatMessages) {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }
}

class AITaskAssistant {
    constructor() {
        this.initializeEventListeners();
        this.initializeTaskEstimation();
        this.initializeNaturalLanguageInput();
    }
    
    initializeEventListeners() {
        // Auto-estimate task duration when title or description changes
        const taskForm = document.getElementById('task-form');
        if (taskForm) {
            const titleInput = taskForm.querySelector('input[name="title"]');
            const descriptionInput = taskForm.querySelector('textarea[name="description"]');
            
            if (titleInput && descriptionInput) {
                const estimateButton = document.createElement('button');
                estimateButton.type = 'button';
                estimateButton.className = 'btn btn-sm btn-outline-secondary mt-2';
                estimateButton.id = 'estimate-duration-btn';
                estimateButton.innerHTML = '⏱️ Estimate Duration';
                
                const durationEstimate = document.createElement('span');
                durationEstimate.id = 'duration-estimate';
                durationEstimate.className = 'ml-2 text-muted';
                
                const container = document.createElement('div');
                container.className = 'd-flex align-items-center mt-2';
                container.appendChild(estimateButton);
                container.appendChild(durationEstimate);
                
                if (descriptionInput.nextElementSibling) {
                    descriptionInput.parentNode.insertBefore(container, descriptionInput.nextElementSibling);
                } else {
                    descriptionInput.parentNode.appendChild(container);
                }
                
                estimateButton.addEventListener('click', () => this.estimateTaskDuration());
            }
        }
    }
    
    initializeTaskEstimation() {
        // Check if we're on a task detail page with estimation data
        const taskEstimateElement = document.getElementById('task-estimate');
        if (taskEstimateElement) {
            const taskId = taskEstimateElement.dataset.taskId;
            if (taskId) {
                this.updateTaskEstimate(taskId);
            }
        }
    }
    
    initializeNaturalLanguageInput() {
        const quickAddForm = document.getElementById('quick-add-task');
        if (quickAddForm) {
            const input = quickAddForm.querySelector('input[type="text"]');
            const projectId = quickAddForm.dataset.projectId;
            
            if (input) {
                input.addEventListener('keypress', async (e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        const text = input.value.trim();
                        if (!text) return;
                        
                        try {
                            const response = await fetch('/ai/api/ai/create-task', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
                                },
                                body: JSON.stringify({
                                    text,
                                    project_id: projectId || null
                                })
                            });
                            
                            if (response.ok) {
                                const data = await response.json();
                                if (data.success) {
                                    // Show success message
                                    this.showToast('Task created successfully!', 'success');
                                    // Reload the page to show the new task
                                    setTimeout(() => window.location.reload(), 1000);
                                } else {
                                    throw new Error(data.error || 'Failed to create task');
                                }
                            } else {
                                throw new Error('Failed to create task');
                            }
                        } catch (error) {
                            console.error('Error creating task:', error);
                            this.showToast(error.message || 'Failed to create task', 'error');
                        }
                    }
                });
            }
        }
    }
    
    async estimateTaskDuration() {
        const title = document.querySelector('input[name="title"]')?.value || '';
        const description = document.querySelector('textarea[name="description"]')?.value || '';
        const projectId = document.querySelector('input[name="project_id"]')?.value || null;
        
        if (!title) {
            this.showToast('Please enter a task title first', 'warning');
            return;
        }
        
        const estimateBtn = document.getElementById('estimate-duration-btn');
        const originalText = estimateBtn.innerHTML;
        estimateBtn.disabled = true;
        estimateBtn.innerHTML = 'Estimating...';
        
        try {
            const response = await fetch('/ai/api/ai/estimate-duration', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
                },
                body: JSON.stringify({
                    title,
                    description,
                    project_id: projectId
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to get estimation');
            }
            
            const data = await response.json();
            const durationEstimate = document.getElementById('duration-estimate');
            
            if (data.estimated_days) {
                durationEstimate.textContent = `Estimated: ${data.estimated_days} days`;
                
                // Auto-fill due date if not already set
                const dueDateInput = document.querySelector('input[name="due_date"]');
                if (dueDateInput && !dueDateInput.value) {
                    const today = new Date();
                    const dueDate = new Date(today);
                    dueDate.setDate(today.getDate() + Math.ceil(data.estimated_days));
                    dueDateInput.value = dueDate.toISOString().split('T')[0];
                }
                
                this.showToast('Duration estimated successfully!', 'success');
            } else {
                durationEstimate.textContent = 'Not enough data for estimation';
            }
            
        } catch (error) {
            console.error('Estimation error:', error);
            this.showToast('Failed to estimate duration', 'error');
        } finally {
            estimateBtn.disabled = false;
            estimateBtn.innerHTML = originalText;
        }
    }
    
    async updateTaskEstimate(taskId) {
        try {
            const response = await fetch(`/ai/api/ai/risks?task_id=${taskId}`);
            if (response.ok) {
                const data = await response.json();
                const taskEstimateElement = document.getElementById('task-estimate');
                
                if (data.length > 0) {
                    const risk = data[0]; // Get the first (most relevant) risk
                    taskEstimateElement.textContent = `⚠️ High risk of missing deadline (${risk.risk_score}% chance)`;
                    taskEstimateElement.className = 'text-danger';
                } else {
                    taskEstimateElement.textContent = '✅ On track';
                    taskEstimateElement.className = 'text-success';
                }
            }
        } catch (error) {
            console.error('Failed to update task estimate:', error);
        }
    }
    
    showToast(message, type = 'info') {
        // Check if toast container exists, if not create it
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.style.position = 'fixed';
            toastContainer.style.top = '20px';
            toastContainer.style.right = '20px';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }
        
        const toast = document.createElement('div');
        toast.className = `toast show align-items-center text-white bg-${type} border-0`;
        toast.role = 'alert';
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        const toastBody = document.createElement('div');
        toastBody.className = 'd-flex';
        
        const toastContent = document.createElement('div');
        toastContent.className = 'toast-body';
        toastContent.textContent = message;
        
        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'btn-close btn-close-white me-2 m-auto';
        closeButton.setAttribute('data-bs-dismiss', 'toast');
        closeButton.setAttribute('aria-label', 'Close');
        
        toastBody.appendChild(toastContent);
        toastBody.appendChild(closeButton);
        toast.appendChild(toastBody);
        
        toastContainer.appendChild(toast);
        
        // Auto-remove toast after 5 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 150);
        }, 5000);
        
        // Close button functionality
        closeButton.addEventListener('click', () => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 150);
        });
    }
}

// Initialize AI features when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if AI features are enabled
    const aiEnabled = document.body.dataset.aiEnabled === 'true';
    
    if (aiEnabled) {
        // Initialize AI Chat if the chat container exists
        if (document.getElementById('ai-chat-container')) {
            window.aiChat = new AIChat();
        }
        
        // Initialize AI Task Assistant for task-related features
        window.aiTaskAssistant = new AITaskAssistant();
        
        // Load AI summary if on dashboard
        if (document.getElementById('ai-summary-container')) {
            loadAISummary();
        }
    }
});

// Function to load AI summary for the dashboard
async function loadAISummary() {
    const container = document.getElementById('ai-summary-container');
    if (!container) return;
    
    const projectId = container.dataset.projectId || null;
    const url = projectId 
        ? `/ai/api/ai/summary?project_id=${projectId}`
        : '/ai/api/ai/summary';
    
    try {
        const response = await fetch(url);
        if (response.ok) {
            const data = await response.json();
            container.innerHTML = `<div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">AI Project Summary</h5>
                    <button class="btn btn-sm btn-outline-primary" onclick="refreshAISummary()">
                        <i class="bi bi-arrow-clockwise"></i> Refresh
                    </button>
                </div>
                <div class="card-body">
                    <div class="ai-summary-content">
                        ${formatAISummary(data.summary)}
                    </div>
                </div>
            </div>`;
        } else {
            throw new Error('Failed to load AI summary');
        }
    } catch (error) {
        console.error('Error loading AI summary:', error);
        container.innerHTML = `
            <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle me-2"></i>
                Unable to load AI summary. Please try again later.
            </div>`;
    }
}

// Format the AI summary with proper line breaks and styling
function formatAISummary(summary) {
    if (!summary) return '<p>No summary available.</p>';
    
    // Split by double newlines to get sections
    const sections = summary.split('\n\n');
    let html = '';
    
    for (const section of sections) {
        if (!section.trim()) continue;
        
        // Check if this is a section header (starts with ===)
        if (section.startsWith('===')) {
            const title = section.replace(/^=+\s*|\s*=+$/g, '').trim();
            html += `<h6 class="mt-3 mb-2">${title}</h6>`;
        } 
        // Check if this is a list item (starts with - or *)
        else if (section.startsWith('- ') || section.startsWith('* ')) {
            const items = section.split('\n').filter(line => line.trim().startsWith('-') || line.trim().startsWith('*'));
            html += '<ul class="mb-2">';
            for (const item of items) {
                const text = item.replace(/^[-*]\s*/, '').trim();
                html += `<li>${text}</li>`;
            }
            html += '</ul>';
        } 
        // Regular paragraph
        else {
            html += `<p class="mb-2">${section.replace(/\n/g, '<br>')}</p>`;
        }
    }
    
    return html;
}

// Global function to refresh the AI summary
window.refreshAISummary = function() {
    const container = document.getElementById('ai-summary-container');
    if (container) {
        container.innerHTML = `
            <div class="text-center py-3">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Updating summary...</p>
            </div>`;
        loadAISummary();
    }
};

// Load AI suggestions for the user's dashboard
async function loadAISuggestions() {
    const container = document.getElementById('ai-suggestions');
    if (!container) return;
    
    try {
        const response = await fetch('/ai/api/ai/suggestions');
        if (response.ok) {
            const data = await response.json();
            if (data.suggestions && data.suggestions.length > 0) {
                let html = '<div class="list-group">';
                data.suggestions.forEach(suggestion => {
                    if (suggestion.trim()) {
                        html += `
                        <div class="list-group-item">
                            <div class="d-flex align-items-center">
                                <i class="bi bi-lightbulb text-warning me-2"></i>
                                <span>${suggestion}</span>
                            </div>
                        </div>`;
                    }
                });
                html += '</div>';
                container.innerHTML = html;
            } else {
                container.innerHTML = '<p class="text-muted">No suggestions available at the moment.</p>';
            }
        } else {
            throw new Error('Failed to load suggestions');
        }
    } catch (error) {
        console.error('Error loading AI suggestions:', error);
        container.innerHTML = `
            <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle me-2"></i>
                Unable to load suggestions. Please try again later.
            </div>`;
    }
}

// Load workload visualization
async function loadWorkloadVisualization() {
    const container = document.getElementById('workload-visualization');
    if (!container) return;
    
    const projectId = container.dataset.projectId || null;
    const url = projectId 
        ? `/ai/api/ai/workload?project_id=${projectId}`
        : '/ai/api/ai/workload';
    
    try {
        const response = await fetch(url);
        if (response.ok) {
            const workloadData = await response.json();
            
            if (workloadData.length === 0) {
                container.innerHTML = '<p class="text-muted">No workload data available.</p>';
                return;
            }
            
            // Create a bar chart using Chart.js if available
            if (typeof Chart !== 'undefined') {
                const ctx = document.createElement('canvas');
                container.innerHTML = '';
                container.appendChild(ctx);
                
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: workloadData.map(u => u.username),
                        datasets: [
                            {
                                label: 'High Priority',
                                data: workloadData.map(u => u.high_priority),
                                backgroundColor: 'rgba(220, 53, 69, 0.7)',
                                borderColor: 'rgba(220, 53, 69, 1)',
                                borderWidth: 1
                            },
                            {
                                label: 'Medium Priority',
                                data: workloadData.map(u => u.medium_priority),
                                backgroundColor: 'rgba(255, 193, 7, 0.7)',
                                borderColor: 'rgba(255, 193, 7, 1)',
                                borderWidth: 1
                            },
                            {
                                label: 'Low Priority',
                                data: workloadData.map(u => u.low_priority),
                                backgroundColor: 'rgba(40, 167, 69, 0.7)',
                                borderColor: 'rgba(40, 167, 69, 1)',
                                borderWidth: 1
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            x: {
                                stacked: true,
                                title: {
                                    display: true,
                                    text: 'Team Members'
                                }
                            },
                            y: {
                                stacked: true,
                                title: {
                                    display: true,
                                    text: 'Number of Tasks'
                                },
                                beginAtZero: true,
                                ticks: {
                                    stepSize: 1
                                }
                            }
                        },
                        plugins: {
                            title: {
                                display: true,
                                text: 'Workload Distribution by Priority'
                            },
                            tooltip: {
                                callbacks: {
                                    afterLabel: function(context) {
                                        const data = workloadData[context.dataIndex];
                                        return `Total: ${data.total_tasks} tasks`;
                                    }
                                }
                            }
                        }
                    }
                });
            } else {
                // Fallback to a simple table if Chart.js is not available
                let html = `
                <div class="table-responsive">
                    <table class="table table-sm table-hover">
                        <thead>
                            <tr>
                                <th>Team Member</th>
                                <th class="text-end">High</th>
                                <th class="text-end">Medium</th>
                                <th class="text-end">Low</th>
                                <th class="text-end">Total</th>
                            </tr>
                        </thead>
                        <tbody>`;
                
                workloadData.forEach(user => {
                    html += `
                        <tr>
                            <td>${user.username}</td>
                            <td class="text-end">${user.high_priority}</td>
                            <td class="text-end">${user.medium_priority}</td>
                            <td class="text-end">${user.low_priority}</td>
                            <td class="text-end fw-bold">${user.total_tasks}</td>
                        </tr>`;
                });
                
                html += `
                        </tbody>
                    </table>
                </div>`;
                
                container.innerHTML = html;
            }
        } else {
            throw new Error('Failed to load workload data');
        }
    } catch (error) {
        console.error('Error loading workload visualization:', error);
        container.innerHTML = `
            <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle me-2"></i>
                Unable to load workload data. Please try again later.
            </div>`;
    }
}

// Load all AI components when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // Load AI suggestions if the container exists
    if (document.getElementById('ai-suggestions')) {
        loadAISuggestions();
    }
    
    // Load workload visualization if the container exists
    if (document.getElementById('workload-visualization')) {
        loadWorkloadVisualization();
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
