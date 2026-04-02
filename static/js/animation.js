const themeToggle = document.querySelector("[data-theme-toggle]");
const storedTheme = localStorage.getItem("quiz-theme");

if (storedTheme) {
    document.documentElement.setAttribute("data-theme", storedTheme);
}

if (themeToggle) {
    themeToggle.addEventListener("click", () => {
        const nextTheme =
            document.documentElement.getAttribute("data-theme") === "light" ? "dark" : "light";
        document.documentElement.setAttribute("data-theme", nextTheme);
        localStorage.setItem("quiz-theme", nextTheme);
    });
}

document.querySelectorAll("[data-loading-form]").forEach((form) => {
    form.addEventListener("submit", () => {
        const overlay = document.createElement("div");
        overlay.className = "loading-overlay";
        overlay.innerHTML = `
            <div class="loading-card">
                <p class="eyebrow">Generating quiz</p>
                <h3>Please wait while AI prepares your questions.</h3>
            </div>
        `;
        document.body.appendChild(overlay);
    });
});
