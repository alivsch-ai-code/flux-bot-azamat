"""
Haupt-GUI: Ein-Klick-Aktionen für Datenbank-Init, Modell-Import und Live-Schaltung.
"""
import io
import sys
from pathlib import Path

# Projekt-Root für src-Imports hinzufügen
_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="AI Bot Tools",
    layout="centered",
)

st.title("🎛️ AI Bot Model Manager")
st.caption("Tools zum Einrichten und Verwalten der KI-Modelle")

# Output-Capture Helper
def run_with_output(func):
    """Führt eine Funktion aus und fängt print-Ausgaben ab."""
    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer
    try:
        func()
        return True, buffer.getvalue()
    except Exception as e:
        return False, str(e)
    finally:
        sys.stdout = old_stdout


# --- Schritt 1: DB initialisieren ---
st.subheader("1️⃣ Datenbank initialisieren")
st.write("Erstellt Tabellen `ai_models` und `ai_models_staging`. **Achtung:** Löscht bestehende Daten!")

if st.button("🧹 Datenbank initialisieren", key="init"):
    with st.spinner("Initialisiere..."):
        success, out = run_with_output(lambda: __import__("src.tools.init", fromlist=["setup_database"]).setup_database())
    if success:
        st.success("✅ Fertig!")
        st.code(out, language=None)
    else:
        st.error(out)


# --- Schritt 2: Default-Modelle laden ---
st.subheader("2️⃣ Default-Modelle laden")
st.write("Lädt 8 Best-of-Modelle (Flux, Kling, Llama, etc.) von Replicate ins Staging.")

if st.button("📥 Default-Modelle laden", key="fetch"):
    with st.spinner("Lade von Replicate..."):
        success, out = run_with_output(lambda: __import__("src.tools.fetch_advanced", fromlist=["import_to_staging"]).import_to_staging())
    if success:
        st.success("✅ Fertig!")
        st.code(out, language=None)
    else:
        st.error(out)


# --- Schritt 3: Freigeben & Live schalten ---
st.subheader("3️⃣ Freigeben & Live schalten")
st.write("Überträgt alle Modelle mit ✓ Approve aus dem Staging in die Live-Datenbank.")

if st.button("🚀 Approve & Push to Live", key="approve"):
    with st.spinner("Übertrage..."):
        success, out = run_with_output(lambda: __import__("src.tools.approve_to_main", fromlist=["transfer_approved"]).transfer_approved())
    if success:
        st.success("✅ Fertig!")
        st.code(out, language=None)
    else:
        st.error(out)


# --- Link zur Admin-GUI ---
st.divider()
st.subheader("📋 Modelle bearbeiten")
st.write("Im **Admin-GUI** kannst du Modelle sichten, bearbeiten (Typ, Credits, Menü) und für Approve markieren.")
st.markdown("""
Führe in einem **neuen Terminal** aus:
```
streamlit run src/tools/admin_gui.py
```
Oder öffne: [Admin-GUI](http://localhost:8502) (falls bereits gestartet).
""")
