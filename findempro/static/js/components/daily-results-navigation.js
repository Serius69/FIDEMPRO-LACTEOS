// Daily Results Navigation Component

function initializeDailyResultsPagination() {
    const dailyResultsContainer = document.getElementById('dailyResultsContainer');
    if (!dailyResultsContainer) return;
    
    const allItems = document.querySelectorAll('.daily-result-item');
    const totalDays = allItems.length;
    let currentDay = 1;
    
    const prevBtn = document.getElementById('prevDayBtn');
    const nextBtn = document.getElementById('nextDayBtn');
    const dayCounter = document.getElementById('dayCounter');
    const currentDayIndicator = document.getElementById('currentDayIndicator');
    
    function updateDayDisplay() {
        // Hide all items
        allItems.forEach(item => {
            item.style.display = 'none';
        });
        
        // Show current item with animation
        const currentItem = document.querySelector(`[data-day="${currentDay}"]`);
        if (currentItem) {
            currentItem.style.display = 'block';
            currentItem.style.animation = 'fadeIn 0.3s ease';
        }
        
        // Update counters
        if (dayCounter) dayCounter.textContent = `Día ${currentDay} de ${totalDays}`;
        if (currentDayIndicator) currentDayIndicator.textContent = `Día ${currentDay}`;
        
        // Update button states
        if (prevBtn) {
            prevBtn.disabled = currentDay === 1;
            prevBtn.classList.toggle('btn-outline-secondary', currentDay === 1);
            prevBtn.classList.toggle('btn-outline-primary', currentDay > 1);
        }
        
        if (nextBtn) {
            nextBtn.disabled = currentDay === totalDays;
            nextBtn.classList.toggle('btn-outline-secondary', currentDay === totalDays);
            nextBtn.classList.toggle('btn-outline-primary', currentDay < totalDays);
        }
    }
    
    if (prevBtn) {
        prevBtn.addEventListener('click', function() {
            if (currentDay > 1) {
                currentDay--;
                updateDayDisplay();
            }
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', function() {
            if (currentDay < totalDays) {
                currentDay++;
                updateDayDisplay();
            }
        });
    }
    
    // Initialize display
    updateDayDisplay();
    
    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey || e.metaKey) {
            if (e.key === 'ArrowLeft' && currentDay > 1) {
                e.preventDefault();
                currentDay--;
                updateDayDisplay();
            } else if (e.key === 'ArrowRight' && currentDay < totalDays) {
                e.preventDefault();
                currentDay++;
                updateDayDisplay();
            }
        }
    });
}

// Timeline pagination
document.addEventListener('DOMContentLoaded', function() {
    // Show only first 10 timeline items initially
    const timelineItems = document.querySelectorAll('.timeline-item');
    let visibleItems = 10;
    
    timelineItems.forEach((item, index) => {
        if (index >= visibleItems) {
            item.style.display = 'none';
        }
    });
});