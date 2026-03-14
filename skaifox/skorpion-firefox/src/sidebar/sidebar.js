// === SkAi — SIDEBAR ===

const chatArea      = document.getElementById("chat-area");
const userInput     = document.getElementById("user-input");
const sendBtn       = document.getElementById("send-btn");
const statusDot     = document.getElementById("status-dot");
const statusText    = document.getElementById("status-text");
const sessionsPanel = document.getElementById("sessions-panel");
const sessionsList  = document.getElementById("sessions-list");
const sessionsCount = document.getElementById("sessions-count");
const welcomeMsg    = document.getElementById("welcome-msg");

let isLoading       = false;
let streamingBubble = null;
let lastActionsRow  = null;

// =========================================================
// INIT
// =========================================================
async function init() {
  const { status, ollamaReady } = await browser.runtime.sendMessage({ type: "GET_STATUS" });
  updateStatusUI(status, ollamaReady);

  const { history } = await browser.runtime.sendMessage({ type: "GET_HISTORY" });
  if (history?.length > 0) {
    welcomeMsg.style.display = "none";
    addSystemNote(`Sessione ripresa — ${history.length / 2} scambi precedenti`);
  }

  const { sessions } = await browser.runtime.sendMessage({ type: "GET_SESSIONS" });
  updateSessionsUI(sessions);
}
init();

// =========================================================
// MESSAGGI DAL BACKGROUND
// =========================================================
browser.runtime.onMessage.addListener((msg) => {
  switch (msg.type) {
    case "STATUS_CHANGED":
      updateStatusUI(msg.status, msg.ollamaReady);
      break;
    case "AI_STREAM_CHUNK":
      handleStreamChunk(msg.full);
      break;
    case "CHAT_REPLY":
      finalizeStreamingBubble(msg.text);
      setLoading(false);
      break;
    case "AI_ERROR":
      if (streamingBubble) finalizeStreamingBubble(`⚠ ${msg.message}`);
      else addMessage("ai", `⚠ ${msg.message}`);
      setLoading(false);
      break;
    case "ACTIONS_DONE":
      handleActionsDone(msg.results);
      break;
    case "SEARCH_STARTED":
      addActionPill(`↗ Cerco: ${msg.query}`, "active");
      break;
    case "TAB_OPENED":
      updateActionPill(`⬡ Tab aperta: ${msg.topic}`, "done");
      break;
    case "PAGE_READ":
      updateActionPill(`✓ Pagina letta`, "done");
      break;
    case "PAGE_SUMMARY":
      addMessage("ai", msg.summary);
      setLoading(false);
      break;
    case "ACTION_ERROR":
      addActionPill(`✕ Errore: ${msg.action?.type ?? "azione"}`, "error");
      break;
    case "SESSION_UPDATED":
      updateSessionsUI(msg.sessions);
      break;
  }
});

// =========================================================
// INVIO MESSAGGIO
// =========================================================
async function sendMessage() {
  const text = userInput.value.trim();
  if (!text || isLoading) return;

  welcomeMsg.style.display = "none";
  addMessage("user", text);
  userInput.value = "";
  autoResizeInput();
  setLoading(true);
  lastActionsRow = null;

  // Contesto pagina corrente — MV2 usa tabs.executeScript
  let pageContext = null;
  try {
    const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
    if (tab?.id) {
      const results = await browser.tabs.executeScript(tab.id, {
        code: `({
          title: document.title,
          url:   location.href,
          text:  document.body ? document.body.innerText.slice(0, 2000) : ""
        })`
      });
      pageContext = results?.[0] ?? null;
    }
  } catch { /* pagina non accessibile */ }

  streamingBubble = createStreamingBubble();

  try {
    await browser.runtime.sendMessage({ type: "USER_MESSAGE", text, pageContext });
  } catch (err) {
    finalizeStreamingBubble(`⚠ ${err.message}`);
    setLoading(false);
  }
}

sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    sendMessage();
  }
  setTimeout(autoResizeInput, 0);
});

// =========================================================
// STREAMING
// =========================================================
function createStreamingBubble() {
  const wrapper = document.createElement("div");
  wrapper.className = "sk-message ai";
  wrapper.innerHTML = `
    <div class="sk-message-meta">
      <span class="sk-message-role">SkAi</span>
      <span class="sk-message-time">${timestamp()}</span>
    </div>
    <div class="sk-message-bubble sk-typing-cursor" id="sk-stream-bubble"></div>
  `;
  chatArea.appendChild(wrapper);
  scrollToBottom();
  return wrapper.querySelector("#sk-stream-bubble");
}

