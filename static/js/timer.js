function startQuizTimer() {
    const quizRoot = document.querySelector("[data-quiz-attempt]");
    if (!quizRoot) {
        return;
    }

    const timerDisplay = quizRoot.querySelector("[data-timer-display]");
    const timerChip = quizRoot.querySelector("[data-timer]");
    const deadline = new Date(quizRoot.dataset.deadline);

    const tick = () => {
        const remaining = deadline.getTime() - Date.now();
        const safeRemaining = Math.max(remaining, 0);
        const minutes = String(Math.floor(safeRemaining / 60000)).padStart(2, "0");
        const seconds = String(Math.floor((safeRemaining % 60000) / 1000)).padStart(2, "0");
        timerDisplay.textContent = `${minutes}:${seconds}`;

        if (safeRemaining <= 300000) {
            timerChip.classList.add("timer-danger");
        }

        if (safeRemaining <= 0) {
            clearInterval(window.quizTimerInterval);
            const submitForm = document.createElement("form");
            submitForm.method = "post";
            submitForm.action = quizRoot.dataset.submitAllUrl;
            document.body.appendChild(submitForm);
            submitForm.submit();
        }
    };

    tick();
    window.quizTimerInterval = window.setInterval(tick, 1000);
}

document.addEventListener("DOMContentLoaded", startQuizTimer);
