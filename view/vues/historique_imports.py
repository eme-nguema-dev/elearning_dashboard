import streamlit as st
import sqlite3
import pandas as pd
import sys
sys.path.append(".")

def get_conn():
    return sqlite3.connect("model/elearning.db")

def show_historique_imports(user):
    st.header("🗂️ Historique des imports")

    conn = get_conn()
    df = pd.read_sql(f"""
        SELECT I.id_import, I.nom_import, I.type_fichier, I.date_import
        FROM IMPORTS I
        WHERE I.id_utilisateur = {user['id']}
        AND I.role_utilisateur = '{user['role']}'
        ORDER BY I.date_import DESC
    """, conn)
    conn.close()

    if df.empty:
        st.info("Aucun import sauvegardé pour le moment.")
        return

    st.markdown(f"**{len(df)} import(s) sauvegardé(s)**")
    st.divider()

    for _, row in df.iterrows():
        col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 1, 1])
        with col1:
            st.markdown(f"📁 **{row['nom_import']}**")
        with col2:
            st.markdown(f"`{row['type_fichier']}`")
        with col3:
            st.markdown(f"🕐 {row['date_import']}")
        with col4:
            if st.button("Ouvrir", key=f"open_{row['id_import']}"):
                st.session_state["import_id"] = int(row["id_import"])
                st.session_state["nav_page"] = "Import des données"
                st.rerun()
        with col5:
            if st.button("🗑️", key=f"del_{row['id_import']}"):
                st.session_state[f"confirm_del_{row['id_import']}"] = True
                st.rerun()

        if st.session_state.get(f"confirm_del_{row['id_import']}", False):
            st.warning(f"⚠️ Supprimer **{row['nom_import']}** ?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Confirmer", key=f"confirm_yes_{row['id_import']}", type="primary"):
                    conn = get_conn()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM RAPPORTS_IMPORTS WHERE id_import=?", (row['id_import'],))
                    cursor.execute("DELETE FROM IMPORTS WHERE id_import=?", (row['id_import'],))
                    conn.commit()
                    conn.close()
                    st.session_state.pop(f"confirm_del_{row['id_import']}", None)
                    st.success("✅ Import supprimé avec succès")
                    st.rerun()
            with c2:
                if st.button("Annuler", key=f"confirm_no_{row['id_import']}"):
                    st.session_state.pop(f"confirm_del_{row['id_import']}", None)
                    st.rerun()

        st.divider()