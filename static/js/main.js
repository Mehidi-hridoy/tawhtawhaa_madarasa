// Navbar Scroll Effect
window.addEventListener('scroll', function() {
    const navbar = document.getElementById('mainNavbar');
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
    
    // Back to top button
    const backToTop = document.getElementById('backToTop');
    if (window.scrollY > 300) {
        backToTop.classList.add('show');
    } else {
        backToTop.classList.remove('show');
    }
});

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Mega dropdown hover effect
    const megaDropdown = document.querySelector('.mega-dropdown');
    if (megaDropdown) {
        const dropdownMenu = megaDropdown.querySelector('.dropdown-menu');
        
        megaDropdown.addEventListener('mouseenter', function() {
            const megaMenu = new bootstrap.Dropdown(this);
            megaMenu.show();
        });
        
        megaDropdown.addEventListener('mouseleave', function() {
            setTimeout(() => {
                const megaMenu = new bootstrap.Dropdown(this);
                megaMenu.hide();
            }, 300);
        });
        
        dropdownMenu.addEventListener('mouseenter', function() {
            clearTimeout(window.megaMenuTimeout);
        });
        
        dropdownMenu.addEventListener('mouseleave', function() {
            window.megaMenuTimeout = setTimeout(() => {
                const megaMenu = new bootstrap.Dropdown(megaDropdown);
                megaMenu.hide();
            }, 100);
        });
    }
    
    // Animate numbers on scroll
    function animateNumbers() {
        const statNumbers = document.querySelectorAll('.stat-number');
        statNumbers.forEach(stat => {
            const value = parseInt(stat.textContent);
            let start = 0;
            const duration = 2000;
            const increment = value / (duration / 16);
            
            const timer = setInterval(() => {
                start += increment;
                if (start >= value) {
                    stat.textContent = value + '+';
                    clearInterval(timer);
                } else {
                    stat.textContent = Math.floor(start) + '+';
                }
            }, 16);
        });
    }
    
    // Check if element is in viewport
    function isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
    
    // Intersection Observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                
                // If element has stat numbers, animate them
                if (entry.target.querySelector('.stat-number')) {
                    animateNumbers();
                }
            }
        });
    }, observerOptions);
    
    // Observe elements with animation
    document.querySelectorAll('.course-card, .category-card, .testimonial-card').forEach(el => {
        observer.observe(el);
    });
    
    // Back to top functionality
    const backToTop = document.getElementById('backToTop');
    if (backToTop) {
        backToTop.addEventListener('click', function(e) {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    // Form validation enhancement
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="loading"></span> Processing...';
                submitBtn.disabled = true;
            }
        });
    });
    
    // Course card hover effect
    const courseCards = document.querySelectorAll('.course-card');
    courseCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.zIndex = '10';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.zIndex = '1';
        });
    });
});

// Parallax effect for hero section
window.addEventListener('scroll', function() {
    const hero = document.querySelector('.hero-section');
    if (hero) {
        const scrolled = window.pageYOffset;
        const rate = scrolled * -0.5;
        hero.style.transform = 'translateY(' + rate + 'px)';
    }
});

// Add smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        if (href !== '#') {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                window.scrollTo({
                    top: target.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        }
    });
});