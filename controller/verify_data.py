import sqlite3
import pandas as pd

try:
    conn = sqlite3.connect("elearning.db")

    tables = ["ENSEIGNANTS", "ADMINISTRATION", "RESPONSABLE_PEDAGOGIQUE",
              "ETUDIANTS", "COURS", "NOTES", "ACTIVITE"]

    for table in tables:
        df = pd.read_sql(f"SELECT * FROM {table}", conn)
        print(f"\n── {table} ({len(df)} enregistrements) ──")
        print(df.head(3).to_string(index=False))

    conn.close()
    print("\n✅ Vérification terminée")

except Exception as e:
    print(f"❌ Erreur : {e}")