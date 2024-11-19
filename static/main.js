document.addEventListener("DOMContentLoaded", function () {
    const products = document.querySelectorAll(".product");

    // Create an Intersection Observer
    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("visible"); // Add the 'visible' class when in view
                observer.unobserve(entry.target); // Stop observing once the animation is triggered
            }
        });
    });

    // Observe each product card
    products.forEach((product) => {
        observer.observe(product);
    });
});
