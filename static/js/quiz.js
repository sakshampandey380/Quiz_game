function playTone(type) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) {
        return;
    }

    const audioContext = new AudioContextClass();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.type = "sine";
    oscillator.frequency.value = type === "correct" ? 660 : 220;
    gainNode.gain.value = 0.001;
    oscillator.start();

    gainNode.gain.exponentialRampToValueAtTime(0.18, audioContext.currentTime + 0.01);
    gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.22);
    oscillator.stop(audioContext.currentTime + 0.24);
}

function showConfetti() {
    if (!document.querySelector("[data-confetti]")) {
        return;
    }

    playTone("correct");
    const colors = ["#24d6b5", "#ffb84d", "#ff6c8f", "#7cb8ff"];
    for (let index = 0; index < 32; index += 1) {
        const piece = document.createElement("span");
        piece.className = "confetti-piece";
        piece.style.left = `${Math.random() * 100}%`;
        piece.style.background = colors[index % colors.length];
        piece.style.setProperty("--x-shift", `${Math.random() * 180 - 90}px`);
        piece.style.animationDelay = `${Math.random() * 0.25}s`;
        document.body.appendChild(piece);
        setTimeout(() => piece.remove(), 3200);
    }
}

function setupQuizInteractions() {
    const quizRoot = document.querySelector("[data-quiz-attempt]");
    if (!quizRoot) {
        showConfetti();
        return;
    }

    const answerForm = quizRoot.querySelector("[data-answer-form]");
    const radios = [...answerForm.querySelectorAll("input[type='radio']")];
    const nextButton = quizRoot.querySelector("[data-next-question]");
    const submitQuizButton = quizRoot.querySelector("[data-submit-quiz]");
    const submitUrl = quizRoot.dataset.submitUrl;
    const autosaveUrl = quizRoot.dataset.autosaveUrl;
    const abandonUrl = quizRoot.dataset.abandonUrl;
    let isNavigating = false;

    const submitWholeQuiz = () => {
        isNavigating = true;
        const submitForm = document.createElement("form");
        submitForm.method = "post";
        submitForm.action = quizRoot.dataset.submitAllUrl;
        document.body.appendChild(submitForm);
        submitForm.submit();
    };

    const highlightSelected = () => {
        radios.forEach((radio) => {
            radio.closest(".option-card").classList.toggle("selected", radio.checked);
        });
    };

    const postAutosave = async (selectedOption) => {
        await fetch(autosaveUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ selected_option: selectedOption }),
        });
    };

    radios.forEach((radio) => {
        radio.addEventListener("change", async () => {
            highlightSelected();
            await postAutosave(radio.value);
        });
    });

    highlightSelected();

    window.history.pushState(null, "", window.location.href);
    window.addEventListener("popstate", () => {
        window.history.pushState(null, "", window.location.href);
    });

    if (performance.getEntriesByType("navigation")[0]?.type === "reload") {
        fetch(abandonUrl, { method: "POST", keepalive: true }).finally(() => {
            window.location.href = quizRoot.dataset.resultUrl;
        });
        return;
    }

    window.addEventListener("beforeunload", () => {
        if (!isNavigating) {
            navigator.sendBeacon(abandonUrl);
        }
    });

    nextButton?.addEventListener("click", async () => {
        const selected = answerForm.querySelector("input[name='selected_option']:checked");
        if (!selected) {
            window.alert("Please choose an option before moving ahead.");
            playTone("wrong");
            return;
        }

        isNavigating = true;
        const formData = new FormData();
        formData.append("selected_option", selected.value);
        const response = await fetch(submitUrl, { method: "POST", body: formData });
        const payload = await response.json();
        if (!response.ok || !payload.ok) {
            playTone("wrong");
            window.alert(payload.message || "Unable to save your answer.");
            isNavigating = false;
            if (payload.redirect_url) {
                window.location.href = payload.redirect_url;
            }
            return;
        }

        window.location.href = payload.redirect_url;
    });

    submitQuizButton?.addEventListener("click", () => {
        submitWholeQuiz();
    });
}

document.addEventListener("DOMContentLoaded", setupQuizInteractions);
