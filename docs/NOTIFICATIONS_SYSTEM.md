# Real-Time Notifications System

## Overview

A comprehensive real-time notifications system using Socket.IO for instant notification delivery, with database persistence, user preferences, and a modern UI with bell icon and notification panel.

---

## 🎯 Features

### 1. Real-Time Notifications
- ✅ Socket.IO for instant delivery
- ✅ Push notifications to connected users
- ✅ Automatic reconnection handling
- ✅ Fallback to polling if needed

### 2. Notification Types
- ✅ Task assignments
- ✅ Task completions
- ✅ Overdue tasks
- ✅ Performance updates
- ✅ Comments on tasks
- ✅ Team updates
- ✅ Custom notifications

### 3. Database Persistence
- ✅ Store all notifications
- ✅ Track read/unread status
- ✅ Historical data
- ✅ Automatic cleanup

### 4. User Preferences
- ✅ Enable/disable notification types
- ✅ Email vs in-app delivery
- ✅ Quiet hours
- ✅ Notification frequency

### 5. UI Components
- ✅ Bell icon with badge
- ✅ Notification panel
- ✅ Toast notifications
- ✅ Animation effects
- ✅ Dark mode support

---

## 📊 Data Models

### Notification
```python
{
    'id': int,
    'user_id': int,
    'title': str,
    'message': str,
    'notification_type': str,
    'task_id': int,
    'project_id': int,
    'related_user_id': int,
    'is_read': bool,
    'read_at': datetime,
    'data': dict,
    'action_url': str,
    'created_at': datetime
}
```

### NotificationPreference
```python
{
    'user_id': int,
    'task_assigned': bool,
    'task_completed': bool,
    'task_overdue': bool,
    'comment_added': bool,
    'team_update': bool,
    'performance_update': bool,
    'email_notifications': bool,
    'push_notifications': bool,
    'in_app_notifications': bool,
    'quiet_hours_enabled': bool,
    'quiet_hours_start': str,
    'quiet_hours_end': str
}
```

---

## 📡 API Endpoints

### Get Notifications
```
GET /api/notifications?unread_only=false&limit=50&page=1&per_page=20
Authorization: Bearer <token>

Response: 200 OK
{
    "total": 150,
    "pages": 8,
    "current_page": 1,
    "notifications": [
        {
            "id": 1,
            "user_id": 5,
            "title": "📋 New Task Assigned",
            "message": "John assigned you: Complete Project Proposal",
            "notification_type": "task_assigned",
            "task_id": 42,
            "related_user_name": "john_doe",
            "is_read": false,
            "action_url": "/tasks/42",
            "created_at": "2024-05-15T14:30:00"
        }
    ]
}
```

### Get Unread Count
```
GET /api/notifications/unread-count
Authorization: Bearer <token>

Response: 200 OK
{
    "user_id": 5,
    "unread_count": 3
}
```

### Mark as Read
```
POST /api/notifications/<notification_id>/read
Authorization: Bearer <token>

Response: 200 OK
{
    "success": true,
    "notification_id": 1,
    "is_read": true
}
```

### Mark All as Read
```
POST /api/notifications/mark-all-read
Authorization: Bearer <token>

Response: 200 OK
{
    "success": true,
    "marked_count": 3
}
```

### Delete Notification
```
DELETE /api/notifications/<notification_id>
Authorization: Bearer <token>

Response: 200 OK
{
    "success": true
}
```

### Get Preferences
```
GET /api/notifications/preferences
Authorization: Bearer <token>

Response: 200 OK
{
    "user_id": 5,
    "task_assigned": true,
    "task_completed": true,
    "email_notifications": false,
    "push_notifications": true,
    ...
}
```

### Update Preferences
```
PUT /api/notifications/preferences
Authorization: Bearer <token>
Content-Type: application/json

{
    "task_assigned": true,
    "email_notifications": false,
    "quiet_hours_enabled": true,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "08:00"
}

Response: 200 OK
{
    "success": true,
    "preferences": {...}
}
```

### Get Statistics
```
GET /api/notifications/statistics
Authorization: Bearer <token>

Response: 200 OK
{
    "user_id": 5,
    "total_notifications": 150,
    "unread_notifications": 3,
    "read_notifications": 147,
    "by_type": {
        "task_assigned": 50,
        "task_completed": 40,
        "performance_update": 30,
        "comment_added": 30
    }
}
```

### Search Notifications
```
GET /api/notifications/search?q=proposal&type=task_assigned&start_date=2024-05-01
Authorization: Bearer <token>

Response: 200 OK
{
    "query": "proposal",
    "results": 5,
    "notifications": [...]
}
```

---

## 🔌 Socket.IO Events

### Client → Server

#### mark_notification_read
```javascript
socket.emit('mark_notification_read', {
    notification_id: 1
});
```

#### mark_all_read
```javascript
socket.emit('mark_all_read');
```

#### request_unread_count
```javascript
socket.emit('request_unread_count');
```

### Server → Client

#### connected
```javascript
socket.on('connected', (data) => {
    console.log('Connected. Unread:', data.unread_count);
});
```

