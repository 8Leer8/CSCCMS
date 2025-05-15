// Function to check if user is logged in
function isLoggedIn() {
    return document.querySelector('.accordion-label.logout') !== null;
}

// Function to show login requirement modal
function showLoginRequiredModal() {
    const modal = new bootstrap.Modal(document.getElementById('need_account'));
    modal.show();
}

// Add click event listeners to concerns and feedback links
document.addEventListener('DOMContentLoaded', function() {
    // Get all concerns and feedback links
    const protectedLinks = document.querySelectorAll('a[href*="concerns"], a[href*="feedback"]');
    
    // Add click event listener to each link
    protectedLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (!isLoggedIn()) {
                e.preventDefault();
                showLoginRequiredModal();
            }
        });
    });
}); 