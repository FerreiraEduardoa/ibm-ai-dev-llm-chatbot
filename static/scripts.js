// ==============================
// Modern Chat UI - Frontend Logic
// (English comments, Portuguese UI text)
// ==============================

const form = document.getElementById("chatForm");
const input = document.getElementById("prompt");
const messages = document.getElementById("messages");
const btnSend = document.getElementById("btnSend");
const btnClear = document.getElementById("btnClear");
const statusText = document.getElementById("statusText");

// Scroll chat to the latest message
function scrollToBottom() {
  messages.scrollTop = messages.scrollHeight;
}

// Add a message bubble to the UI
function addMessage(role, text) {
  const row = document.createElement("div");
  row.className = role === "user" ? "msg msg-user" : "msg msg-bot";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = role === "user" ? "Você" : "Bot";

  const content = document.createElement("div");
  content.className = "text";
  content.textContent = text;

  bubble.appendChild(meta);
  bubble.appendChild(content);
  row.appendChild(bubble);

  messages.appendChild(row);
  scrollToBottom();
  return row;
}

// Show a temporary "typing..." message
function showTyping() {
  return addMessage("bot", "Digitando...");
}

// Clear chat (frontend only)
btnClear.addEventListener("click", () => {
  messages.innerHTML = "";
  addMessage("bot", "Conversa limpa. Como posso te ajudar?");
});

// Send prompt to backend
async function sendToBackend(promptText) {
  btnSend.disabled = true;
  statusText.textContent = "Pensando...";

  const typingRow = showTyping();

  try {
    const res = await fetch("/chatbot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: promptText })
    });

    let botText = "";
    const contentType = res.headers.get("content-type") || "";

    // Support both JSON and plain text responses
    if (contentType.includes("application/json")) {
      const data = await res.json();
      botText = data.response || "";
    } else {
      botText = await res.text();
    }

    typingRow.remove();
    addMessage("bot", botText || "(sem resposta)");
  } catch (err) {
    typingRow.remove();
    addMessage("bot", "Erro: não consegui acessar o servidor. Veja o terminal do Flask.");
  } finally {
    btnSend.disabled = false;
    statusText.textContent = "Online";
    input.focus();
  }
}

// Form submit (Enter sends)
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const text = input.value.trim();
  if (!text) return;

  addMessage("user", text);
  input.value = "";

  await sendToBackend(text);
});
