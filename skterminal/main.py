import sys
import io
import json
import re
import requests
from pathlib import Path

# ─── UTF-8 terminal fix ───────────────────────────────────────────────────────
sys.stdin  = io.TextIOWrapper(sys.stdin.buffer,  encoding="utf-8", errors="replace")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from config import OLLAMA_URL, MODEL, SKAI_HOME, MAX_FILES, CHAT_SYSTEM, TOOL_NAMES
from fs_create import create_file
from fs_edit   import edit_file
from fs_delete import delete_file, delete_all_files
from fs_rename import rename_file
from fs_read   import read_file, list_files
from fs_dirs   import create_dir, rename_dir, delete_dir, list_dirs, move_dir
from fs_move   import move_file
from web_access import web_search
from memory import load_memory, save_memory, memory_to_context, update_memory

MAX_RETRIES = 3


# ─── Ollama call ─────────────────────────────────────────────────────────────

def ask_ollama(messages: list, temperature: float = 0.3, max_tokens: int = 600) -> str:
    """Send messages to Ollama and return the raw text response."""
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=120)
        r.raise_for_status()
        return r.json().get("message", {}).get("content", "").strip()
    except requests.exceptions.ConnectionError:
        return "ERROR: Ollama is not running. Start it with: ollama serve"
    except Exception as e:
        return f"ERROR: {e}"


# ─── Response parsing ─────────────────────────────────────────────────────────

def parse_tool_calls(response: str) -> list[dict] | None:
    """
    Look for one or more valid tool calls inside the model's response.
    Supports two formats:
      - Single:   {"tool": "...", "params": {...}}
      - Multiple: [{"tool": "...", "params": {...}}, ...]

    Returns a list of valid dicts, or None if nothing is found.
    """
    def normalize(data):
        if isinstance(data, dict) and "tool" in data:
            data["tool"] = data["tool"].lower()
        return data

    for text in [response.strip(), response.strip().strip("`")]:
        try:
            data = json.loads(text)
            if isinstance(data, list):
                data = [normalize(d) for d in data]
                valid = [d for d in data if isinstance(d, dict) and d.get("tool") in TOOL_NAMES]
                if valid:
                    return valid
            if isinstance(data, dict):
                normalize(data)
                if data.get("tool") in TOOL_NAMES:
                    return [data]
        except json.JSONDecodeError:
            pass

    for pattern in [r'\[[\s\S]*\]', r'\{[\s\S]*\}']:
        match = re.search(pattern, response)
        if match:
            try:
                data = json.loads(match.group())
                if isinstance(data, list):
                    data = [normalize(d) for d in data]
                    valid = [d for d in data if isinstance(d, dict) and d.get("tool") in TOOL_NAMES]
                    if valid:
                        return valid
                if isinstance(data, dict):
                    normalize(data)
                    if data.get("tool") in TOOL_NAMES:
                        return [data]
            except json.JSONDecodeError:
                pass

    return None


def is_echoed_prompt(text: str) -> bool:
    markers = ["Request:", "Files in folder:", "Reply ONLY with JSON", "Single example:"]
    return sum(1 for m in markers if m in text) >= 2


def is_boilerplate(text: str) -> bool:
    phrases = [
        "i'll execute immediately",
        "executing immediately",
        "understood! executing",
        "without asking for confirmation",
        "i'm ready to help",
        "got it, executing",
    ]
    t = text.lower()
    return any(p in t for p in phrases)


# ─── Intent classifier ────────────────────────────────────────────────────────

_INTENT_SYSTEM = "You are a classifier. Reply ONLY with the word YES or the word NO."

def needs_tool(user_input: str, file_list: str) -> bool:
    msgs = [
        {"role": "system", "content": _INTENT_SYSTEM},
        {"role": "user",   "content": (
            f"The user said: \"{user_input}\"\n"
            f"Is this asking to create, read, edit, rename, or delete files? "
            f"Existing files: {file_list}.\n"
            f"Reply YES if it's a file operation, NO if it's normal conversation."
        )},
    ]
    resp = ask_ollama(msgs, temperature=0.0, max_tokens=10).strip().upper()
    return resp.startswith("YES") or resp == "Y"


