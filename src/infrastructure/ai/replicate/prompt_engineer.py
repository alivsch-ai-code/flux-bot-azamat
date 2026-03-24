import os
import replicate
import logging

logger = logging.getLogger(__name__)

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
        logger.warning("REPLICATE_API_TOKEN nicht gefunden.")
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
        logger.warning("Gemini Prompt Optimierung fehlgeschlagen: %s", e)
        return user_prompt # Fallback: Original zurückgeben


# System-Instruction NUR für Chat-Zusammenfassung – komplett getrennt von Bild-Prompt-Optimierung!
# Replicate: system_instruction wird separat übergeben, damit das Modell seine Rolle VOR dem Chat-Input kennt.
SUMMARY_SYSTEM_INSTRUCTION = """You are a CONVERSATION SUMMARIZER. Your ONLY task is to write a short summary of the chat dialogue you will receive.

STRICT RULES:
1. Output a brief summary (2-5 sentences) of what was discussed.
2. Preserve participant names (who said what) when present.
3. NEVER output image prompts, image descriptions, photography terms, or artistic/flux/midjourney-style text.
4. Output ONLY plain summary text. No "Summary:", no labels, no quotes.
5. If the conversation contains image-generation requests, summarize them as "User requested an image of X" – do NOT repeat or expand the image prompt."""


def summarize_conversation_via_llm(conversation_text: str) -> str:
    """
    Fasst eine Unterhaltung via Gemini zusammen. Nutzt system_instruction (separat von prompt),
    damit das Modell eindeutig als Summarizer agiert und KEINE Bild-Prompt-Optimierung macht.
    """
    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        return _truncate_fallback(conversation_text)
    try:
        client = replicate.Client(api_token=api_token)
        # prompt = NUR der Chat-Inhalt + kurze Aufforderung (system_instruction = Rolle)
        user_prompt = f"CONVERSATION:\n{conversation_text}\n\nSummarize the above conversation in 2-5 sentences. Output ONLY the summary."
        output = client.run(
            MODEL_ID,
            input={
                "prompt": user_prompt,
                "system_instruction": SUMMARY_SYSTEM_INSTRUCTION,
                "temperature": 0.2,
                "max_output_tokens": 300,
                "top_p": 0.9,
            },
        )
        full_response = "".join([str(x) for x in output]).strip()
        if not full_response or len(full_response) < 5:
            return _truncate_fallback(conversation_text)
        # Safeguard: Wenn die Antwort wie ein Bild-Prompt aussieht → Fallback
        img_keywords = (
            "photorealistic", "8k", "ultra-detailed", "hyper-realistic", "bokeh", "chiaroscuro",
            "arri alexa", "cinematic portrait", "hyper-photorealistic", "unreal engine", "dramatic lighting",
            "medium close-up", "shallow depth of field", "fedora", "leather jacket"
        )
        if any(kw in full_response.lower() for kw in img_keywords):
            return _truncate_fallback(conversation_text)
        return full_response
    except Exception as e:
        logger.warning("Gemini Summarization fehlgeschlagen: %s", e)
        return _truncate_fallback(conversation_text)


def _truncate_fallback(conversation_text: str, max_len: int = 500) -> str:
    """Fallback: Kürzt die Konversation statt fehlerhafter Zusammenfassung."""
    t = (conversation_text or "").strip()
    if len(t) <= max_len:
        return t
    return t[:max_len] + "..."