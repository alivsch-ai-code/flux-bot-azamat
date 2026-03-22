import os
import replicate

# --- CONFIG ---
# Wir nutzen Gemini 2.5 Flash für maximale Geschwindigkeit und Präzision
MODEL_ID = "google/gemini-2.5-flash"

SYSTEM_PROMPT = """
You are an expert prompt engineer for AI Image Generators (Flux, Midjourney).
Your task is to optimize the user's prompt to be more detailed, artistic, and effective.
RULES:
1. Keep it in English.
2. Add keywords for lighting, texture, camera angle, and style.
3. If no style is specified, assume "Photorealistic, 8k, highly detailed".
4. RETURN ONLY THE RAW OPTIMIZED PROMPT. NO EXPLANATION, NO QUOTES.
"""

def optimize_prompt_via_llm(user_prompt: str):
    """
    Optimiert den User-Prompt via Gemini (Replicate).
    Bei Fehlern wird der originale Prompt als Fallback zurückgegeben.
    """
    api_token = os.getenv("REPLICATE_API_TOKEN")
    
    if not api_token:
        print("⚠️ REPLICATE_API_TOKEN nicht gefunden.")
        return user_prompt

    try:
        client = replicate.Client(api_token=api_token)
        
        # Kombinierter Input für das Modell
        prompt_input = f"{SYSTEM_PROMPT}\n\nUSER INPUT: {user_prompt}\n\nOPTIMIZED PROMPT:"
        
        output = client.run(
            MODEL_ID,
            input={
                "prompt": prompt_input,
                "temperature": 0.4,
                "max_tokens": 250,
                "top_p": 0.9
            }
        )
        
        # Replicate gibt einen Generator zurück, den wir zusammenfügen
        full_response = "".join([str(x) for x in output]).strip()
        
        # --- BEREINIGUNG ---
        # 1. Falls Gemini "Optimized Prompt: ..." oder "Here is..." schreibt
        if ":" in full_response[:30]:
            full_response = full_response.split(":", 1)[1].strip()
            
        # 2. Anführungszeichen entfernen, die LLMs gerne setzen
        full_response = full_response.strip('"').strip("'").strip("`")
        
        # Sicherheitscheck: Falls das Ergebnis leer ist, Original nutzen
        if not full_response or len(full_response) < 3:
            return user_prompt
            
        return full_response

    except Exception as e:
        print(f"⚠️ Gemini Prompt Optimierung fehlgeschlagen: {e}")
        return user_prompt # Fallback: Original zurückgeben


SUMMARY_SYSTEM = (
    "You summarize conversations concisely. Preserve who said what (names) when present. "
    "Output ONLY the summary, no intro. Keep it short (2-5 sentences)."
)


def summarize_conversation_via_llm(conversation_text: str) -> str:
    """Fasst eine Unterhaltung via Gemini zusammen. Erhält Teilnehmer-Namen."""
    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        return conversation_text[:500]  # Fallback: Kürzung
    try:
        client = replicate.Client(api_token=api_token)
        prompt_input = f"{SUMMARY_SYSTEM}\n\nCONVERSATION:\n{conversation_text}\n\nSUMMARY:"
        output = client.run(
            MODEL_ID,
            input={"prompt": prompt_input, "temperature": 0.3, "max_tokens": 300, "top_p": 0.9},
        )
        full_response = "".join([str(x) for x in output]).strip()
        if not full_response or len(full_response) < 3:
            return conversation_text[:500]
        return full_response
    except Exception as e:
        print(f"⚠️ Gemini Summarization fehlgeschlagen: {e}")
        return conversation_text[:500]