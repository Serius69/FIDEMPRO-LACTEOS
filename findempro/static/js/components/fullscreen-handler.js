// Fullscreen Handler Component

function initializeFullscreen() {
    window.openFullscreen = function(imageData, title) {
        const overlay = document.getElementById('fullscreenOverlay');
        const image = document.getElementById('fullscreenImage');
        
        if (!overlay || !image) return;
        
        image.src = `data:image/png;base64,${imageData}`;
        image.alt = title;
        overlay.style.display = 'flex';
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    };
    
    window.closeFullscreen = function() {
        const overlay = document.getElementById('fullscreenOverlay');
        if (overlay) overlay.style.display = 'none';
        
        // Restore body scroll
        document.body.style.overflow = '';
    };
    
    // Close on ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeFullscreen();
        }
    });
    
    // Close on overlay click
    const overlay = document.getElementById('fullscreenOverlay');
    if (overlay) {
        overlay.addEventListener('click', function(e) {
            if (e.target === this) {
                closeFullscreen();
            }
        });
    }
}