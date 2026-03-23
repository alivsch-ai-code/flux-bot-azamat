import re


class InputValidator:
    """
    Zentrale Sicherheits-Validierung für User-Inputs (Prompts).
    """

    MAX_PROMPT_LEN = 4000

    # einfache Blacklist-Heuristiken (Prompt-Injection / Secrets)
    _FORBIDDEN_PATTERNS = [
        r"ignore (all )?previous instructions",
        r"system prompt",
        r"developer mode",
        r"openai_api_key",
        r"replicate_api_token",
        r"password",
        r"DROP TABLE",
        r"rm -rf",
    ]

    @staticmethod
    def sanitize_prompt(text: str) -> str:
        """
        Bereinigt den Input:
        1. Entfernt Whitespaces am Anfang/Ende
        2. Begrenzt Länge auf MAX_PROMPT_LEN Zeichen (Spamschutz)
        """
        if not text:
            return ""

        clean = text.strip()
        return clean[: InputValidator.MAX_PROMPT_LEN]

    @staticmethod
    def validate_safety(text: str) -> bool:
        """
        Prüft auf gefährliche oder unerwünschte Inhalte.
        Returns: True wenn sicher, False wenn unsicher.
        """
        if not text:
            # Leere Prompts sind sinnlos, aber nicht gefährlich – der Aufrufer
            # entscheidet, ob das zugelassen wird.
            return True

        lowered = text.lower()

        # Längenlimit (zu lange Prompts deuten oft auf Abuse/Spam hin)
        if len(lowered) > InputValidator.MAX_PROMPT_LEN:
            return False

        # Blacklist-Muster (Regex für Varianten wie "ignore (all )?previous instructions")
        for pattern in InputValidator._FORBIDDEN_PATTERNS:
            if re.search(pattern, lowered, re.IGNORECASE):
                return False

        return True