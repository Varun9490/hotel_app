document.addEventListener('DOMContentLoaded', function() {

    // --- Sidebar Management ---
    class SidebarManager {
        constructor() {
            this.sidebar = document.getElementById('sidebar');
            this.mainContent = document.getElementById('mainContent');
            this.sidebarToggle = document.getElementById('sidebarToggle');
            this.sidebarOverlay = document.getElementById('sidebarOverlay');
            this.isMobile = window.innerWidth <= 768;

            this.init();
        }

        init() {
            this.sidebarToggle.addEventListener('click', () => this.toggleSidebar());
            this.sidebarOverlay.addEventListener('click', () => this.closeMobileSidebar());
            window.addEventListener('resize', () => this.handleResize());

            // Close sidebar on mobile when a nav link is clicked
            document.querySelectorAll('.sidebar .nav-link').forEach(link => {
                link.addEventListener('click', () => {
                    if (this.isMobile) this.closeMobileSidebar();
                });
            });
        }

        toggleSidebar() {
            if (this.isMobile) {
                this.sidebar.classList.toggle('show');
                this.sidebarOverlay.classList.toggle('show');
            } else {
                this.sidebar.classList.toggle('collapsed');
                this.mainContent.classList.toggle('expanded');
            }
        }

        closeMobileSidebar() {
            this.sidebar.classList.remove('show');
            this.sidebarOverlay.classList.remove('show');
        }

        handleResize() {
            const newIsMobile = window.innerWidth <= 768;
            if (newIsMobile !== this.isMobile) {
                this.isMobile = newIsMobile;
                // Reset sidebar state on mode change
                this.sidebar.classList.remove('show', 'collapsed');
                this.mainContent.classList.remove('expanded');
                this.sidebarOverlay.classList.remove('show');
            }
        }
    }

    // --- Toast Notification System ---
    class ToastManager {
        constructor() {
            this.container = document.getElementById('toastContainer');
        }

        show(message, type = 'info', duration = 5000) {
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;

            const icons = {
                success: 'fa-check-circle',
                error: 'fa-exclamation-circle',
                warning: 'fa-exclamation-triangle',
                info: 'fa-info-circle'
            };

            const titles = {
                success: 'Success',
                error: 'Error',
                warning: 'Warning',
                info: 'Info'
            };

            toast.innerHTML = `
                <div class="toast-header">
                    <i class="fas ${icons[type]} icon"></i>
                    <strong class="title">${titles[type]}</strong>
                    <button class="toast-close-btn">&times;</button>
                </div>
                <div class="toast-body">${message}</div>
            `;

            this.container.appendChild(toast);

            // Animate in
            setTimeout(() => toast.classList.add('show'), 100);

            const close = () => {
                toast.classList.remove('show');
                toast.addEventListener('transitionend', () => toast.remove(), { once: true });
            };

            toast.querySelector('.toast-close-btn').addEventListener('click', close);

            if (duration) {
                setTimeout(close, duration);
            }
        }

        success(message, duration) { this.show(message, 'success', duration); }
        error(message, duration) { this.show(message, 'error', duration); }
        warning(message, duration) { this.show(message, 'warning', duration); }
        info(message, duration) { this.show(message, 'info', duration); }
    }

    // --- Loading Indicator for Buttons ---
    class LoadingManager {
        show(element, text = 'Loading...') {
            if (element) {
                element.dataset.originalContent = element.innerHTML;
                element.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${text}`;
                element.disabled = true;
            }
        }

        hide(element) {
            if (element && element.dataset.originalContent) {
                element.innerHTML = element.dataset.originalContent;
                element.disabled = false;
                delete element.dataset.originalContent;
            }
        }
    }

    // --- Dropdown Menu ---
    class DropdownManager {
        constructor(toggleId, menuId) {
            this.toggle = document.getElementById(toggleId);
            this.menu = document.getElementById(menuId);
            this.container = this.toggle.parentElement;

            if (this.toggle && this.menu) {
                this.init();
            }
        }

        init() {
            this.toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                this.container.classList.toggle('open');
            });
            
            document.addEventListener('click', (e) => {
                if (!this.container.contains(e.target)) {
                    this.container.classList.remove('open');
                }
            });
        }
    }


    // --- Initialization ---
    const sidebarManager = new SidebarManager();
    const toastManager = new ToastManager();
    const loadingManager = new LoadingManager();
    const userDropdown = new DropdownManager('userProfileToggle', 'userProfileMenu');

    // --- Make managers globally available ---
    window.showToast = (message, type, duration) => toastManager.show(message, type, duration);
    window.showLoading = (element, text) => loadingManager.show(element, text);
    window.hideLoading = (element) => loadingManager.hide(element);

    // --- Django Messages Handling (from original template) ---
    // This part requires the Django template variables to be present in the HTML.
    // Example: <script id="django-messages" type="application/json">...</script>
    // For this example, we assume it's handled in the HTML template directly.
    {% if messages %}
        {% for message in messages %}
            toastManager.show('{{ message|escapejs }}', '{{ message.tags }}');
        {% endfor %}
    {% endif %}

    // --- Enhanced Form Handling ---
    document.querySelectorAll('form[data-toast="true"]').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                loadingManager.show(submitBtn, 'Processing...');
            }
        });
    });
});