# ─── Search query builder ─────────────────────────────────────────────────────

_QUERY_SYSTEM = (
    "You are a search query optimizer. "
    "The user will give you a question or sentence. "
    "Reply with ONLY 2-5 English keywords suitable for a search engine. "
    "If the query contains a proper name (person, place, title), ALWAYS keep it exactly as written — never translate or replace it. "
    "IGNORE any formatting or length instructions in the query (e.g. '100 lines', '100 righe', 'write me', 'fammi un sunto', 'make a list') — those are not search terms. "
    "Focus only on the subject matter being asked about. "
    "Correct obvious typos only if you are 100% sure. "
    "No punctuation, no explanation, no extra words. Just the keywords."
)

_STRIP_PATTERNS = [
    r'\b\d+\s*(righe|lines|linee|parole|words|paragrafi|paragraphs|caratteri|chars)\b',
    r'\b(fammi|fai|scrivi|crea|genera|write|make|create|produce|give me|insert|inserisci)\b',
    r'\b(un sunto|una ricerca|un riassunto|un resoconto|summary|research|overview)\b',
    r'\b(di circa|circa|about|around|roughly|almeno|at least)\b',
]

def _strip_formatting_intent(text: str) -> str:
    result = text
    for pattern in _STRIP_PATTERNS:
        result = re.sub(pattern, ' ', result, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', result).strip()

def build_search_query(user_input: str) -> str:
    cleaned = _strip_formatting_intent(user_input)
    if not cleaned:
        cleaned = user_input

    msgs = [
        {"role": "system", "content": _QUERY_SYSTEM},
        {"role": "user",   "content": cleaned},
    ]
    keywords = ask_ollama(msgs, temperature=0.0, max_tokens=20).strip()

    if len(keywords) > 60:
        keywords = " ".join(keywords.split()[:5])

    cleaned_words  = set(cleaned.lower().split())
    keyword_words  = set(keywords.lower().split())
    if not cleaned_words & keyword_words:
        fallback = " ".join(cleaned.split()[:5])
        print(f"  [query fallback: '{keywords}' → '{fallback}']")
        return fallback

    return keywords


# ─── Main call with JSON retry ────────────────────────────────────────────────

_RETRY_SYSTEM = """You are a JSON generator. Output ONLY a valid JSON array of tool calls. No text, no explanation, no markdown, no code blocks.

ALWAYS use this exact format, even for a single operation:
[{"tool": "tool_name", "params": {...}}]

Available tools and their exact param names:
  create_file  → {"filename": "name.txt", "content": "text"}
  edit_file    → {"filename": "name.txt", "new_content": "text"}
  delete_file  → {"filename": "name.txt"}
  rename_file  → {"old": "old.txt", "new": "new.txt"}
  read_file    → {"filename": "name.txt"}
  move_file    → {"filename": "name.txt", "destination": "foldername"}
  move_dir     → {"dirname": "subfolder", "destination": "parent_folder"}
  create_dir   → {"dirname": "foldername"}
  rename_dir   → {"old": "oldfolder", "new": "newfolder"}
  delete_dir   → {"dirname": "foldername", "force": true}
  list_files   → {}
  list_dirs    → {}
  delete_all   → {}
  web_search   → {"query": "2-5 keyword English query — NEVER copy user's sentence"}

If the user wants N operations, output N objects in the array.
"""

_RETRY_EXAMPLE_MULTI = (
    'Example — create a file in each of 3 folders:\n'
    '[{"tool": "create_file", "params": {"filename": "folder1/note.txt", "content": "hello"}}, '
    '{"tool": "create_file", "params": {"filename": "folder2/note.txt", "content": "hello"}}, '
    '{"tool": "create_file", "params": {"filename": "folder3/note.txt", "content": "hello"}}]'
)


def ask_ollama_with_retry(messages: list, user_input: str, force_tool: bool = False) -> tuple[str, list[dict] | None]:
    response = ask_ollama(messages)

    if response.startswith("ERROR"):
        return response, None

    tool_calls = parse_tool_calls(response)
    if tool_calls:
        return "", tool_calls

    snapshot = folder_snapshot()

    if not force_tool and not is_boilerplate(response) and not needs_tool(user_input, snapshot):
        return response, None

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"  [retry {attempt}/{MAX_RETRIES}]...")

        retry_messages = [
            {"role": "system", "content": _RETRY_SYSTEM},
            {"role": "user",   "content": (
                f"Current state of skai_home:\n{snapshot}\n\n"
                f"User request: {user_input}\n\n"
                f"{_RETRY_EXAMPLE_MULTI}"
            )},
        ]

        response = ask_ollama(retry_messages, temperature=0.0, max_tokens=2000)
        print(f"  [debug] {response[:150]}")

        tool_calls = parse_tool_calls(response)
        if tool_calls:
            return "", tool_calls

        if is_echoed_prompt(response) or is_boilerplate(response):
            continue

    return "I didn't understand the operation. Try to be more specific (e.g. 'create a file called notes.txt')", None


