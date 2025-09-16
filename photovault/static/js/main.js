// photovault/static/js/main.js

// REMOVE OR COMMENT OUT any existing upload-related JavaScript like:

/*
// OLD CODE - REMOVE THIS TO PREVENT CONFLICTS
function triggerUpload() {
    document.getElementById('fileInput').click();
}

document.getElementById('uploadBtn').addEventListener('click', triggerUpload);
// END OF CODE TO REMOVE
*/

// Keep only non-upload related JavaScript here
document.addEventListener('DOMContentLoaded', function() {
    // Other PhotoVault functionality (navigation, search, etc.)
    console.log('PhotoVault main.js loaded');
    
    // Example: Navigation highlighting
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});