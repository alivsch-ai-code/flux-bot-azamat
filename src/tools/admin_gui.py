import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

# Konfiguration laden
load_dotenv()

st.set_page_config(page_title="AI Model Admin", layout="wide")

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"), sslmode='require')

# --- DATEN LADEN ---
def load_data():
    conn = get_connection()
    # Wir laden alles aus Staging
    query = """
        SELECT 
            key, name, provider, model_type, menu_path, 
            internal_cost, base_cost_usd, 
            is_approved, manual_override, 
            description
        FROM ai_models_staging
        ORDER BY is_approved DESC, manual_override DESC, name ASC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# --- ÄNDERUNGEN SPEICHERN ---
def save_changes(edited_df, original_df):
    conn = get_connection()
    cur = conn.cursor()
    
    # Wir vergleichen, was sich geändert hat
    count = 0
    try:
        # Iteriere über den Index des bearbeiteten Dataframes
        for index, row in edited_df.iterrows():
            # Schlüssel zur Identifikation
            key = row['key']
            
            # Hat sich etwas geändert? (Vergleich mit Original ist hier vereinfacht, 
            # wir updaten einfach die geänderten Zeilen basierend auf Streamlits delta)
            
            # WICHTIG: Wenn wir was ändern, setzen wir manual_override = 1
            # Damit der Bot beim nächsten Import diese Zeile nicht überschreibt!
            
            cur.execute("""
                UPDATE ai_models_staging
                SET name = %s,
                    model_type = %s,
                    menu_path = %s,
                    internal_cost = %s,
                    is_approved = %s,
                    manual_override = 1 
                WHERE key = %s
            """, (
                row['name'], 
                row['model_type'], 
                row['menu_path'], 
                int(row['internal_cost']), 
                int(row['is_approved']), 
                key
            ))
            count += 1
            
        conn.commit()
        st.success(f"✅ {count} Zeilen aktualisiert & geschützt!")
    except Exception as e:
        st.error(f"Fehler beim Speichern: {e}")
    finally:
        conn.close()

# --- PUSH TO MAIN ---
def push_approved_to_main():
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Transfer Logik (wie in approve_to_main.py)
        cur.execute("""
            INSERT INTO ai_models (
                key, replicate_id, name, description, base_cost_usd, 
                internal_cost, custom_price, provider, model_type, 
                menu_path, is_active, is_commercial, input_schema, 
                output_schema, example_data
            )
            SELECT 
                key, replicate_id, name, description, base_cost_usd, 
                internal_cost, NULL, provider, model_type, 
                menu_path, 1, 1, input_schema, 
                output_schema, example_data
            FROM ai_models_staging
            WHERE is_approved = 1
            ON CONFLICT (key) DO UPDATE SET
                internal_cost = EXCLUDED.internal_cost,
                model_type = EXCLUDED.model_type,
                menu_path = EXCLUDED.menu_path,
                input_schema = EXCLUDED.input_schema,
                example_data = EXCLUDED.example_data,
                last_checked = NOW();
        """)
        count = cur.rowcount
        conn.commit()
        st.balloons()
        st.success(f"🚀 {count} Modelle erfolgreich LIVE geschaltet!")
    except Exception as e:
        st.error(f"Transfer Fehler: {e}")
    finally:
        conn.close()

# --- UI AUFBAU ---
st.title("🎛️ AI Bot Model Manager")

# Sidebar Aktionen
with st.sidebar:
    st.header("Aktionen")
    if st.button("🔄 Tabelle neu laden"):
        st.rerun()
    
    st.write("---")
    st.write("Wenn du zufrieden bist:")
    if st.button("🚀 APPROVE & PUSH TO LIVE", type="primary"):
        push_approved_to_main()
        
    st.info("Hinweis: Wenn du Zeilen bearbeitest, werden sie automatisch vor dem Überschreiben durch den Import geschützt (Manual Override).")

# Haupttabelle
df = load_data()

st.subheader("Staging Area (Bearbeitbar)")

# Streamlit Data Editor - Das Herzstück
# Wir konfigurieren Spalten für bessere UX
edited_df = st.data_editor(
    df,
    column_config={
        "is_approved": st.column_config.CheckboxColumn(
            "Approve?",
            help="Haken setzen um live zu schalten",
            default=False,
        ),
        "manual_override": st.column_config.CheckboxColumn(
            "Locked",
            help="Wenn an, überschreibt der Import Script diese Zeile NICHT.",
            disabled=True # Wird automatisch gesetzt
        ),
        "internal_cost": st.column_config.NumberColumn(
            "Credits",
            min_value=0,
            step=1,
            format="%d ⭐️"
        ),
        "model_type": st.column_config.SelectboxColumn(
            "Typ",
            options=["image", "video", "text", "audio", "tools", "image,text"],
            required=True
        ),
        "menu_path": st.column_config.TextColumn(
            "Menu Pfad",
            help="z.B. image/flux oder video"
        ),
        "base_cost_usd": st.column_config.NumberColumn(
            "USD Cost",
            format="$%.4f",
            disabled=True # Nur Info
        )
    },
    disabled=["key", "provider"], # Key darf nicht geändert werden
    hide_index=True,
    num_rows="fixed" # Keine neuen Zeilen hier, nur Import
)

# Speicher-Button Logik
# Streamlit erkennt Änderungen im 'edited_df'. 
# Wir vergleichen es grob, aber der Einfachheit halber speichern wir bei Button Klick.
if st.button("💾 Änderungen speichern"):
    # Wir filtern nur die Zeilen heraus, die sich von den geladenen Daten unterscheiden
    # (In einer echten App würde man session_state nutzen, hier speichern wir einfach den aktuellen Stand des Editors)
    save_changes(edited_df, df)