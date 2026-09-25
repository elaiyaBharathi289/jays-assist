const API_CONFIG = {
  baseUrl: "/api",
};

function getCookie(name) {
  const cookies = document.cookie ? document.cookie.split(";") : [];
  for (const cookie of cookies) {
    const [key, ...parts] = cookie.trim().split("=");
    if (key === name) return decodeURIComponent(parts.join("="));
  }
  return null;
}

async function apiRequest(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = {
    Accept: "application/json",
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(method !== "GET" && method !== "HEAD" ? { "X-CSRFToken": getCookie("csrftoken") || "" } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_CONFIG.baseUrl}${path}`, {
    credentials: "same-origin",
    ...options,
    headers,
  });

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    let message = data?.error || data?.detail || "Something went wrong.";
    if (typeof data === "object" && !data.error && !data.detail) {
      const firstError = Object.values(data).flat()[0];
      if (firstError) message = firstError;
    }
    const error = new Error(message);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

async function getCurrentUser() {
  return apiRequest("/auth/me/");
}

async function loginUser(payload) {
  return apiRequest("/auth/login/", { method: "POST", body: JSON.stringify(payload) });
}

async function registerUser(payload) {
  return apiRequest("/auth/register/", { method: "POST", body: JSON.stringify(payload) });
}

async function logoutUser() {
  return apiRequest("/auth/logout/", { method: "POST" });
}

async function getThreads() {
  return apiRequest("/threads/");
}

async function createThread(payload = {}) {
  return apiRequest("/threads/", { method: "POST", body: JSON.stringify(payload) });
}

async function getThreadMessages(threadId) {
  return apiRequest(`/threads/${threadId}/messages/`);
}

async function sendMessage(threadId, content) {
  return apiRequest(`/threads/${threadId}/messages/`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

async function deleteThread(threadId) {
  return apiRequest(`/threads/${threadId}/`, { method: "DELETE" });
}
