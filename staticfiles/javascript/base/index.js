document.addEventListener("DOMContentLoaded", () => {
    // Menu Toggle Functionality
    const menuToggle = document.getElementById("menuToggle");
    const closeMenu = document.getElementById("closeMenu");
    const dropdownMenu = document.getElementById("dropdownMenu");
  
    menuToggle.addEventListener("click", () => {
      dropdownMenu.classList.add("active");
    });
  
    closeMenu.addEventListener("click", () => {
      dropdownMenu.classList.remove("active");
    });
  
    // Accordion Functionality
    const accordionLabels = document.querySelectorAll(".accordion-label:not(.login):not(.logout)");
    const accordionContents = document.querySelectorAll(".accordion-content");
  
    // Ensure all accordion contents are hidden on page load
    accordionContents.forEach(content => {
      content.style.display = "none";
    });
  
    accordionLabels.forEach(label => {
      label.addEventListener("click", (e) => {
        // Don't toggle if clicking on login/logout links
        if (e.target.classList.contains("login") || e.target.classList.contains("logout")) {
          return;
        }
  
        const content = label.nextElementSibling;
  
        // If the clicked content is already visible, hide it and return
        if (content.style.display === "flex") {
          content.style.display = "none";
          return;
        }
  
        // Close all other accordion contents
        accordionContents.forEach(content => {
          content.style.display = "none";
        });
  
        // Show the clicked accordion content
        if (content.classList.contains("accordion-content")) {
          content.style.display = "flex";
        }
      });
    });
  
    // Close dropdown when clicking outside
    document.addEventListener("click", (e) => {
      if (!dropdownMenu.contains(e.target) && e.target !== menuToggle) {
        dropdownMenu.classList.remove("active");
      }
    });
  });