// Animations Component
function initializeCounters() {
    const counters = document.querySelectorAll('.counter');
    const speed = 200; // Animation speed
    
    const animateCounter = (counter) => {
        const target = +counter.getAttribute('data-target');
        const count = +counter.innerText;
        const increment = target / speed;
        
        if (count < target) {
            counter.innerText = Math.ceil(count + increment);
            setTimeout(() => animateCounter(counter), 1);
        } else {
            counter.innerText = target;
        }
    };
    
    // Intersection Observer for viewport detection
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    });
    
    counters.forEach(counter => {
        observer.observe(counter);
    });
}

// Chart loading states
function initializeChartInteractions() {
    document.querySelectorAll('.chart-image').forEach(img => {
        img.addEventListener('load', function() {
            this.style.opacity = '0';
            this.style.animation = 'fadeIn 0.5s ease forwards';
        });
    });
    
    // Smooth tab transitions
    document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(e) {
            const targetPane = document.querySelector(this.getAttribute('data-bs-target'));
            if (targetPane) {
                targetPane.style.animation = 'fadeIn 0.3s ease';
            }
        });
    });
}

// Timeline animations
window.toggleTimelineDetails = function(day) {
    const detailsDiv = document.getElementById(`timelineDetails${day}`);
    const isVisible = detailsDiv.style.display !== 'none';
    
    if (isVisible) {
        detailsDiv.style.display = 'none';
    } else {
        detailsDiv.style.display = 'block';
        detailsDiv.style.animation = 'fadeIn 0.3s ease';
    }
};

// Load more timeline items
window.loadMoreTimeline = function() {
    const timelineItems = document.querySelectorAll('.timeline-item');
    let visibleCount = 0;
    let itemsToShow = 10;
    
    timelineItems.forEach((item) => {
        if (item.style.display !== 'none') {
            visibleCount++;
        }
    });
    
    let shown = 0;
    timelineItems.forEach((item, index) => {
        if (index >= visibleCount && shown < itemsToShow) {
            item.style.display = 'block';
            item.style.animation = 'fadeIn 0.3s ease';
            shown++;
        }
    });
    
    // Hide button if all items are visible
    if (visibleCount + shown >= timelineItems.length) {
        event.target.style.display = 'none';
    }
};