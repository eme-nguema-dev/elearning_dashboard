import streamlit as st
import sqlite3
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import chardet
import io
import sys
sys.path.append(".")

def get_conn():
    return sqlite3.connect("model/elearning.db")

def parse_file(uploaded_file, file_type):
    try:
        raw = uploaded_file.read()

        excel_signature = b'PK\x03\x04'
        xls_signature = b'\xd0\xcf\x11\xe0'

        if raw[:4] == excel_signature or raw[:4] == xls_signature:
            return pd.read_excel(io.BytesIO(raw))

        if file_type == "csv":
            encoding = chardet.detect(raw)["encoding"] or "utf-8"
            return pd.read_csv(io.BytesIO(raw), encoding=encoding)
        elif file_type in ["xlsx", "xls"]:
            return pd.read_excel(io.BytesIO(raw))
        elif file_type == "json":
            return pd.read_json(io.BytesIO(raw))
        elif file_type == "xml":
            tree = ET.fromstring(raw)
            data = [{child.tag: child.text for child in row} for row in tree]
            return pd.DataFrame(data)
        elif file_type == "sql":
            return raw.decode("utf-8", errors="replace")
    except Exception as e:
        st.error(f"❌ Erreur lors de la lecture du fichier : {e}")
        return None

def show_analyse(df):
    import plotly.express as px

    st.subheader("📊 Analyse des données importées")

    col1, col2, col3 = st.columns(3)
    col1.metric("Nombre de lignes", df.shape[0])
    col2.metric("Nombre de colonnes", df.shape[1])
    col3.metric("Valeurs manquantes", int(df.isnull().sum().sum()))

    st.divider()
    st.markdown("**Aperçu et édition des données**")
    
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="data_editor")
    
    # Guardar cambios si el df fue editado
    if not edited_df.equals(df):
        st.session_state["imported_df"] = edited_df
        df = edited_df

    st.divider()
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if num_cols:
        st.markdown("**Statistiques descriptives**")
        st.dataframe(df[num_cols].describe().round(2), use_container_width=True)

        st.markdown("**Distribution des colonnes numériques**")

        default_index = 0
        if "dist_col_value" in st.session_state and st.session_state["dist_col_value"] in num_cols:
            default_index = num_cols.index(st.session_state["dist_col_value"])

        col_sel = st.selectbox("Sélectionner une colonne", num_cols,
                                index=default_index, key="dist_col")
        st.session_state["dist_col_value"] = col_sel

        fig = px.histogram(df, x=col_sel, nbins=20,
                           title=f"Distribution de {col_sel}",
                           color_discrete_sequence=["#378ADD"])
        st.plotly_chart(fig, use_container_width=True)

    return df.describe().round(2).to_json()

def save_import(nom_import, type_fichier, id_utilisateur, role_utilisateur, df, contenu_rapport):
    conn = get_conn()
    cursor = conn.cursor()
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""INSERT INTO IMPORTS (nom_import, type_fichier, date_import,
                      id_utilisateur, role_utilisateur, donnees)
                      VALUES (?, ?, ?, ?, ?, ?)""",
                   (nom_import, type_fichier, date_now,
                    id_utilisateur, role_utilisateur, df.to_json()))
    id_import = cursor.lastrowid
    cursor.execute("""INSERT INTO RAPPORTS_IMPORTS (id_import, contenu_rapport, date_rapport)
                      VALUES (?, ?, ?)""",
                   (id_import, contenu_rapport, date_now))
    conn.commit()
    conn.close()
    return id_import

def show_import_donnees(user, import_id=None):
    st.header("📂 Import des données")

    # ── CHARGER UN IMPORT EXISTANT DEPUIS HISTORIQUE ──────
    if import_id and "imported_df" not in st.session_state:
        conn = get_conn()
        row = pd.read_sql(f"SELECT * FROM IMPORTS WHERE id_import={import_id}", conn)
        conn.close()
        if not row.empty:
            st.session_state["imported_df"] = pd.read_json(io.StringIO(row["donnees"].values[0]))
            st.session_state["imported_nom"] = row['nom_import'].values[0]
            st.session_state["imported_saved"] = True

    # ── NOUVEAU IMPORT ────────────────────────────────────
    st.subheader("Importer un fichier")
    nom_import = st.text_input("Nom de l'import",
                                placeholder="Ex: Notes S1 2024",
                                value=st.session_state.get("imported_nom", ""))

    uploaded_file = st.file_uploader(
        "Choisir un fichier",
        type=["csv", "xlsx", "xls", "json", "xml", "sql"]
    )

    if uploaded_file:
        file_type = uploaded_file.name.split(".")[-1].lower()
        st.info(f"📄 Fichier détecté : **{uploaded_file.name}** ({file_type.upper()})")
        if file_type == "sql":
            content = parse_file(uploaded_file, file_type)
            st.subheader("Contenu SQL")
            st.code(content, language="sql")
        else:
            df = parse_file(uploaded_file, file_type)
            if df is not None:
                st.session_state["imported_df"] = df
                st.session_state["imported_nom"] = nom_import
                st.session_state["imported_saved"] = False
                st.session_state.pop("dist_col_value", None)

    # ── AFFICHER LES DONNÉES EN SESSION ──────────────────
    if "imported_df" in st.session_state:
        if import_id:
            st.info(f"📁 Import chargé : **{st.session_state.get('imported_nom', '')}**")
        df = st.session_state["imported_df"]
        contenu_rapport = show_analyse(df)

        if not st.session_state.get("imported_saved", False):
            st.divider()
            st.subheader("💾 Sauvegarder l'import")
            if st.button("Sauvegarder", key="save_btn"):
                if nom_import:
                    save_import(nom_import, "CSV",
                                user["id"], user["role"],
                                df, contenu_rapport)
                    st.success(f"✅ Import '{nom_import}' sauvegardé avec succès")
                    st.session_state["imported_saved"] = True
                    st.rerun()
                else:
                    st.error("❌ Veuillez donner un nom à l'import")