"""In-Memory Dialog-State pro User (thread-sicher für parallele Handler)."""
import threading

# Format: {user_id: {"step": "waiting_for_prompt", "model_key": "...", ...}}

user_context = {}
_context_lock = threading.Lock()


def get_context(user_id):
    with _context_lock:
        ctx = user_context.get(user_id)
        return dict(ctx) if ctx else {}


def set_context(user_id, data):
    with _context_lock:
        user_context[user_id] = data


def clear_context(user_id):
    with _context_lock:
        user_context.pop(user_id, None)
