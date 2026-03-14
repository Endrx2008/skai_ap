# SkAi — Firefox Plugin

Plugin Firefox con AI agent integrata via Ollama (Qwen3).
Parte del progetto **SkAi**.

---

## Struttura del progetto

```
skai-firefox/
├── manifest.json                  ← Manifest WebExtension v3
├── icons/
│   ├── skai-48.png
│   ├── skai-96.png
│   └── skai-128.png
└── src/
    ├── shared/
    │   ├── constants.js           ← Costanti globali, system prompt, config
    │   └── ollama.js              ← Client REST per Ollama (streaming)
    ├── background/
    │   └── background.js          ← Service worker — orchestratore
    ├── content/
    │   └── content.js             ← Iniettato in ogni pagina
    └── sidebar/
        ├── sidebar.html           ← UI sidebar
        ├── sidebar.css            ← Design SkAi
        └── sidebar.js             ← Logica sidebar
```

---

## Prerequisiti

1. **Firefox 109+** (supporto Manifest v3 + sidebar_action)
2. **Ollama** installato e in esecuzione
3. **Modello Qwen3** scaricato:
   ```bash
   ollama pull qwen3:4b
   ```
4. Ollama deve girare su `localhost:11434` (default)
   - In SkAi questo è gestito automaticamente

---

## Installazione (sviluppo)

1. Apri Firefox e vai su `about:debugging`
2. Clicca **"Questo Firefox"** (o "This Firefox")
3. Clicca **"Carica componente aggiuntivo temporaneo"**
4. Seleziona il file `manifest.json` di questo progetto

La sidebar si apre con `Visualizza > Sidebar > SkAi`
oppure con la scorciatoia impostata nel manifest.

---

## Come funziona

### Flusso principale

```
Utente scrive → Sidebar.js → Background.js → Ollama (Qwen3)
                                    ↓
                           JSON action response
                                    ↓
                          Action Router (switch)
                                    ↓
             ┌──────────────────────────────────┐
             │  reply_chat  search  open_tab     │
             │  navigate    read_page  workflow  │
             └──────────────────────────────────┘
```

### JSON Actions

Ollama risponde sempre con un JSON strutturato:

```json
{
  "decision": "search",
  "reply": null,
  "actions": [
    {
      "type": "search",
      "query": "Linux kernel 6.8 release notes",
      "engine": "ddg",
      "topic": "linux-kernel",
      "new_tab": true,
      "read_after": true
    },
    {
      "type": "search",
      "query": "Linux kernel 6.8 new features",
      "engine": "brave",
      "topic": "linux-kernel",
      "new_tab": true
    }
  ],
  "reasoning": "Apro due tab per avere più fonti sul kernel"
}
```

### Tipi di action supportati

| Action           | Descrizione                              |
|------------------|------------------------------------------|
| `reply_chat`     | Risponde direttamente in chat            |
| `search`         | Cerca su web (Google/DDG/Brave)          |
| `open_tab`       | Apre una URL in nuova tab                |
| `navigate`       | Naviga nella tab corrente                |
| `read_page`      | Legge/riassume una pagina                |
| `close_tab`      | Chiude le tab di un topic                |
| `notify`         | Notifica browser                         |
| `workflow`       | Lista di azioni annidate (pipeline)      |

---

## Prossimi step (roadmap)

- [ ] Aggiunta icone SVG SkAi
- [ ] Persistenza storia su `browser.storage.local`
- [ ] Workflow builder visuale
- [ ] Support multi-modello (selettore in UI)
- [ ] RAG locale: indicizzazione pagine visitate
- [ ] Export sessioni di ricerca come markdown
- [ ] Hotkey globale per aprire la sidebar
- [ ] Integrazione con altri servizi SkAi

---

## Configurazione avanzata

Modifica `src/shared/constants.js` per:
- Cambiare modello (`OLLAMA_MODEL`)
- Cambiare porta Ollama (`OLLAMA_BASE_URL`)
- Personalizzare il system prompt (`SYSTEM_PROMPT`)
- Aggiungere motori di ricerca (`SEARCH_ENGINES`)