function handleStreamChunk(full) {
  if (!streamingBubble) return;
  const cleaned = full
    .replace(/^[\s]*\{[\s]*"decision"[\s]*:[\s]*"[^"]*"[\s]*,[\s]*"reply"[\s]*:[\s]*"?/, "")
    .replace(/"[\s]*,[\s]*"actions"[\s]*:[\s]*\[[\s\S]*$/, "")
    .trim();
  streamingBubble.textContent = cleaned || "...";
  scrollToBottom();
}

function finalizeStreamingBubble(text) {
  if (!streamingBubble) return;
  streamingBubble.classList.remove("sk-typing-cursor");
  streamingBubble.removeAttribute("id");
  streamingBubble.textContent = text;
  streamingBubble = null;
  scrollToBottom();
}

// =========================================================
// AZIONI COMPLETATE
// =========================================================
function handleActionsDone(results) {
  chatArea.querySelectorAll(".sk-action-pill.active").forEach(p => {
    p.classList.remove("active");
    p.classList.add("done");
  });
  const errors = results?.filter(r => !r.ok) ?? [];
  if (errors.length > 0) {
    addSystemNote(`${errors.length} azione${errors.length > 1 ? "i" : ""} non riuscit${errors.length > 1 ? "e" : "a"}`);
  }
  setLoading(false);
}

// =========================================================
// UI HELPERS
// =========================================================
function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `sk-message ${role}`;
  div.innerHTML = `
    <div class="sk-message-meta">
      <span class="sk-message-role">${role === "user" ? "TU" : "SkAi"}</span>
      <span class="sk-message-time">${timestamp()}</span>
    </div>
    <div class="sk-message-bubble">${escHtml(text)}</div>
  `;
  chatArea.appendChild(div);
  scrollToBottom();
}

function addSystemNote(text) {
  const div = document.createElement("div");
  div.className = "sk-system-note";
  div.textContent = text;
  chatArea.appendChild(div);
  scrollToBottom();
}

function addActionPill(label, state = "active") {
  if (!lastActionsRow || !chatArea.contains(lastActionsRow)) {
    lastActionsRow = document.createElement("div");
    lastActionsRow.className = "sk-actions-row";
    chatArea.appendChild(lastActionsRow);
  }
  const pill = document.createElement("span");
  pill.className = `sk-action-pill ${state}`;
  pill.textContent = label;
  lastActionsRow.appendChild(pill);
  scrollToBottom();
  return pill;
}

function updateActionPill(label, state) {
  if (!lastActionsRow) return addActionPill(label, state);
  const active = lastActionsRow.querySelector(".sk-action-pill.active");
  if (active) {
    active.textContent = label;
    active.className = `sk-action-pill ${state}`;
  } else {
    addActionPill(label, state);
  }
  scrollToBottom();
}

function updateStatusUI(status, ollamaReady) {
  statusDot.className = "sk-status-dot";
  switch (status) {
    case "idle":
      if (ollamaReady) { statusDot.classList.add("online"); statusText.textContent = "Pronto"; }
      else             { statusDot.classList.add("error");  statusText.textContent = "Ollama non raggiungibile"; }
      break;
    case "thinking":
      statusDot.classList.add("thinking");
      statusText.textContent = "Qwen3 sta pensando...";
      break;
    case "searching":
      statusDot.classList.add("searching");
      statusText.textContent = "Ricerca in corso...";
      break;
    case "reading":
      statusDot.classList.add("searching");
      statusText.textContent = "Lettura pagina...";
      break;
    case "done":
      statusDot.classList.add("online");
      statusText.textContent = "Fatto";
      setTimeout(() => updateStatusUI("idle", true), 2000);
      break;
    case "error":
      statusDot.classList.add("error");
      statusText.textContent = "Errore";
      break;
  }
}

function updateSessionsUI(sessions) {
  const topics = Object.keys(sessions ?? {});
  sessionsPanel.style.display = topics.length === 0 ? "none" : "block";
  sessionsCount.textContent = topics.length;
  sessionsList.innerHTML = "";
  for (const topic of topics) {
    const count = sessions[topic].length;
    const tag   = document.createElement("div");
    tag.className = "sk-session-tag";
    tag.innerHTML = `
      <span>${escHtml(topic)}</span>
      <span class="sk-tag-count">${count}</span>
      <span class="sk-session-close" title="Chiudi tab">✕</span>
    `;
    tag.querySelector(".sk-session-close").addEventListener("click", (e) => {
      e.stopPropagation();
      browser.runtime.sendMessage({ type: "CLOSE_SESSION", topic });
    });
    sessionsList.appendChild(tag);
  }
}

function setLoading(val) {
  isLoading          = val;
  sendBtn.disabled   = val;
  userInput.disabled = val;
  if (!val) lastActionsRow = null;
}

function scrollToBottom()  { chatArea.scrollTop = chatArea.scrollHeight; }
function autoResizeInput() { userInput.style.height = "auto"; userInput.style.height = Math.min(userInput.scrollHeight, 120) + "px"; }
function timestamp()       { return new Date().toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" }); }
function escHtml(s)        { return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }

document.getElementById("btn-clear").addEventListener("click", async () => {
  await browser.runtime.sendMessage({ type: "CLEAR_HISTORY" });
  [...chatArea.children].forEach(c => { if (c !== welcomeMsg) c.remove(); });
  welcomeMsg.style.display = "block";
  streamingBubble = null;
  lastActionsRow  = null;
});