# ─── Tool dispatcher ──────────────────────────────────────────────────────────

def dispatch_tool(tool: str, params: dict) -> str:
    match tool:
        case "list_files":
            return list_files()

        case "read_file":
            return read_file(params.get("filename", ""))

        case "create_file" | "new_file":
            content_val = params.get("content") or params.get("text") or ""
            return create_file(params.get("filename", ""), content_val)

        case "edit_file" | "write_file" | "update_file":
            content_val = (params.get("new_content") or params.get("content")
                           or params.get("text") or "")
            return edit_file(params.get("filename", ""), content_val)

        case "delete_file" | "rm" | "remove_file" | "del" | "unlink":
            files = params.get("files")
            if files and isinstance(files, list):
                results = [delete_file(f) for f in files]
                return "\n".join(results)

            all_flag = params.get("all") or params.get("all_files") or params.get("directory")
            if all_flag:
                return delete_all_files()

            fname = (params.get("filename") or params.get("file")
                     or params.get("name") or params.get("path") or "")
            fname = Path(fname).name if fname else ""
            return delete_file(fname)

        case "rename_file":
            old = params.get("old") or params.get("old_name", "")
            new = params.get("new") or params.get("new_name", "")
            return rename_file(old, new)

        case "delete_all" | "rm_all" | "delete_all_files" | "clear_folder" | "clear":
            return delete_all_files()

        case "replace_file" | "swap_file":
            old_f = (params.get("old_file") or params.get("old_filename")
                     or params.get("filename") or "")
            new_f = (params.get("new_file") or params.get("new_filename")
                     or params.get("new_name") or "")
            if not old_f or not new_f:
                return "replace_file: insufficient parameters."
            r1 = delete_file(Path(old_f).name)
            r2 = create_file(Path(new_f).name, "")
            return f"{r1} | {r2}"

        case "create_dir" | "mkdir":
            dirname = (params.get("dirname") or params.get("foldername")
                       or params.get("name") or params.get("folder") or "")
            return create_dir(dirname)

        case "rename_dir":
            old = params.get("old") or params.get("old_name", "")
            new = params.get("new") or params.get("new_name", "")
            return rename_dir(old, new)

        case "delete_dir" | "rmdir":
            dirname = (params.get("dirname") or params.get("foldername")
                       or params.get("name") or params.get("folder") or "")
            force   = bool(params.get("force", False))
            return delete_dir(dirname, force=force)

        case "move_dir":
            dirname = (params.get("dirname") or params.get("foldername")
                       or params.get("name") or params.get("folder") or "")
            dest    = (params.get("destination") or params.get("dest")
                       or params.get("destination_folder") or "")
            return move_dir(dirname, dest)

        case "list_dirs":
            return list_dirs()

        case "move_file" | "mv":
            fname = (params.get("filename") or params.get("file")
                     or params.get("source") or params.get("source_filename") or "")
            dest  = (params.get("destination") or params.get("dest")
                     or params.get("destination_folder") or params.get("folder") or "")
            return move_file(fname, dest)

        case "web_search":
            return dispatch_web_search(params)

        case _:
            return f"Unknown tool: '{tool}'."


