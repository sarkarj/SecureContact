document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form");
    const submitBtn = document.getElementById("submit-btn");
    const refreshBtn = document.getElementById("refresh-captcha");
    const captchaImg = document.getElementById("captcha-img");

    const fields = {
        name: document.getElementById("name"),
        email: document.getElementById("email"),
        phone: document.getElementById("phone"),
        prefer_time: document.getElementById("prefer_time"),
        captcha: document.getElementById("captcha"),
    };

    const errors = {
        name: document.getElementById("name-error"),
        email: document.getElementById("email-error"),
        phone: document.getElementById("phone-error"),
        prefer_time: document.getElementById("prefer_time-error"),
        captcha: document.getElementById("captcha-error"),
    };

    let refreshCount = 0;
    const maxRefreshes = 9;  // Max allowed refreshes
    const refreshWindow = 60000; // 1 minute window for refresh count
    let refreshTimestamps = []; // Array to store timestamps of refreshes
    const captchaBaseUrl = captchaImg.getAttribute("data-base-url");

    function isNameValid(value) {
        return /^[a-zA-Z\s.]+$/.test(value.trim());
    }

    function isEmailValid(value) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
    }

    function isPhoneValid(value) {
        return /^\(\d{3}\) \d{3}-\d{4}$/.test(value.trim());
    }

    function isPreferTimeValid(value) {
        return value.trim() !== "";
    }

    function updateSubmitButton() {
        const valid =
            isNameValid(fields.name.value) &&
            isEmailValid(fields.email.value) &&
            isPhoneValid(fields.phone.value) &&
            isPreferTimeValid(fields.prefer_time.value) &&
            fields.captcha.value.trim() !== "";

        submitBtn.disabled = !valid;
    }

    function validateField(id, validator, message) {
        const value = fields[id].value.trim();
        const input = fields[id];

        if (!value) {
            errors[id].textContent = `${id.replace("_", " ")} is required`;
            input.classList.remove("valid");
            input.classList.add("invalid");
            return false;
        }
        if (!validator(value)) {
            errors[id].textContent = message;
            input.classList.remove("valid");
            input.classList.add("invalid");
            return false;
        }
        errors[id].textContent = "";
        input.classList.remove("invalid");
        input.classList.add("valid");
        return true;
    }

    function formatPhoneInput(e) {
        let value = e.target.value.replace(/\D/g, "");
        if (value.length <= 3) {
            e.target.value = value ? `(${value}` : value;
        } else if (value.length <= 6) {
            e.target.value = `(${value.slice(0, 3)}) ${value.slice(3)}`;
        } else {
            e.target.value = `(${value.slice(0, 3)}) ${value.slice(3, 6)}-${value.slice(6, 10)}`;
        }
    }

    function addInputValidation() {
        fields.name.addEventListener("input", e => {
            e.target.value = e.target.value.replace(/[^a-zA-Z\s.]/g, "");
            updateSubmitButton();
        });

        fields.phone.addEventListener("input", e => {
            formatPhoneInput(e);
            updateSubmitButton();
        });

        Object.keys(fields).forEach(id => {
            fields[id].addEventListener("blur", () => {
                switch (id) {
                    case "name":
                        validateField(id, isNameValid, "only alphabets, spaces, and dots allowed");
                        break;
                    case "email":
                        validateField(id, isEmailValid, "enter a valid email");
                        break;
                    case "phone":
                        validateField(id, isPhoneValid, "enter a valid 10-digit phone number");
                        break;
                    case "prefer_time":
                        validateField(id, isPreferTimeValid, "preferred time is required");
                        break;
                    case "captcha":
                        if (!fields.captcha.value.trim()) {
                            errors.captcha.textContent = "captcha is required";
                        } else {
                            errors.captcha.textContent = "";
                        }
                        break;
                }
                updateSubmitButton();
            });

            fields[id].addEventListener("input", updateSubmitButton);
        });
    }

    function addCaptchaRefreshLogic() {
        refreshBtn.addEventListener("click", () => {
            const now = Date.now();
            refreshTimestamps = refreshTimestamps.filter(ts => now - ts < refreshWindow);
            
            if (refreshTimestamps.length >= maxRefreshes) {
                alert("Too many CAPTCHA refreshes. Please wait a minute before trying again.");
                refreshBtn.disabled = true;
                const retryTime = refreshWindow - (now - refreshTimestamps[0]);
                setTimeout(() => {
                    refreshBtn.disabled = false;
                    refreshTimestamps = refreshTimestamps.filter(ts => Date.now() - ts < refreshWindow);
                }, retryTime);
            } else {
                refreshTimestamps.push(now);
                captchaImg.src = captchaBaseUrl + "?ts=" + now;
                fields.captcha.value = "";
                errors.captcha.textContent = "";
                updateSubmitButton();
            }
        });
    }

    function addFormSubmitValidation() {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            // Clear previous error messages
            Object.keys(errors).forEach(id => {
                errors[id].textContent = "";
            });

            // Final validation
            const isValid =
                validateField("name", isNameValid, "only alphabets, spaces, and dots allowed") &&
                validateField("email", isEmailValid, "enter a valid email") &&
                validateField("phone", isPhoneValid, "enter a valid 10-digit phone number") &&
                validateField("prefer_time", isPreferTimeValid, "preferred time is required") &&
                fields.captcha.value.trim();

            if (!isValid) {
                alert("Please correct the highlighted errors.");
                return;
            }

            const formData = new FormData(form);

            try {
                const response = await fetch("/submit", {
                    method: "POST",
                    body: formData,
                });

                const result = await response.json();

                switch (result.status) {
                    case "success":
                        alert("Thank you! Your information has been saved.");
                        form.reset();
                        Object.values(fields).forEach(field => field.classList.remove("valid", "invalid"));
                        captchaImg.src = captchaBaseUrl + "?ts=" + new Date().getTime();
                        updateSubmitButton();
                        break;
                    case "exists":
                        alert("You have already submitted your information.");
                        break;
                    case "invalid_phone":
                        errors.phone.textContent = "phone number failed verification.";
                        fields.phone.classList.add("invalid");
                        break;
                    case "captcha_fail":
                        errors.captcha.textContent = "incorrect captcha, try again.";
                        captchaImg.src = captchaBaseUrl + "?ts=" + new Date().getTime();
                        fields.captcha.value = "";
                        break;
                    case "error":
                        if (result.errors) {
                            for (const [field, messages] of Object.entries(result.errors)) {
                                if (errors[field]) {
                                    errors[field].textContent = messages[0];
                                    fields[field].classList.add("invalid");
                                }
                            }
                        } else {
                            alert("Something went wrong. Please try again.");
                        }
                        break;
                    default:
                        alert("Unexpected response from server.");
                }

            } catch (error) {
                alert("Network error: " + error.message);
            }
        });
    }

    addInputValidation();
    addCaptchaRefreshLogic();
    addFormSubmitValidation();
    updateSubmitButton();
});
