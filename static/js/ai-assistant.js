/**
 * AI Assistant Chat Interface
 * Floating chat bubble for natural language queries
 */

class AIAssistant {
    constructor() {
        this.isOpen = false;
        this.messages = [];
        this.suggestions = [];
        this.init();
    }
    
    /**
     * Initialize assistant
     */
    async init() {
        this.createUI();
        this.setupEventListeners();
        await this.loadSuggestions();
    }
    
    /**
     * Create UI elements
     */
    createUI() {
        // Create container
        const container = document.createElement('div');
        container.id = 'ai-assistant-container';
        container.className = 'ai-assistant-container';
        
        // Create chat bubble button
        const bubble = document.createElement('button');
        bubble.id = 'ai-assistant-bubble';
        bubble.className = 'ai-assistant-bubble';
        bubble.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span class="bubble-badge" style="display: none;">1</span>
        `;
        
        // Create chat panel
        const panel = document.createElement('div');
        panel.id = 'ai-assistant-panel';
        panel.className = 'ai-assistant-panel';
        panel.innerHTML = `
            <div class="assistant-header">
                <div class="assistant-title">
                    <span class="assistant-icon">🤖</span>
                    <span>AI Assistant</span>
                </div>
                <button class="assistant-close-btn">&times;</button>
            </div>
            
            <div class="assistant-messages" id="assistant-messages">
                <div class="assistant-welcome">
                    <div class="welcome-icon">👋</div>
                    <div class="welcome-text">Hi! I'm your AI Assistant. Ask me anything about your tasks, performance, or skills.</div>
                </div>
            </div>
            
            <div class="assistant-suggestions" id="assistant-suggestions">
                <!-- Suggestions loaded here -->
            </div>
            
            <div class="assistant-input-area">
                <input 
                    type="text" 
                    id="assistant-input" 
                    class="assistant-input" 
                    placeholder="Ask me anything..."
                    autocomplete="off"
                >
                <button class="assistant-send-btn" id="assistant-send-btn">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <line x1="22" y1="2" x2="11" y2="13"></line>
                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                </button>
            </div>
        `;
        
        container.appendChild(bubble);
        container.appendChild(panel);
        document.body.appendChild(container);
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Bubble click
        document.getElementById('ai-assistant-bubble').addEventListener('click', () => {
            this.togglePanel();
        });
        
        // Close button
        document.querySelector('.assistant-close-btn').addEventListener('click', () => {
            this.closePanel();
        });
        
        // Send button
        document.getElementById('assistant-send-btn').addEventListener('click', () => {
            this.sendMessage();
        });
        
        // Input enter key
        document.getElementById('assistant-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        
        // Suggestion clicks
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('suggestion-chip')) {
                this.sendMessage(e.target.textContent);
            }
        });
    }
    
    /**
     * Toggle chat panel
     */
    togglePanel() {
        if (this.isOpen) {
            this.closePanel();
        } else {
            this.openPanel();
        }
    }
    
    /**
     * Open chat panel
     */
    openPanel() {
        const panel = document.getElementById('ai-assistant-panel');
        const bubble = document.getElementById('ai-assistant-bubble');
        
        panel.classList.add('open');
        bubble.classList.add('active');
        this.isOpen = true;
        
        // Focus input
        setTimeout(() => {
            document.getElementById('assistant-input').focus();
        }, 300);
    }
    
    /**
     * Close chat panel
     */
    closePanel() {
        const panel = document.getElementById('ai-assistant-panel');
        const bubble = document.getElementById('ai-assistant-bubble');
        
        panel.classList.remove('open');
        bubble.classList.remove('active');
        this.isOpen = false;
    }
    
    /**
     * Load suggestions
     */
    async loadSuggestions() {
        try {
            const response = await fetch('/api/assistant/suggestions', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });
            
            const data = await response.json();
            this.suggestions = data.suggestions || [];
            this.renderSuggestions();
        } catch (error) {
            console.error('Error loading suggestions:', error);
        }
    }
    
    /**
     * Render suggestions
     */
    renderSuggestions() {
        const container = document.getElementById('assistant-suggestions');
        if (!container) return;
        
        container.innerHTML = `
            <div class="suggestions-label">Quick suggestions:</div>
            <div class="suggestions-grid">
                ${this.suggestions.slice(0, 4).map(suggestion => `
                    <button class="suggestion-chip">${suggestion}</button>
                `).join('')}
            </div>
        `;
    }
    
    /**
     * Send message
     */
    async sendMessage(messageText = null) {
        const input = document.getElementById('assistant-input');
        const message = messageText || input.value.trim();
        
        if (!message) return;
        
        // Clear input
        input.value = '';
        
        // Add user message to UI
        this.addMessage(message, 'user');
        
        // Show loading
        this.addMessage('Thinking...', 'assistant', true);
        
        try {
            // Send query to backend
            const response = await fetch('/api/assistant/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getToken()}`
                },
                body: JSON.stringify({ query: message })
            });
            
            const data = await response.json();
            
            // Remove loading message
            this.removeLastMessage();
            
            // Add assistant response
            this.addMessage(data.message, 'assistant');
            
            // Add data visualization if available
            if (data.data && Object.keys(data.data).length > 0) {
                this.renderData(data.category, data.data);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.removeLastMessage();
            this.addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
        }
    }
    
    /**
     * Add message to chat
     */
    addMessage(text, sender, isLoading = false) {
        const messagesContainer = document.getElementById('assistant-messages');
        
        // Remove welcome message on first message
        const welcome = messagesContainer.querySelector('.assistant-welcome');
        if (welcome && this.messages.length === 0) {
            welcome.remove();
        }
        
        const messageEl = document.createElement('div');
        messageEl.className = `assistant-message ${sender}`;
        
        if (isLoading) {
            messageEl.innerHTML = `
                <div class="message-content">
                    <div class="loading-dots">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            `;
        } else {
            messageEl.innerHTML = `
                <div class="message-content">${this.escapeHtml(text)}</div>
            `;
        }
        
        messagesContainer.appendChild(messageEl);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        this.messages.push({ text, sender, timestamp: new Date() });
    }
    
    /**
     * Remove last message
     */
    removeLastMessage() {
        const messagesContainer = document.getElementById('assistant-messages');
        const lastMessage = messagesContainer.lastElementChild;
        if (lastMessage) {
            lastMessage.remove();
            this.messages.pop();
        }
    }
    
    /**
     * Render data based on category
     */
    renderData(category, data) {
        const messagesContainer = document.getElementById('assistant-messages');
        
        let html = '';
        
        if (category === 'pending_tasks' || category === 'completed_tasks') {
            if (data.tasks && data.tasks.length > 0) {
                html = `
                    <div class="data-container tasks-list">
                        ${data.tasks.map(task => `
                            <div class="task-item">
                                <div class="task-title">${this.escapeHtml(task.title)}</div>
                                <div class="task-meta">
                                    <span class="priority priority-${task.priority}">${task.priority}</span>
                                    ${task.due_date ? `<span class="due-date">${task.due_date}</span>` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
            }
        } else if (category === 'performance') {
            if (data.performance_score) {
                html = `
                    <div class="data-container performance-card">
                        <div class="perf-score">
                            <div class="score-value">${data.performance_score.toFixed(1)}</div>
                            <div class="score-label">/100</div>
                        </div>
                        <div class="perf-metrics">
                            <div class="metric">
                                <span class="metric-label">On-Time</span>
                                <span class="metric-value">${(data.on_time_ratio * 100).toFixed(0)}%</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Skill Match</span>
                                <span class="metric-value">${(data.skill_accuracy * 100).toFixed(0)}%</span>
                            </div>
                        </div>
                    </div>
                `;
            }
        } else if (category === 'skills') {
            if (data.top_skills && data.top_skills.length > 0) {
                html = `
                    <div class="data-container skills-list">
                        ${data.top_skills.map(skill => `
                            <div class="skill-item">
                                <div class="skill-name">${this.escapeHtml(skill.skill)}</div>
                                <div class="skill-bar">
                                    <div class="skill-fill" style="width: ${skill.proficiency}%"></div>
                                </div>
                                <div class="skill-level">${skill.level}</div>
                            </div>
                        `).join('')}
                    </div>
                `;
            }
        } else if (category === 'assign_task') {
            if (data.tasks && data.tasks.length > 0) {
                html = `
                    <div class="data-container tasks-list">
                        ${data.tasks.map(task => `
                            <div class="task-item">
                                <div class="task-title">${this.escapeHtml(task.title)}</div>
                                <div class="task-meta">
                                    <span class="score">Match: ${task.score.toFixed(0)}%</span>
                                    <span class="difficulty">Difficulty: ${task.difficulty}/10</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
            }
        } else if (category === 'help') {
            if (data.commands) {
                html = `
                    <div class="data-container commands-list">
                        ${data.commands.map(cmd => `
                            <div class="command-item">${this.escapeHtml(cmd)}</div>
                        `).join('')}
                    </div>
                `;
            }
        }
        
        if (html) {
            const dataEl = document.createElement('div');
            dataEl.className = 'assistant-message assistant data-message';
            dataEl.innerHTML = html;
            messagesContainer.appendChild(dataEl);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }
    
    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Get authentication token
     */
    getToken() {
        return localStorage.getItem('token') || document.querySelector('meta[name="csrf-token"]')?.content || '';
    }
}

// Initialize assistant when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.aiAssistant = new AIAssistant();
});
