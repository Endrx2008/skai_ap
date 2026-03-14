// === SkAi — CLIENT OLLAMA (MV2, XMLHttpRequest per bypassare CORS) ===

function askOllama(userMessage, history, onChunk) {
  history = history || [];

  const messages = [
    { role: "system", content: SYSTEM_PROMPT },
    ...history,
    { role: "user",   content: userMessage }
  ];

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", OLLAMA_BASE_URL + "/api/chat", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.timeout = OLLAMA_TIMEOUT;

    let rawText  = "";
    let lastPos  = 0;

    xhr.onprogress = function() {
      const chunk = xhr.responseText.slice(lastPos);
      lastPos = xhr.responseText.length;

      const lines = chunk.split("\n").filter(Boolean);
      for (const line of lines) {
        try {
          const parsed = JSON.parse(line);
          if (parsed.message && parsed.message.content) {
            rawText += parsed.message.content;
            if (onChunk) onChunk(parsed.message.content, rawText);
          }
        } catch(e) {}
      }
    };

    xhr.onload = function() {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(parseAIResponse(rawText));
      } else {
        reject(new Error("Ollama HTTP " + xhr.status + ": " + xhr.statusText));
      }
    };

    xhr.onerror   = function() { reject(new Error("Ollama non raggiungibile su localhost:11434")); };
    xhr.ontimeout = function() { reject(new Error("Timeout: Ollama non risponde")); };

    xhr.send(JSON.stringify({
      model:    OLLAMA_MODEL,
      messages: messages,
      stream:   true,
      options:  { temperature: 0.3, top_p: 0.9 }
    }));
  });
}

function checkOllamaHealth() {
  return new Promise((resolve) => {
    const xhr = new XMLHttpRequest();
    xhr.open("GET", OLLAMA_BASE_URL + "/api/tags", true);
    xhr.timeout = 3000;
    xhr.onload    = function() { resolve(xhr.status >= 200 && xhr.status < 300); };
    xhr.onerror   = function() { resolve(false); };
    xhr.ontimeout = function() { resolve(false); };
    xhr.send();
  });
}

function parseAIResponse(raw) {
  const text = raw.trim();
  try { return JSON.parse(text); } catch(e) {}
  const fence = text.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
  if (fence) { try { return JSON.parse(fence[1]); } catch(e) {} }
  const braceMatch = text.match(/\{[\s\S]*\}/);
  if (braceMatch) { try { return JSON.parse(braceMatch[0]); } catch(e) {} }
  return {
    decision:  "chat",
    reply:     text || "Non ho capito la richiesta.",
    actions:   [],
    reasoning: "fallback"
  };
}