# ─── Web search dispatcher ────────────────────────────────────────────────────

def dispatch_web_search(params: dict) -> str:
    raw_query = params.get("query") or params.get("q") or params.get("search") or ""
    if not raw_query:
        return "web_search: missing 'query' parameter."

    optimized_query = build_search_query(raw_query)
    print(f"  [query: '{raw_query}' → '{optimized_query}']")

    return web_search(optimized_query)


# ─── Folder snapshot ─────────────────────────────────────────────────────────

def folder_snapshot() -> str:
    if not SKAI_HOME.exists():
        return "skai_home does not exist yet."

    def _tree(path: Path, indent: int) -> list[str]:
        lines = []
        pad = "  " * indent
        children = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
        for child in children:
            if child.is_dir():
                lines.append(f"{pad}{child.name}/")
                lines.extend(_tree(child, indent + 1))
            else:
                lines.append(f"{pad}{child.name} ({child.stat().st_size} bytes)")
        return lines

    tree_lines = _tree(SKAI_HOME, 1)
    if not tree_lines:
        return "skai_home is currently empty."

    return "skai_home/\n" + "\n".join(tree_lines)


def inject_snapshot(messages: list, memory: dict | None = None) -> None:
    snapshot = folder_snapshot()
    mem_context = memory_to_context(memory) if memory else ""
    memory_block = f"\n\n{mem_context}" if mem_context else ""
    messages[0]["content"] = (
        CHAT_SYSTEM +
        memory_block +
        f"\n\n--- Current state of skai_home ---\n{snapshot}\n---"
    )


# ─── Startup context injection ────────────────────────────────────────────────

def build_initial_messages(memory: dict) -> list:
    messages = [
        {"role": "system", "content": CHAT_SYSTEM},
        {
            "role": "user",
            "content": (
                f"[SYSTEM] Working folder: {SKAI_HOME} | Max file limit: {MAX_FILES}"
            ),
        },
        {
            "role": "assistant",
            "content": "Got it. Ready.",
        },
    ]
    inject_snapshot(messages, memory)
    return messages


# ─── Main loop ────────────────────────────────────────────────────────────────

