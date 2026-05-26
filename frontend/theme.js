// theme.js — Global Theme Controller for ALL pages

// 1. Apply saved theme when page loads
(function () {
    const savedTheme = localStorage.getItem("coresight-theme");

    if (savedTheme === "light") {
        document.body.classList.add("light-mode");
    }
})();

// 2. Handles toggle and updates localStorage + button icon
function toggleTheme(button) {
    document.body.classList.toggle("light-mode");

    const isLight = document.body.classList.contains("light-mode");

    // Save to localStorage
    localStorage.setItem("coresight-theme", isLight ? "light" : "dark");

    // Update clicked button icon
    button.textContent = isLight ? "☀️" : "🌙";

    // Update ALL other theme toggle buttons on other pages
    document.querySelectorAll(".theme-toggle").forEach(btn => {
        btn.textContent = isLight ? "☀️" : "🌙";
    });
}

// 3. Attach automatic listeners to ANY button with class .theme-toggle
window.addEventListener("DOMContentLoaded", () => {
    const isLight = document.body.classList.contains("light-mode");

    document.querySelectorAll(".theme-toggle").forEach(btn => {
        btn.textContent = isLight ? "☀️" : "🌙";

        btn.addEventListener("click", () => {
            toggleTheme(btn);
        });
    });
});
