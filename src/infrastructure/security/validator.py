import re
import unicodedata
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Strukturiertes Ergebnis der Sicherheitsprüfung."""
    is_safe: bool
    reason: str | None = None  # z.B. "forbidden_pattern: jailbreak"


class InputValidator:
    """
    Zentrale Sicherheits-Validierung für User-Inputs (Prompts).

    Wichtig: Pattern-Matching ist nur die erste Verteidigungsschicht.
    Für robustere Sicherheit sollte zusätzlich ein Moderations-Prompt
    auf LLM-Ebene eingesetzt werden (z.B. im System-Prompt selbst).
    """

    MAX_PROMPT_LEN = 4000

    # Blacklist-Heuristiken (Prompt-Injection / Secrets / Shell)
    # Hinweis: re.IGNORECASE wird beim Matching gesetzt – kein .lower() nötig.
    _FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
        # --- Prompt Injection ---
        (r"ignore\s+(all\s+)?previous\s+instructions?",  "prompt_injection"),
        (r"disregard\s+(all\s+)?previous",               "prompt_injection"),
        (r"forget\s+(everything|all|your\s+instructions?)", "prompt_injection"),
        (r"new\s+instructions?\s*:",                     "prompt_injection"),
        (r"you\s+are\s+now\s+(a|an|in)\b",               "prompt_injection"),  # "You are now DAN"
        (r"act\s+as\s+(if\s+you\s+(are|were)|a\b|an\b)", "prompt_injection"),
        (r"\bjailbreak\b",                               "prompt_injection"),
        (r"\bdan\s+mode\b",                              "prompt_injection"),
        (r"pretend\s+(you\s+are|to\s+be)",               "prompt_injection"),

        # --- System-Kontext auslesen ---
        (r"\bsystem\s+prompt\b",                                    "context_extraction"),
        (r"reveal\s+(your\s+)?(prompt|instructions?|context)",       "context_extraction"),
        (r"what\s+(are|is)\s+your\s+instructions?",                 "context_extraction"),
        (r"show\s+me\s+your\s+(system|prompt|instructions?)",       "context_extraction"),
        (r"\binternal\s+monologue\b",                               "context_extraction"),
        (r"\bthought\s+process\b",                                  "context_extraction"),

        # --- Debug- / Entwickler-Modi ---
        (r"\bdeveloper\s+mode\b",   "debug_mode"),
        (r"\bdebug\s+mode\b",       "debug_mode"),
        (r"\bmaintenance\s+mode\b", "debug_mode"),

        # --- Secrets & Credentials ---
        (r"\bapi[_\s-]?key\b",       "credential"),
        (r"\bsecret[_\s-]?key\b",    "credential"),
        (r"\baccess[_\s-]?token\b",  "credential"),
        (r"\bauth[_\s-]?token\b",    "credential"),
        (r"\bbearer\s+token\b",      "credential"),
        (r"\bpassword\b",            "credential"),
        (r"\bpassphrase\b",          "credential"),
        (r"\bprivate[_\s-]?key\b",   "credential"),

        # --- Destruktive Shell-Befehle ---
        (r"\brm\s+-rf\b",           "shell_command"),
        (r"\bdrop\s+table\b",       "shell_command"),
        (r"\bdelete\s+from\b",      "shell_command"),
        (r"\btruncate\s+table\b",   "shell_command"),
        (r"format\s+[a-z]:\\",      "shell_command"),  # Windows

        # --- Code-Exfiltration / gefährliche Builtins ---
        (r"import\s+os\b.*\bsystem\b", "code_injection"),
        (r"\bexec\s*\(",               "code_injection"),
        (r"\beval\s*\(",               "code_injection"),
        (r"\b__import__\b",            "code_injection"),

        # --- Delimiter-Manipulation ---
        (r"<\/system>",  "delimiter_manipulation"),
        (r"\]\]>",       "delimiter_manipulation"),
        (r"END\s+OF\s+MESSAGE", "delimiter_manipulation"),
        (r"STOP\s+HERE",        "delimiter_manipulation"),
    ]

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Bereinigt den Input:
        - Entfernt führende/nachfolgende Whitespaces
        - Begrenzt auf MAX_PROMPT_LEN Zeichen
        """
        if not text:
            return ""
        # NFKC normalisiert Homoglyphen-/Unicode-Varianten robuster.
        normalized = unicodedata.normalize("NFKC", text)
        # Zero-width Zeichen entfernen, um Regex-Bypässe zu reduzieren.
        normalized = re.sub(r"[\u200B-\u200D\uFEFF]", "", normalized)
        return normalized.strip()[: InputValidator.MAX_PROMPT_LEN]

    sanitize_prompt = sanitize  # Alias (services, tests)

    @staticmethod
    def validateSafetyPromptInput(text: str) -> ValidationResult:
        """
        Prüft den bereinigten Text auf gefährliche Inhalte.

        Returns:
            ValidationResult mit is_safe=True wenn unbedenklich,
            sonst is_safe=False und einem reason-String.
        """
        if not text:
            return ValidationResult(is_safe=True)

        if len(text) > InputValidator.MAX_PROMPT_LEN:
            return ValidationResult(is_safe=False, reason="too_long")

        for pattern, category in InputValidator._FORBIDDEN_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                snippet = match.group(0)[:40] if match else ""
                return ValidationResult(
                    is_safe=False,
                    reason=f"{category}: '{snippet}'"
                )

        return ValidationResult(is_safe=True)

    @staticmethod
    def validate_safety(text: str) -> bool:
        """Kurzform für Tests und einfache Checks: True wenn Eingabe erlaubt."""
        return InputValidator.validateSafetyPromptInput(text).is_safe

    @classmethod
    def process(cls, raw_text: str) -> tuple[str, ValidationResult]:
        """
        Sanitize + Validate in einem Schritt.
        Stellt sicher, dass beide immer zusammen aufgerufen werden.

        Returns:
            (bereinigter Text, ValidationResult)

        Beispiel:
            clean, result = InputValidator.process(user_input)
            if not result.is_safe:
                logger.warning("Blocked input: %s", result.reason)
                return  # Anfrage ablehnen
        """
        clean = cls.sanitize(raw_text)
        result = cls.validateSafetyPromptInput(clean)
        return clean, result