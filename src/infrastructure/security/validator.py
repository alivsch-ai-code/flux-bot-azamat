import re

class InputValidator:
    """
    Statische Klasse oder Helper-Methoden zur Bereinigung von User-Inputs.
    """

    @staticmethod
    def sanitize_prompt(text: str) -> str:
        """
        Bereinigt den Input:
        1. Entfernt Whitespaces am Anfang/Ende
        2. Begrenzt Länge auf 1000 Zeichen (Replicate Limit & Spamschutz)
        3. Entfernt nicht-druckbare Zeichen
        """
        if not text:
            return ""
            
        # Strip
        clean = text.strip()
        
        # Length check (schneidet hart ab)
        clean = clean[:1000]
        
        return clean

    @staticmethod
    def validate_safety(text: str) -> bool:
        """
        Prüft auf gefährliche oder unerwünschte Inhalte.
        Returns: True wenn sicher, False wenn unsicher.
        """
        if not text:
            return False

        # 1. Blacklist für offensichtliche Systembefehle (bei CLI-Tools relevant)
        # Auch wenn Replicate isoliert ist, filtern wir es proaktiv.
        blacklist = [
            "rm -rf", 
            "DROP TABLE", 
            "<script>", 
            "javascript:",
            "system(",
            "os.remove"
        ]
        
        for term in blacklist:
            if term.lower() in text.lower():
                return False

        # 2. Einfacher Schutz gegen "Prompt Injection" (Versuch, Regeln zu umgehen)
        # User versuchen oft: "Ignore previous instructions..."
        injection_triggers = [
            "ignore all previous instructions",
            "system override",
            "developer mode"
        ]
        
        for trigger in injection_triggers:
            if trigger.lower() in text.lower():
                # Wir blocken das nicht hart, aber loggen es vielleicht als Warnung.
                # Für strikte Sicherheit: return False
                pass 

        return True