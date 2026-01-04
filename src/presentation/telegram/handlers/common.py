# Einfacher In-Memory State für den aktuellen Dialog-Schritt
# Format: {user_id: {"step": "waiting_for_prompt", "model": "imagen3", "mode": "image"}}
user_context = {}

def get_context(user_id):
    return user_context.get(user_id, {})

def set_context(user_id, data):
    user_context[user_id] = data

def clear_context(user_id):
    if user_id in user_context:
        del user_context[user_id]