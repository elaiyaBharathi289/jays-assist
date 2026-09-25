(function () {
  const state = {
    threads: [],
    activeThreadId: null,
    messages: {},
    user: null,
    isSending: false,
  };

  const els = {
    sidebar: document.getElementById("sidebar"),
    overlay: document.getElementById("sidebarOverlay"),
    threadList: document.getElementById("threadList"),
    emptyThreads: document.getElementById("emptyThreads"),
    welcomeState: document.getElementById("welcomeState"),
    messageList: document.getElementById("messageList"),
    conversationTitle: document.getElementById("conversationTitle"),
    messageInput: document.getElementById("messageInput"),
    sendBtn: document.getElementById("sendBtn"),
    composerShell: document.getElementById("composerShell"),
    toast: document.getElementById("appToast"),
    toastBody: document.getElementById("toastBody"),
    profileName: document.getElementById("profileName"),
    profileEmail: document.getElementById("profileEmail"),
    profileAvatar: document.getElementById("profileAvatar"),
  };

  function showToast(message) {
    els.toastBody.textContent = message;
    bootstrap.Toast.getOrCreateInstance(els.toast, { delay: 3000 }).show();
  }

  function formatDate(value) {
    const date = new Date(value);
    const now = new Date();
    if (date.toDateString() === now.toDateString()) {
      return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
    }
    return date.toLocaleDateString([], { month: "short", day: "numeric" });
  }

  function initials(name) {
    return name.split(" ").filter(Boolean).map((part) => part[0]).join("").slice(0, 2).toUpperCase();
  }

  function renderProfile() {
    const user = state.user || { username: "User", email: "" };
    const displayName = user.username || "User";
    els.profileName.textContent = displayName;
    els.profileEmail.textContent = user.email || "Jays Assist account";
    els.profileAvatar.textContent = initials(displayName);
  }

  function renderThreads() {
    els.threadList.innerHTML = "";
    els.emptyThreads.classList.toggle("d-none", state.threads.length > 0);

    state.threads.forEach((thread) => {
      const item = document.createElement("div");
      item.className = `thread-item ${thread.id === state.activeThreadId ? "active" : ""}`;
      item.innerHTML = `
        <button class="thread-main" type="button">
          <span class="thread-icon">◌</span>
          <span class="thread-text">
            <strong>${escapeHtml(thread.title)}</strong>
            <small>${formatDate(thread.updated_at)}</small>
          </span>
        </button>
        <button class="thread-delete" type="button" aria-label="Delete ${escapeHtml(thread.title)}">×</button>
      `;
      item.querySelector(".thread-main").addEventListener("click", () => selectThread(thread.id));
      item.querySelector(".thread-delete").addEventListener("click", (event) => {
        event.stopPropagation();
        removeThread(thread.id);
      });
      els.threadList.appendChild(item);
    });
  }

  function renderMessages() {
    const messages = state.messages[state.activeThreadId] || [];
    const hasMessages = messages.length > 0;
    els.welcomeState.classList.toggle("d-none", hasMessages);
    els.messageList.classList.toggle("d-none", !hasMessages);
    els.messageList.innerHTML = "";
    messages.forEach((message) => appendMessage(message, false));
    els.messageList.scrollTop = els.messageList.scrollHeight;
  }

  function appendMessage(message, scroll = true) {
    const row = document.createElement("article");
    row.className = `message-row ${message.role}`;
    row.innerHTML = `
      <div class="message-avatar">${message.role === "user" ? "You" : "J"}</div>
      <div class="message-body">
        <div class="message-meta"><strong>${message.role === "user" ? "You" : "Jays Assist"}</strong><span>${formatDate(message.created_at)}</span></div>
        <div class="message-bubble">${escapeHtml(message.content).replace(/\n/g, "<br>")}</div>
      </div>
    `;
    els.messageList.appendChild(row);
    if (scroll) els.messageList.scrollTop = els.messageList.scrollHeight;
  }

  async function selectThread(threadId) {
    const thread = state.threads.find((item) => item.id === threadId);
    if (!thread) return;
    state.activeThreadId = threadId;
    els.conversationTitle.textContent = thread.title;
    renderThreads();
    closeSidebar();

    try {
      state.messages[threadId] = await getThreadMessages(threadId);
      renderMessages();
    } catch (error) {
      showToast(error.message || "Unable to load this conversation.");
    }
  }

  async function createNewThread() {
    try {
      const thread = await createThread({ title: "New conversation" });
      state.threads.unshift(thread);
      state.activeThreadId = thread.id;
      state.messages[thread.id] = [];
      els.conversationTitle.textContent = thread.title;
      renderThreads();
      renderMessages();
      els.messageInput.focus();
      closeSidebar();
    } catch (error) {
      showToast(error.message || "Unable to create a new conversation.");
    }
  }

  async function removeThread(threadId) {
    const thread = state.threads.find((item) => item.id === threadId);
    if (!thread) return;
    if (!window.confirm(`Delete “${thread.title}”?`)) return;

    try {
      await deleteThread(threadId);
      state.threads = state.threads.filter((item) => item.id !== threadId);
      delete state.messages[threadId];
      if (state.activeThreadId === threadId) {
        state.activeThreadId = null;
        els.conversationTitle.textContent = "New conversation";
      }
      renderThreads();
      renderMessages();
      showToast("Conversation deleted.");
    } catch (error) {
      showToast(error.message || "Unable to delete the conversation.");
    }
  }

  async function sendCurrentMessage() {
    if (state.isSending) return;
    const content = els.messageInput.value.trim();
    if (!content) return;

    if (!state.activeThreadId) {
      await createNewThread();
      if (!state.activeThreadId) return;
    }

    const threadId = state.activeThreadId;
    state.isSending = true;
    els.sendBtn.disabled = true;
    els.composerShell.classList.add("sending");
    els.messageInput.value = "";
    autoResizeTextarea();

    // Show the user's message immediately while the server processes it.
    const optimistic = {
      id: `temp-${Date.now()}`,
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };
    state.messages[threadId] = state.messages[threadId] || [];
    state.messages[threadId].push(optimistic);
    renderMessages();

    try {
      const result = await sendMessage(threadId, content);
      state.messages[threadId] = state.messages[threadId].filter((message) => message.id !== optimistic.id);
      state.messages[threadId].push(result.user_message, result.assistant_message);

      const updatedThread = state.threads.find((thread) => thread.id === threadId);
      if (updatedThread) {
        updatedThread.title = content.replace(/\s+/g, " ").trim().slice(0, 120);
        if (content.length > 120) updatedThread.title += "…";
        updatedThread.updated_at = result.assistant_message.created_at;
        els.conversationTitle.textContent = updatedThread.title;
      }
      state.threads.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
      renderThreads();
      renderMessages();
    } catch (error) {
      state.messages[threadId] = state.messages[threadId].filter((message) => message.id !== optimistic.id);
      renderMessages();
      showToast(error.message || "The AI service is temporarily unavailable.");
    } finally {
      state.isSending = false;
      els.sendBtn.disabled = false;
      els.composerShell.classList.remove("sending");
      els.messageInput.focus();
    }
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function autoResizeTextarea() {
    els.messageInput.style.height = "auto";
    els.messageInput.style.height = `${Math.min(els.messageInput.scrollHeight, 180)}px`;
  }

  function openSidebar() {
    els.sidebar.classList.add("open");
    els.overlay.classList.add("show");
  }

  function closeSidebar() {
    els.sidebar.classList.remove("open");
    els.overlay.classList.remove("show");
  }

  function openSettings() {
    bootstrap.Modal.getOrCreateInstance(document.getElementById("settingsModal")).show();
  }

  function initEvents() {
    document.getElementById("newChatBtn").addEventListener("click", createNewThread);
    document.getElementById("openSidebar").addEventListener("click", openSidebar);
    document.getElementById("closeSidebar").addEventListener("click", closeSidebar);
    els.overlay.addEventListener("click", closeSidebar);
    document.getElementById("settingsNav").addEventListener("click", openSettings);
    document.getElementById("profileSettingsBtn").addEventListener("click", openSettings);

    document.getElementById("profileMenuButton").addEventListener("click", () => {
      document.getElementById("profileMenu").classList.toggle("d-none");
    });

    document.getElementById("logoutBtn").addEventListener("click", async () => {
      try {
        await logoutUser();
      } finally {
        window.location.href = "/login/";
      }
    });

    els.sendBtn.addEventListener("click", sendCurrentMessage);
    els.messageInput.addEventListener("input", autoResizeTextarea);
    els.messageInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendCurrentMessage();
      }
    });

    document.getElementById("attachmentBtn").addEventListener("click", () => {
      document.getElementById("attachmentInput").click();
    });
    document.getElementById("attachmentInput").addEventListener("change", (event) => {
      const count = event.target.files.length;
      if (count) showToast(`${count} attachment${count > 1 ? "s" : ""} selected. File upload is not part of the current backend scope.`);
    });
    document.getElementById("searchBtn").addEventListener("click", () => {
      showToast("Search is reserved for a future feature; the current project focuses on conversational AI.");
    });
    document.getElementById("modelButton").addEventListener("click", () => {
      showToast("The model is configured securely on the Django backend.");
    });

    window.addEventListener("resize", () => {
      if (window.innerWidth >= 992) closeSidebar();
    });
  }

  async function init() {
    try {
      const userResult = await getCurrentUser();
      state.user = userResult.user;
      renderProfile();
      state.threads = await getThreads();
      renderThreads();
      initEvents();
    } catch (error) {
      if (error.status === 401 || error.status === 403) {
        window.location.href = "/login/";
        return;
      }
      showToast(error.message || "Unable to load Jays Assist.");
      initEvents();
    }
  }

  init();
})();
