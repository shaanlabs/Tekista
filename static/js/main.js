// TaskManager - Interactive JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeAnimations();
    initializeFormValidation();
    initializeTooltips();
    initializeProgressBars();
    initializeTaskFilters();
    initializeApiIntegration();
    initializeNotifications();
});

// Animation and UI Enhancements
function initializeAnimations() {
    // Fade in animation for cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Form Validation and Enhancement
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // Real-time validation
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    validateField(this);
                }
            });
        });

        // Form submission with loading state
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                showLoadingState(submitBtn);
            }
        });
    });
}

function validateField(field) {
    const value = field.value.trim();
    const fieldType = field.type;
    const isRequired = field.hasAttribute('required');
    
    let isValid = true;
    let errorMessage = '';

    // Required field validation
    if (isRequired && !value) {
        isValid = false;
        errorMessage = 'This field is required';
    }
    
    // Email validation
    if (fieldType === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address';
        }
    }
    
    // Password validation
    if (fieldType === 'password' && value) {
        if (value.length < 6) {
            isValid = false;
            errorMessage = 'Password must be at least 6 characters long';
        }
    }
    
    // Username validation
    if (field.name === 'username' && value) {
        if (value.length < 3) {
            isValid = false;
            errorMessage = 'Username must be at least 3 characters long';
        }
    }

    // Update field appearance
    if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
        removeFieldError(field);
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
        showFieldError(field, errorMessage);
    }
    
    return isValid;
}

function showFieldError(field, message) {
    removeFieldError(field);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

function removeFieldError(field) {
    const existingError = field.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
}

function showLoadingState(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="loading"></span> Processing...';
    button.disabled = true;
    
    // Re-enable after 3 seconds (fallback)
    setTimeout(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    }, 3000);
}

// Tooltip and Popover Enhancement
function initializeTooltips() {
    // Initialize Bootstrap tooltips if available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Custom tooltips for status and priority badges
    const badges = document.querySelectorAll('.badge');
    badges.forEach(badge => {
        badge.addEventListener('mouseenter', function() {
            showCustomTooltip(this, getBadgeTooltipText(this));
        });
        
        badge.addEventListener('mouseleave', function() {
            hideCustomTooltip();
        });
    });
}

function getBadgeTooltipText(badge) {
    if (badge.classList.contains('badge-status-todo')) {
        return 'Task is not yet started';
    } else if (badge.classList.contains('badge-status-in-progress')) {
        return 'Task is currently being worked on';
    } else if (badge.classList.contains('badge-status-done')) {
        return 'Task has been completed';
    } else if (badge.classList.contains('badge-priority-high')) {
        return 'High priority - should be completed first';
    } else if (badge.classList.contains('badge-priority-normal')) {
        return 'Normal priority - standard timeline';
    } else if (badge.classList.contains('badge-priority-low')) {
        return 'Low priority - can be completed later';
    }
    return '';
}

function showCustomTooltip(element, text) {
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
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
}

function hideCustomTooltip() {
    const tooltip = document.querySelector('.custom-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Progress Bar Animation
function initializeProgressBars() {
    const progressBars = document.querySelectorAll('.project-progress-bar');
    
    progressBars.forEach(bar => {
        const width = bar.style.width || bar.getAttribute('data-width') || '0%';
        bar.style.width = '0%';
        
        setTimeout(() => {
            bar.style.transition = 'width 1s ease-in-out';
            bar.style.width = width;
        }, 200);
    });
}

// Task Filtering and Search
function initializeTaskFilters() {
    const filterInputs = document.querySelectorAll('.task-filter');
    const taskCards = document.querySelectorAll('.task-card');
    
    filterInputs.forEach(input => {
        input.addEventListener('input', function() {
            const filterValue = this.value.toLowerCase();
            const filterType = this.getAttribute('data-filter');
            
            taskCards.forEach(card => {
                const shouldShow = filterTask(card, filterValue, filterType);
                card.style.display = shouldShow ? 'block' : 'none';
            });
        });
    });
}

function filterTask(card, filterValue, filterType) {
    if (!filterValue) return true;
    
    const text = card.textContent.toLowerCase();
    return text.includes(filterValue);
}

// API Integration
function initializeApiIntegration() {
    // Auto-refresh data every 30 seconds
    setInterval(refreshData, 30000);
    
    // Handle API token expiration
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-api-action]')) {
            e.preventDefault();
            handleApiAction(e.target);
        }
    });
}

function refreshData() {
    // Only refresh if user is on a data-heavy page
    if (window.location.pathname.includes('/projects') || window.location.pathname.includes('/tasks')) {
        fetch(window.location.href, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.text())
        .then(html => {
            // Update only the content area
            const parser = new DOMParser();
            const newDoc = parser.parseFromString(html, 'text/html');
            const newContent = newDoc.querySelector('.container');
            const currentContent = document.querySelector('.container');
            
            if (newContent && currentContent) {
                currentContent.innerHTML = newContent.innerHTML;
                initializeAnimations(); // Re-initialize animations
            }
        })
        .catch(error => console.log('Auto-refresh failed:', error));
    }
}

function handleApiAction(element) {
    const action = element.getAttribute('data-api-action');
    const url = element.getAttribute('data-api-url');
    
    if (!url) return;
    
    showLoadingState(element);
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Action completed successfully!', 'success');
            // Refresh the page or update specific elements
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification(data.message || 'Action failed', 'error');
        }
    })
    .catch(error => {
        showNotification('Network error occurred', 'error');
        console.error('API Error:', error);
    });
}

// Notification System
function initializeNotifications() {
    // Create notification container
    const notificationContainer = document.createElement('div');
    notificationContainer.id = 'notification-container';
    notificationContainer.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        max-width: 400px;
    `;
    document.body.appendChild(notificationContainer);
}

function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.style.cssText = `
        margin-bottom: 10px;
        animation: slideInRight 0.3s ease;
    `;
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.getElementById('notification-container').appendChild(notification);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }
    }, duration);
}

// Add CSS for notification animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);

// Utility Functions
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

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export functions for global use
window.TaskManager = {
    showNotification,
    showLoadingState,
    validateField,
    refreshData
};