def main():
    print("=" * 57)
    print("  Skai - File assistant powered by qwen2.5:14b")
    print(f"  Folder  : {SKAI_HOME}")
    print(f"  Limit   : {MAX_FILES} files")
    print(f"  Model   : {MODEL}")
    print("  Type 'exit' to quit, 'files' for a quick file list")
    print("  Prefixes: '!' force tool | '?' force plain text")
    print("=" * 57)

    memory = load_memory()
    mem_ctx = memory_to_context(memory)
    if mem_ctx:
        print("\n[memory loaded]")
        user_name = memory.get("user", {}).get("name")
        if user_name:
            print(f"  Welcome back, {user_name}!")

    messages = build_initial_messages(memory)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            print("Bye!")
            break
        if user_input.lower() in ("files", "ls", "list"):
            print(f"\n{list_files()}")
            continue

        force_tool = user_input.startswith("!")
        force_text = user_input.startswith("?")
        clean_input = user_input[1:].strip() if (force_tool or force_text) else user_input

        messages.append({"role": "user", "content": clean_input})
        inject_snapshot(messages, memory)

        print("Skai is thinking...")

        if force_text:
            llm_response = ask_ollama(messages)
            tool_calls = None
        else:
            llm_response, tool_calls = ask_ollama_with_retry(
                messages, clean_input, force_tool=force_tool
            )

        if tool_calls:
            results = []
            web_results_to_forward = []

            for tc in tool_calls:
                tool   = tc["tool"]
                params = tc.get("params", {})
                print(f"Skai executing: {tool}({params})...")
                result = dispatch_tool(tool, params)
                print(f"  → {result[:120]}...")

                if tool == "web_search":
                    web_results_to_forward.append(result)
                else:
                    results.append(f"{tool}: {result}")

            if web_results_to_forward:
                context = "\n\n".join(web_results_to_forward)
                needs_file_op = needs_tool(clean_input, folder_snapshot())

                if needs_file_op:
                    followup_instruction = (
                        f"[WEB SEARCH RESULTS]\n{context}\n\n"
                        f"The user asked: \"{clean_input}\"\n\n"
                        f"Using the search results above, perform the file operation requested. "
                        f"Output ONLY a valid JSON array with a single tool call. "
                        f"Example: [{{'tool': 'edit_file', 'params': {{'filename': 'news.txt', 'new_content': '...'}}}}]\n"
                        f"Write as much content as possible from the search results. "
                        f"No extra text, no explanation — ONLY the JSON array."
                    )
                else:
                    followup_instruction = (
                        f"[WEB SEARCH RESULTS]\n{context}\n\n"
                        f"Answer the user's question in plain Italian using the results above. "
                        f"Do NOT output JSON. Just write a clear, natural language answer."
                    )

                messages.append({"role": "user", "content": followup_instruction})
                print("Skai is reading the results...")
                final_answer = ask_ollama(messages, temperature=0.3, max_tokens=2000)

                follow_up_calls = parse_tool_calls(final_answer)

                if follow_up_calls and all(ftc["tool"] == "web_search" for ftc in follow_up_calls):
                    print("\nSkai: Non ho trovato risultati sufficienti. "
                          "Prova a riformulare la domanda con parole chiave diverse.")
                    messages.append({
                        "role": "assistant",
                        "content": "No results found. Asked user to rephrase.",
                    })

                elif follow_up_calls:
                    for ftc in follow_up_calls:
                        ftool   = ftc["tool"]
                        fparams = ftc.get("params", {})
                        print(f"Skai executing (follow-up): {ftool}({fparams})...")
                        fresult = dispatch_tool(ftool, fparams)
                        print(f"  → {fresult}")
                        results.append(f"{ftool}: {fresult}")
                    messages.append({
                        "role": "assistant",
                        "content": "Operations done: " + " | ".join(
                            ftc["tool"] for ftc in follow_up_calls
                        ),
                    })

                elif needs_file_op:
                    print("  [follow-up retry: atteso JSON, ricevuto testo]...")
                    retry_msgs = [
                        {"role": "system", "content": _RETRY_SYSTEM},
                        {"role": "user", "content": (
                            f"Web search results:\n{context}\n\n"
                            f"User request: {clean_input}\n"
                            f"Current files: {folder_snapshot()}\n\n"
                            f"Output ONLY a JSON array with the file operation to perform."
                        )},
                    ]
                    retry_answer = ask_ollama(retry_msgs, temperature=0.0, max_tokens=2000)
                    retry_calls  = parse_tool_calls(retry_answer)
                    if retry_calls:
                        for ftc in retry_calls:
                            ftool   = ftc["tool"]
                            fparams = ftc.get("params", {})
                            print(f"Skai executing (retry follow-up): {ftool}({fparams})...")
                            fresult = dispatch_tool(ftool, fparams)
                            print(f"  → {fresult}")
                            results.append(f"{ftool}: {fresult}")
                        messages.append({
                            "role": "assistant",
                            "content": "Operations done: " + " | ".join(
                                ftc["tool"] for ftc in retry_calls
                            ),
                        })
                    else:
                        print(f"\nSkai: {retry_answer}")
                        messages.append({"role": "assistant", "content": retry_answer})

                else:
                    print(f"\nSkai: {final_answer}")
                    messages.append({"role": "assistant", "content": final_answer})

            if results:
                print(f"\n[folder updated]\n{list_files()}")
                messages.append({
                    "role": "assistant",
                    "content": "Operations done: " + " | ".join(results),
                })
            last_reply = messages[-1]["content"] if messages else ""
            memory = update_memory(memory, clean_input, last_reply, ask_ollama)
            save_memory(memory)

        else:
            print(f"\nSkai: {llm_response}")
            messages.append({"role": "assistant", "content": llm_response})
            memory = update_memory(memory, clean_input, llm_response, ask_ollama)
            save_memory(memory)


if __name__ == "__main__":
    main()
