/**
 * Notifications System
 * Handles real-time notifications via Socket.IO
 */

class NotificationSystem {
    constructor() {
        this.socket = null;
        this.unreadCount = 0;
        this.notifications = [];
        this.init();
    }
    
    /**
     * Initialize Socket.IO connection
     */
    init() {
        // Connect to Socket.IO
        this.socket = io();
        
        // Connection events
        this.socket.on('connect', () => {
            console.log('Connected to notification server');
            this.updateUnreadCount();
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from notification server');
        });
        
        // Notification events
        this.socket.on('connected', (data) => {
            this.unreadCount = data.unread_count;
            this.updateBellIcon();
        });
        
        this.socket.on('new_notification', (data) => {
            this.handleNewNotification(data);
        });
        
        this.socket.on('unread_count_update', (data) => {
            this.unreadCount = data.unread_count;
            this.updateBellIcon();
        });
        
        this.socket.on('notification_marked_read', (data) => {
            this.unreadCount = data.unread_count;
            this.updateBellIcon();
        });
        
        this.socket.on('all_notifications_marked_read', (data) => {
            this.unreadCount = 0;
            this.updateBellIcon();
        });
        
        this.setupEventListeners();
    }
    
    /**
     * Setup DOM event listeners
     */
    setupEventListeners() {
        // Bell icon click
        const bellIcon = document.getElementById('notification-bell');
        if (bellIcon) {
            bellIcon.addEventListener('click', () => this.toggleNotificationPanel());
        }
        
        // Mark all as read
        const markAllReadBtn = document.getElementById('mark-all-read-btn');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', () => this.markAllAsRead());
        }
        
        // Close notification panel
        const closeBtn = document.getElementById('notification-panel-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeNotificationPanel());
        }
    }
    
    /**
     * Handle new notification
     */
    handleNewNotification(data) {
        console.log('New notification:', data);
        
        // Add to notifications list
        this.notifications.unshift(data);
        
        // Update unread count
        this.unreadCount++;
        this.updateBellIcon();
        
        // Show toast notification
        this.showToast(data);
        
        // Update notification panel if open
        if (document.getElementById('notification-panel').classList.contains('open')) {
            this.updateNotificationPanel();
        }
        
        // Play sound
        this.playNotificationSound();
    }
    
    /**
     * Show toast notification
     */
    showToast(data) {
        const toast = document.createElement('div');
        toast.className = 'notification-toast';
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-title">${data.title}</div>
                <div class="toast-message">${data.message}</div>
            </div>
            <button class="toast-close">&times;</button>
        `;
        
        // Add to DOM
        const container = document.getElementById('toast-container') || document.body;
        container.appendChild(toast);
        
        // Animate in
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Close button
        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        });
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
        
        // Click to navigate
        toast.addEventListener('click', (e) => {
            if (e.target.classList.contains('toast-close')) return;
            if (data.action_url) {
                window.location.href = data.action_url;
            }
        });
    }
    
    /**
     * Update bell icon with unread count
     */
    updateBellIcon() {
        const bellIcon = document.getElementById('notification-bell');
        if (!bellIcon) return;
        
        // Update badge
        let badge = bellIcon.querySelector('.notification-badge');
        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'notification-badge';
            bellIcon.appendChild(badge);
        }
        
        if (this.unreadCount > 0) {
            badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
            badge.style.display = 'flex';
            bellIcon.classList.add('has-unread');
        } else {
            badge.style.display = 'none';
            bellIcon.classList.remove('has-unread');
        }
    }
    
    /**
     * Toggle notification panel
     */
    toggleNotificationPanel() {
        const panel = document.getElementById('notification-panel');
        if (!panel) return;
        
        if (panel.classList.contains('open')) {
            this.closeNotificationPanel();
        } else {
            this.openNotificationPanel();
        }
    }
    
    /**
     * Open notification panel
     */
    openNotificationPanel() {
        const panel = document.getElementById('notification-panel');
        if (!panel) return;
        
        panel.classList.add('open');
        this.loadNotifications();
    }
    
    /**
     * Close notification panel
     */
    closeNotificationPanel() {
        const panel = document.getElementById('notification-panel');
        if (!panel) return;
        
        panel.classList.remove('open');
    }
    
    /**
     * Load notifications from API
     */
    async loadNotifications() {
        try {
            const response = await fetch('/api/notifications?limit=20', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });
            
            const data = await response.json();
            this.notifications = data.notifications || [];
            this.updateNotificationPanel();
        } catch (error) {
            console.error('Error loading notifications:', error);
        }
    }
    
    /**
     * Update notification panel display
     */
    updateNotificationPanel() {
        const list = document.getElementById('notification-list');
        if (!list) return;
        
        if (this.notifications.length === 0) {
            list.innerHTML = '<div class="empty-state">No notifications</div>';
            return;
        }
        
        list.innerHTML = this.notifications.map(notif => `
            <div class="notification-item ${notif.is_read ? 'read' : 'unread'}">
                <div class="notification-content">
                    <div class="notification-title">${notif.title}</div>
                    <div class="notification-message">${notif.message}</div>
                    <div class="notification-time">${this.formatTime(notif.created_at)}</div>
                </div>
                <div class="notification-actions">
                    ${!notif.is_read ? `
                        <button class="mark-read-btn" onclick="notificationSystem.markAsRead(${notif.id})">
                            ✓
                        </button>
                    ` : ''}
                    <button class="delete-btn" onclick="notificationSystem.deleteNotification(${notif.id})">
                        ✕
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    /**
     * Mark notification as read
     */
    async markAsRead(notificationId) {
        try {
            const response = await fetch(`/api/notifications/${notificationId}/read`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });
            
            if (response.ok) {
                this.loadNotifications();
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }
    
    /**
     * Mark all notifications as read
     */
    async markAllAsRead() {
        try {
            const response = await fetch('/api/notifications/mark-all-read', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });
            
            if (response.ok) {
                this.socket.emit('mark_all_read');
                this.loadNotifications();
            }
        } catch (error) {
            console.error('Error marking all as read:', error);
        }
    }
    
    /**
     * Delete notification
     */
    async deleteNotification(notificationId) {
        try {
            const response = await fetch(`/api/notifications/${notificationId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });
            
            if (response.ok) {
                this.loadNotifications();
            }
        } catch (error) {
            console.error('Error deleting notification:', error);
        }
    }
    
    /**
     * Update unread count
     */
    async updateUnreadCount() {
        try {
            const response = await fetch('/api/notifications/unread-count', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });
            
            const data = await response.json();
            this.unreadCount = data.unread_count;
            this.updateBellIcon();
        } catch (error) {
            console.error('Error updating unread count:', error);
        }
    }
    
    /**
     * Play notification sound
     */
    playNotificationSound() {
        try {
            const audio = new Audio('/static/sounds/notification.mp3');
            audio.volume = 0.5;
            audio.play().catch(() => {
                // Audio play failed (likely due to browser policy)
            });
        } catch (error) {
            // Sound not available
        }
    }
    
    /**
     * Format time for display
     */
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        
        return date.toLocaleDateString();
    }
    
    /**
     * Get authentication token
     */
    getToken() {
        // Get token from localStorage or cookie
        return localStorage.getItem('token') || document.querySelector('meta[name="csrf-token"]')?.content || '';
    }
}

// Initialize notification system when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.notificationSystem = new NotificationSystem();
});
