document.addEventListener("DOMContentLoaded", function () { 
    console.log("✅ script.js loaded!");

    // Menu Elements
    const menuBtn = document.querySelector(".menu-btn");
    const offcanvasMenu = document.querySelector(".offcanvas");
    const closeBtn = document.querySelector(".close-btn");

    // Check if menu elements exist before adding event listeners
    if (menuBtn && offcanvasMenu && closeBtn) {
        console.log("✅ Menu elements found!");

        function openMenu() {
            offcanvasMenu.classList.add("show");
            document.addEventListener("click", closeMenuOnOutsideClick);
        }

        function closeMenu() {
            offcanvasMenu.classList.remove("show");
            document.removeEventListener("click", closeMenuOnOutsideClick);
        }

        function closeMenuOnOutsideClick(event) {
            if (!offcanvasMenu.contains(event.target) && !menuBtn.contains(event.target)) {
                closeMenu();
            }
        }

        menuBtn.addEventListener("click", function (event) {
            event.stopPropagation();
            openMenu();
        });

        closeBtn.addEventListener("click", function (event) {
            event.stopPropagation();
            closeMenu();
        });
    } else {
        console.warn("⚠️ Menu elements not found. Skipping menu functionality.");
    }

    // Scroll Reveal Elements
    const elements = document.querySelectorAll(".scroll-reveal");

    if (elements.length > 0) {
        console.log(`✅ Scroll reveal elements found: ${elements.length}`);

        const observer = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("active");
                    observer.unobserve(entry.target); // Ensures animation happens only once
                }
            });
        }, { threshold: 0.2 });

        elements.forEach(element => {
            observer.observe(element);
        });
    } else {
        console.warn("⚠️ No .scroll-reveal elements found.");
    }

    // Hero Text and Logo Animations on Page Load
    const fadeUpElements = document.querySelectorAll(".fade-up");
    const fadeScaleElements = document.querySelectorAll(".fade-scale");

    if (fadeUpElements.length > 0 || fadeScaleElements.length > 0) {
        console.log(`✅ Hero animation elements found: ${fadeUpElements.length + fadeScaleElements.length}`);

        fadeUpElements.forEach((el, index) => {
            setTimeout(() => {
                el.style.animation = "fadeUp 1s ease-out forwards";
            }, index * 300); // Staggered delay
        });

        fadeScaleElements.forEach((el, index) => {
            setTimeout(() => {
                el.style.animation = "fadeScale 1s ease-out forwards";
            }, 600 + index * 300); // Slightly longer delay
        });
    } else {
        console.warn("⚠️ No fade-up or fade-scale elements found.");
    }
});