import os
import replicate

# Wir bleiben bei Gemini, machen es aber "sauber"
MODEL_ID = "google/gemini-2.5-flash"

SYSTEM_INSTRUCTION = """
You are a prompt generating machine. Your job is to take a user input and turn it into a high-quality Image Generation Prompt.
RULES:
1. OUTPUT ONLY THE RAW PROMPT. No "Here is...", no quotes.
2. If the user wants a specific style (comic, sketch), KEEP it.
3. If NO style is specified, assume "Photorealistic, 8k, highly detailed".
4. Do NOT chat. JUST rewrite.
"""

def optimize_prompt_via_llm(user_prompt: str):
    try:
        client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))
        
        # Kombinierter Prompt
        combined_prompt = f"{SYSTEM_INSTRUCTION}\n\nUSER INPUT: {user_prompt}\n\nOPTIMIZED PROMPT:"
        
        input_data = {
            "input": combined_prompt,
            "prompt": combined_prompt,
            "temperature": 0.4, # Niedrig halten für Präzision
            "top_k": 32,
            "top_p": 0.9,
        }
        
        output = client.run(MODEL_ID, input=input_data)
        full_response = "".join(output).strip()
        
        # --- FIX: String Bereinigung ---
        # Falls Gemini doch "Here is the prompt: ..." schreibt, schneiden wir es weg.
        if ":" in full_response[:25]: # Wenn ein Doppelpunkt am Anfang vorkommt
            full_response = full_response.split(":", 1)[1].strip()
            
        # Anführungszeichen entfernen
        full_response = full_response.strip('"').strip("'")
        
        if not full_response:
            return user_prompt
            
        return full_response

    except Exception as e:
        print(f"⚠️ Prompt Engineer Error: {e}")
        return user_prompt