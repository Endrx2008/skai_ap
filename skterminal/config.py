from pathlib import Path

# ─── Ollama ────────────────────────────────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL      = "qwen2.5:14b"

# ─── Filesystem ───────────────────────────────────────────────────────────────
MAX_FILES  = 100
SKAI_HOME  = Path("/media/endrx/hdd/skai_home")

# ─── System prompt ────────────────────────────────────────────────────────────
CHAT_SYSTEM = """You are Skai, a file management assistant.
You have access to a folder called skai_home to manage text files.

When the user wants to operate on files, reply ONLY with pure JSON, nothing else:
{"tool": "TOOL_NAME", "params": {...}}

Available tools:

  File tools:
  create_file   → {"filename": "...", "content": "..."}
  edit_file     → {"filename": "...", "new_content": "..."}
  delete_file   → {"filename": "..."}
  rename_file   → {"old": "...", "new": "..."}
  read_file     → {"filename": "..."}
  move_file     → {"filename": "...", "destination": "subfolder_name"}
  list_files    → {}

  Folder tools (subfolders inside skai_home only):
  create_dir    → {"dirname": "..."}
  rename_dir    → {"old": "...", "new": "..."}
  delete_dir    → {"dirname": "...", "force": true}
  move_dir      → {"dirname": "...", "destination": "parent_folder"}
  list_dirs     → {}

  Web tool:
  web_search    → {"query": "what to search for"}

Rules:
- Do NOT add any text before or after the JSON.
- Do NOT ask for confirmation before acting.
- For normal conversation reply in American English without JSON.
- If the user asks to delete all files, use the delete_all tool.
- Folder tools only work on subfolders of skai_home, never on skai_home itself.
- Use web_search when the user asks about current events, facts, or anything
  you don't know for certain. After getting the results, reply in plain text.
"""

# ─── Tool name registry ───────────────────────────────────────────────────────
TOOL_NAMES = {
    # File tools
    "create_file", "new_file",
    "edit_file", "write_file", "update_file",
    "delete_file", "rm", "remove_file", "del", "unlink",
    "delete_all", "rm_all", "delete_all_files", "clear_folder", "clear",
    "rename_file", "replace_file", "swap_file",
    "read_file",
    "move_file", "mv",
    "list_files",
    # Folder tools
    "create_dir", "mkdir",
    "rename_dir",
    "delete_dir", "rmdir",
    "move_dir",
    "list_dirs",
    # Web tool
    "web_search",
}
