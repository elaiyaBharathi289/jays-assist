(function () {
  const loginForm = document.getElementById("loginForm");
  const registerForm = document.getElementById("registerForm");

  function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (!element) return;
    element.textContent = message;
    element.classList.remove("d-none");
  }

  function hideError(elementId) {
    const element = document.getElementById(elementId);
    if (element) element.classList.add("d-none");
  }

  function setLoading(button, loading, label) {
    button.disabled = loading;
    button.textContent = loading ? "Please wait..." : label;
  }

  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      hideError("loginError");

      const username = document.getElementById("username").value.trim();
      const password = document.getElementById("password").value;
      const button = document.getElementById("loginBtn");

      if (!username || !password) {
        showError("loginError", "Please enter your username and password.");
        return;
      }

      setLoading(button, true, "Sign in");
      try {
        await loginUser({ username, password });
        window.location.href = "/chat/";
      } catch (error) {
        showError("loginError", error.message);
        setLoading(button, false, "Sign in");
      }
    });
  }

  if (registerForm) {
    registerForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      hideError("registerError");

      const username = document.getElementById("registerUsername").value.trim();
      const email = document.getElementById("registerEmail").value.trim();
      const password = document.getElementById("registerPassword").value;
      const password2 = document.getElementById("registerPassword2").value;
      const button = document.getElementById("registerBtn");

      if (username.length < 3) {
        showError("registerError", "Username must contain at least 3 characters.");
        return;
      }
      if (password.length < 8) {
        showError("registerError", "Password must contain at least 8 characters.");
        return;
      }
      if (password !== password2) {
        showError("registerError", "Passwords do not match.");
        return;
      }

      setLoading(button, true, "Create account");
      try {
        await registerUser({ username, email, password, password2 });
        window.location.href = "/login/";
      } catch (error) {
        const detail = error.data?.username?.[0] || error.data?.password?.[0] || error.data?.password2?.[0];
        showError("registerError", detail || error.message);
        setLoading(button, false, "Create account");
      }
    });
  }
})();
