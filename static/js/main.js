// Cleanifi - Premium UI JavaScript
console.log('Cleanifi - AI Data Cleaning Tool');

// ===== Premium Scroll-Triggered Animations =====
document.addEventListener('DOMContentLoaded', () => {
    initScrollAnimations();
    initRippleEffect();
    initSmoothHover();
    initParallaxEffect();
    initWaterRipples();
    initFloatingEffect();
});

// Interactive Floating Effect (Repurposed from Space)
function initFloatingEffect() {
    // Parallax & Interactive Floating for UI elements
    window.addEventListener('mousemove', (e) => {
        const x = (e.clientX / window.innerWidth - 0.5);
        const y = (e.clientY / window.innerHeight - 0.5);

        // Gently Tilt the Login Box as if floating on water
        const authBox = document.querySelector('.auth-box');
        if (authBox) {
            const moveX = x * 20;
            const moveY = y * 20;
            const rotateX = -y * 10;
            const rotateY = x * 10;
            authBox.style.transform = `translate(${moveX}px, ${moveY}px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        }
    });
}

// Water Ripple Effect - Simulate throwing stone in ocean
function initWaterRipples() {
    const container = document.getElementById('ripple-container');
    if (!container) return;

    window.addEventListener('click', (e) => {
        // Only spawn ripples if clicking on background or non-interactive areas
        // or just spawn everywhere for maximum effect as requested
        createRipple(e.clientX, e.clientY);

        // Spawn secondary ripples for "stone" feel
        setTimeout(() => createRipple(e.clientX, e.clientY), 150);
        setTimeout(() => createRipple(e.clientX, e.clientY), 300);
    });

    function createRipple(x, y) {
        const ripple = document.createElement('div');
        ripple.className = 'water-ripple';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';

        container.appendChild(ripple);

        // Clean up after animation
        setTimeout(() => ripple.remove(), 1500);
    }
}

// Intersection Observer for scroll-triggered animations
function initScrollAnimations() {
    const animatedElements = document.querySelectorAll(
        '.step-section, .stat-card, .info-card, .missing-item, .rename-item'
    );

    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                // Add staggered delay based on element index
                setTimeout(() => {
                    entry.target.classList.add('animate-in');
                }, index * 100);
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    animatedElements.forEach(el => {
        el.classList.add('scroll-animate');
        observer.observe(el);
    });
}

// Enhanced ripple effect for buttons
function initRippleEffect() {
    document.querySelectorAll('.btn, .ripple').forEach(btn => {
        btn.addEventListener('click', function (e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const ripple = document.createElement('span');
            ripple.className = 'ripple-effect';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';

            this.appendChild(ripple);

            setTimeout(() => ripple.remove(), 600);
        });
    });
}

// Smooth hover tracking for cards
function initSmoothHover() {
    document.querySelectorAll('.step-section, .stat-card, .glass-card').forEach(card => {
        card.addEventListener('mousemove', function (e) {
            const rect = this.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width;
            const y = (e.clientY - rect.top) / rect.height;

            const tiltX = (y - 0.5) * 5;
            const tiltY = (x - 0.5) * -5;

            this.style.transform = `perspective(1000px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) translateY(-4px)`;
        });

        card.addEventListener('mouseleave', function () {
            this.style.transform = '';
        });
    });
}

// Subtle parallax effect for background
function initParallaxEffect() {
    let ticking = false;

    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                const scrolled = window.pageYOffset;
                const heroSection = document.querySelector('.hero-section');

                if (heroSection) {
                    heroSection.style.transform = `translateY(${scrolled * 0.3}px)`;
                    heroSection.style.opacity = 1 - (scrolled * 0.002);
                }

                ticking = false;
            });
            ticking = true;
        }
    });
}

// ===== Premium Number Counter Animation =====
function animateCounter(element, target, duration = 1000) {
    const start = 0;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 4); // Ease out quart

        const current = Math.floor(start + (target - start) * eased);
        element.textContent = current.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

// Initialize counters when they come into view
function initCounters() {
    const counters = document.querySelectorAll('.stat-value');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = parseInt(entry.target.textContent.replace(/,/g, ''));
                if (!isNaN(target)) {
                    animateCounter(entry.target, target);
                }
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(counter => observer.observe(counter));
}

// Run counter init after DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCounters);
} else {
    initCounters();
}
