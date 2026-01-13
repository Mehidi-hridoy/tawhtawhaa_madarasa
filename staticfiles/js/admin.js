document.addEventListener('DOMContentLoaded', function() {
    // Sidebar toggle
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('.admin-sidebar');
    const mainContent = document.querySelector('.admin-main');
    
    if (sidebarToggle && sidebar && mainContent) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
            mainContent.classList.toggle('shifted');
        });
    }
    
    // Auto-dismiss alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Update status badges with animation
    const statusBadges = document.querySelectorAll('.badge');
    statusBadges.forEach(badge => {
        if (badge.classList.contains('bg-danger') || badge.classList.contains('bg-warning')) {
            badge.classList.add('animate-pulse');
        }
    });
    
    // Confirm before marking as resolved
    const resolveButtons = document.querySelectorAll('.btn-outline-success');
    resolveButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to mark this message as resolved?')) {
                e.preventDefault();
            }
        });
    });
});

// Utility function for form submission with loading state
function submitFormWithLoading(formId) {
    const form = document.getElementById(formId);
    const submitBtn = form.querySelector('button[type="submit"]');
    
    if (form && submitBtn) {
        form.addEventListener('submit', function() {
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
            submitBtn.disabled = true;
        });
    }
}

// Auto-save functionality for response form
if (typeof autosave !== 'undefined' && autosave) {
    const responseForm = document.querySelector('form[method="post"]');
    if (responseForm) {
        let saveTimeout;
        
        responseForm.addEventListener('input', function() {
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(function() {
                // Trigger auto-save (you can implement AJAX save here)
                console.log('Auto-saving...');
            }, 3000);
        });
    }
}