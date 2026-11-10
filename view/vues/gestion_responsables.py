import streamlit as st
import sqlite3
import pandas as pd
import sys
sys.path.append(".")

def get_conn():
    return sqlite3.connect("model/elearning.db")

def show_gestion_responsables():
    st.header("👨‍💼 Gestion des responsables pédagogiques")

    tab1, tab2, tab3 = st.tabs(["➕ Ajouter", "✏️ Modifier", "🗑️ Supprimer"])

    # ── AJOUTER ──────────────────────────────────────────
    with tab1:
        st.subheader("Ajouter un responsable pédagogique")
        nom = st.text_input("Nom")
        prenom = st.text_input("Prénom")
        email = st.text_input("Email")
        mot_de_passe = st.text_input("Mot de passe", type="password")
        departement = st.text_input("Département")

        if st.button("Ajouter"):
            if nom and prenom and email and mot_de_passe and departement:
                try:
                    conn = get_conn()
                    conn.execute("""INSERT INTO RESPONSABLE_PEDAGOGIQUE 
                                    (nom, prenom, email, mot_de_passe, departement) 
                                    VALUES (?, ?, ?, ?, ?)""",
                                 (nom, prenom, email, mot_de_passe, departement))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Responsable {prenom} {nom} ajouté avec succès")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("❌ Cet email existe déjà")
            else:
                st.error("❌ Veuillez remplir tous les champs")

    # ── MODIFIER ─────────────────────────────────────────
    with tab2:
        st.subheader("Modifier un responsable pédagogique")
        conn = get_conn()
        df = pd.read_sql("SELECT * FROM RESPONSABLE_PEDAGOGIQUE", conn)
        conn.close()

        if df.empty:
            st.info("Aucun responsable disponible")
        else:
            options = {f"{r['prenom']} {r['nom']} ({r['email']})": r['id_responsable']
                       for _, r in df.iterrows()}
            choix = st.selectbox("Sélectionner un responsable", list(options.keys()))
            id_sel = options[choix]
            resp = df[df["id_responsable"] == id_sel].iloc[0]

            nom_m = st.text_input("Nom", value=resp["nom"], key="nom_m")
            prenom_m = st.text_input("Prénom", value=resp["prenom"], key="prenom_m")
            email_m = st.text_input("Email", value=resp["email"], key="email_m")
            mdp_m = st.text_input("Mot de passe", value=resp["mot_de_passe"],
                                   type="password", key="mdp_m")
            dept_m = st.text_input("Département", value=resp["departement"], key="dept_m")

            if st.button("Modifier"):
                try:
                    conn = get_conn()
                    conn.execute("""UPDATE RESPONSABLE_PEDAGOGIQUE 
                                    SET nom=?, prenom=?, email=?, mot_de_passe=?, departement=?
                                    WHERE id_responsable=?""",
                                 (nom_m, prenom_m, email_m, mdp_m, dept_m, id_sel))
                    conn.commit()
                    conn.close()
                    st.success("✅ Responsable modifié avec succès")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("❌ Cet email existe déjà")

    # ── SUPPRIMER ────────────────────────────────────────
    with tab3:
        st.subheader("Supprimer un responsable pédagogique")
        conn = get_conn()
        df = pd.read_sql("SELECT * FROM RESPONSABLE_PEDAGOGIQUE", conn)
        conn.close()

        if df.empty:
            st.info("Aucun responsable disponible")
        else:
            options = {f"{r['prenom']} {r['nom']} ({r['email']})": r['id_responsable']
                       for _, r in df.iterrows()}
            choix = st.selectbox("Sélectionner un responsable", list(options.keys()), key="del")
            id_sel = options[choix]

            st.warning(f"⚠️ Vous allez supprimer : {choix}")
            if st.button("Supprimer", type="primary"):
                conn = get_conn()
                conn.execute("DELETE FROM RESPONSABLE_PEDAGOGIQUE WHERE id_responsable=?",
                             (id_sel,))
                conn.commit()
                conn.close()
                st.success("✅ Responsable supprimé avec succès")
                st.rerun()