#### new_notification
```javascript
socket.on('new_notification', (data) => {
    console.log('New notification:', data);
    // {
    //     id: 1,
    //     title: "📋 New Task Assigned",
    //     message: "...",
    //     type: "task_assigned",
    //     task_id: 42,
    //     action_url: "/tasks/42",
    //     created_at: "2024-05-15T14:30:00"
    // }
});
```

#### unread_count_update
```javascript
socket.on('unread_count_update', (data) => {
    console.log('Unread count:', data.unread_count);
});
```

#### notification_marked_read
```javascript
socket.on('notification_marked_read', (data) => {
    console.log('Marked read:', data.notification_id);
    console.log('Unread count:', data.unread_count);
});
```

---

## 🔧 Usage Examples

### Python - Create Notification

```python
from notifications_service import NotificationService, NotificationEvents

# Create notification
NotificationService.create_notification(
    user_id=5,
    title="📋 New Task Assigned",
    message="Complete Project Proposal",
    notification_type="task_assigned",
    task_id=42,
    related_user_id=3,
    action_url="/tasks/42"
)

# Or use predefined events
NotificationEvents.task_assigned(
    user_id=5,
    task_id=42,
    task_title="Complete Project Proposal",
    assigned_by_id=3
)
```

### Python - Emit Real-Time Notification

```python
from socket_events import emit_task_assigned

# Emit real-time notification
emit_task_assigned(
    user_id=5,
    task_id=42,
    task_title="Complete Project Proposal",
    assigned_by_id=3
)
```

### JavaScript - Listen for Notifications

```javascript
// Already initialized in notifications.js
notificationSystem.socket.on('new_notification', (data) => {
    console.log('New notification:', data);
});

// Get unread count
notificationSystem.updateUnreadCount();

// Mark as read
notificationSystem.markAsRead(notificationId);

// Mark all as read
notificationSystem.markAllAsRead();
```

---

## 🎨 Frontend Integration

### HTML Header
```html
<header>
    <!-- Bell Icon -->
    <button id="notification-bell" class="notification-bell">
        <svg><!-- Bell icon --></svg>
        <span class="notification-badge">3</span>
    </button>
    
    <!-- Notification Panel -->
    <div id="notification-panel" class="notification-panel">
        <div class="panel-header">
            <h3>Notifications</h3>
            <button id="mark-all-read-btn">Mark all as read</button>
            <button id="notification-panel-close">&times;</button>
        </div>
        <div id="notification-list" class="notification-list">
            <!-- Notifications loaded here -->
        </div>
    </div>
</header>
```

### CSS Styling
```css
/* Bell Icon */
.notification-bell {
    position: relative;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: transparent;
    border: none;
    cursor: pointer;
    transition: all 0.3s ease;
}

.notification-bell:hover {
    background: rgba(0, 0, 0, 0.1);
}

.notification-bell.has-unread {
    animation: bell-ring 0.5s ease;
}

/* Badge */
.notification-badge {
    position: absolute;
    top: -5px;
    right: -5px;
    background: #ef4444;
    color: white;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: bold;
}

/* Notification Panel */
.notification-panel {
    position: absolute;
    top: 100%;
    right: 0;
    width: 400px;
    max-height: 600px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
    display: none;
    flex-direction: column;
    z-index: 1000;
}

.notification-panel.open {
    display: flex;
}

/* Toast Notification */
.notification-toast {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    padding: 16px;
    display: flex;
    gap: 12px;
    max-width: 400px;
    opacity: 0;
    transform: translateY(100px);
    transition: all 0.3s ease;
    z-index: 2000;
}

.notification-toast.show {
    opacity: 1;
    transform: translateY(0);
}
```

---

## 🚀 Deployment

### Environment Setup
```env
# Socket.IO
SOCKETIO_ASYNC_MODE=threading
SOCKETIO_PING_TIMEOUT=60
SOCKETIO_PING_INTERVAL=25

# Notifications
NOTIFICATIONS_CLEANUP_DAYS=30
NOTIFICATIONS_BATCH_SIZE=50
```

### Database Migration
```bash
flask db migrate -m "Add notifications tables"
flask db upgrade
```

### Initialize Templates
```python
from notifications_models import NotificationTemplate

templates = [
    NotificationTemplate(
        template_key='task_assigned',
        title_template='📋 {assigned_by} assigned you a task',
        message_template='{assigned_by} assigned: {task_title}',
        notification_type='task_assigned',
        variables=['assigned_by', 'task_title']
    ),
    # ... more templates
]

for template in templates:
    db.session.add(template)
db.session.commit()
```

---

## 📊 Performance Optimization

### Database Indexes
- `idx_notification_user_id` - Fast user lookups
- `idx_notification_is_read` - Fast unread queries
- `idx_notification_created_at` - Fast date queries
- `idx_notification_user_read` - Combined index

### Caching
- Cache unread count (5 min TTL)
- Cache notification preferences (1 hour TTL)
- Cache notification templates (1 day TTL)

### Cleanup
- Auto-delete notifications older than 30 days
- Archive old notifications to separate table
- Batch delete for performance

---

## 🔐 Security

- ✅ User can only see own notifications
- ✅ Verify user ownership before operations
- ✅ CSRF protection on API endpoints
- ✅ Rate limiting on notification creation
- ✅ Audit logging for sensitive operations

---

**Version**: 1.0
**Last Updated**: May 2024
**Status**: Production Ready
