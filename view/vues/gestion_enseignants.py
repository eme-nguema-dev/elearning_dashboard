import streamlit as st
import sqlite3
import pandas as pd
import chardet
import io
import unicodedata
import sys
sys.path.append(".")

def get_conn():
    return sqlite3.connect("model/elearning.db")

def get_cours():
    conn = get_conn()
    df = pd.read_sql("SELECT id_cours, nom_cours FROM COURS", conn)
    conn.close()
    return df

def normalize(s):
    return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('utf-8').lower()

def parse_file(uploaded_file):
    try:
        raw = uploaded_file.read()
        excel_signature = b'PK\x03\x04'
        xls_signature = b'\xd0\xcf\x11\xe0'
        if raw[:4] == excel_signature or raw[:4] == xls_signature:
            return pd.read_excel(io.BytesIO(raw))
        file_type = uploaded_file.name.split(".")[-1].lower()
        if file_type == "csv":
            encoding = chardet.detect(raw)["encoding"] or "utf-8"
            return pd.read_csv(io.BytesIO(raw), encoding=encoding)
        elif file_type in ["xlsx", "xls"]:
            return pd.read_excel(io.BytesIO(raw))
        elif file_type == "json":
            return pd.read_json(io.BytesIO(raw))
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier : {e}")
        return None

def show_gestion_enseignants():
    st.header("Gestion des enseignants")

    tab0, tab1, tab2, tab3, tab4 = st.tabs(["📋 Liste", "➕ Ajouter", "✏️ Modifier", "🗑️ Supprimer", "📥 Importer liste"])

    df_cours = get_cours()
    cours_options = df_cours["nom_cours"].tolist()
    cours_ids = df_cours.set_index("nom_cours")["id_cours"].to_dict()

    with tab0:
        st.subheader("Liste des enseignants")
        conn = get_conn()
        df_list = pd.read_sql("""
            SELECT E.id_enseignant, E.nom, E.prenom, E.email,
                   GROUP_CONCAT(C.nom_cours, ', ') as cours_enseignes
            FROM ENSEIGNANTS E
            LEFT JOIN COURS C ON C.id_enseignant = E.id_enseignant
            GROUP BY E.id_enseignant
            ORDER BY E.nom
        """, conn)
        conn.close()

        if df_list.empty:
            st.info("Aucun enseignant disponible")
        else:
            st.markdown(f"**{len(df_list)} enseignant(s) enregistre(s)**")
            st.dataframe(df_list.rename(columns={
                "id_enseignant": "ID",
                "nom": "Nom",
                "prenom": "Prenom",
                "email": "Email",
                "cours_enseignes": "Cours enseignes"
            }), use_container_width=True)

    with tab1:
        st.subheader("Ajouter un enseignant")
        nom = st.text_input("Nom", key="add_nom")
        prenom = st.text_input("Prenom", key="add_prenom")
        email = st.text_input("Email", key="add_email")
        mot_de_passe = st.text_input("Mot de passe", type="password", key="add_mdp")

        st.markdown("**Cours enseignes**")
        cours_selectionnes = st.multiselect("Selectionner les cours", cours_options, key="add_cours")

        if st.button("Ajouter", key="add_btn"):
            if nom and prenom and email and mot_de_passe:
                try:
                    conn = get_conn()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO ENSEIGNANTS (nom, prenom, email, mot_de_passe) VALUES (?, ?, ?, ?)",
                                   (nom, prenom, email, mot_de_passe))
                    id_enseignant = cursor.lastrowid
                    for nom_cours in cours_selectionnes:
                        id_cours = cours_ids[nom_cours]
                        cursor.execute("UPDATE COURS SET id_enseignant=? WHERE id_cours=?",
                                       (id_enseignant, id_cours))
                    conn.commit()
                    conn.close()
                    st.success(f"Enseignant {prenom} {nom} ajoute avec succes")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Cet email existe deja")
            else:
                st.error("Veuillez remplir tous les champs")

    with tab2:
        st.subheader("Modifier un enseignant")
        conn = get_conn()
        df = pd.read_sql("SELECT * FROM ENSEIGNANTS", conn)
        conn.close()

        if df.empty:
            st.info("Aucun enseignant disponible")
        else:
            options = {f"{r['prenom']} {r['nom']} ({r['email']})": r['id_enseignant']
                       for _, r in df.iterrows()}
            choix = st.selectbox("Selectionner un enseignant", list(options.keys()), key="mod_select")
            id_sel = options[choix]
            enseignant = df[df["id_enseignant"] == id_sel].iloc[0]

            nom_m = st.text_input("Nom", value=enseignant["nom"], key="mod_nom")
            prenom_m = st.text_input("Prenom", value=enseignant["prenom"], key="mod_prenom")
            email_m = st.text_input("Email", value=enseignant["email"], key="mod_email")
            mdp_m = st.text_input("Mot de passe", value=enseignant["mot_de_passe"],
                                   type="password", key="mod_mdp")

            conn = get_conn()
            df_cours_ens = pd.read_sql(f"SELECT nom_cours FROM COURS WHERE id_enseignant={id_sel}", conn)
            conn.close()
            cours_actuels = df_cours_ens["nom_cours"].tolist()

            st.markdown("**Cours enseignes**")
            cours_selectionnes_m = st.multiselect("Selectionner les cours", cours_options,
                                                   default=cours_actuels, key="mod_cours")

            if st.button("Modifier", key="mod_btn"):
                try:
                    conn = get_conn()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE ENSEIGNANTS SET nom=?, prenom=?, email=?, mot_de_passe=? WHERE id_enseignant=?",
                                   (nom_m, prenom_m, email_m, mdp_m, id_sel))
                    cursor.execute("UPDATE COURS SET id_enseignant=NULL WHERE id_enseignant=?", (id_sel,))
                    for nom_cours in cours_selectionnes_m:
                        id_cours = cours_ids[nom_cours]
                        cursor.execute("UPDATE COURS SET id_enseignant=? WHERE id_cours=?",
                                       (id_sel, id_cours))
                    conn.commit()
                    conn.close()
                    st.success("Enseignant modifie avec succes")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Cet email existe deja")

    with tab3:
        st.subheader("Supprimer un enseignant")
        conn = get_conn()
        df = pd.read_sql("SELECT * FROM ENSEIGNANTS", conn)
        conn.close()

        if df.empty:
            st.info("Aucun enseignant disponible")
        else:
            options = {f"{r['prenom']} {r['nom']} ({r['email']})": r['id_enseignant']
                       for _, r in df.iterrows()}
            choix = st.selectbox("Selectionner un enseignant", list(options.keys()), key="del_select")
            id_sel = options[choix]

            st.warning(f"Vous allez supprimer : {choix}")
            if st.button("Supprimer", type="primary", key="del_btn"):
                conn = get_conn()
                cursor = conn.cursor()
                cursor.execute("UPDATE COURS SET id_enseignant=NULL WHERE id_enseignant=?", (id_sel,))
                cursor.execute("DELETE FROM ENSEIGNANTS WHERE id_enseignant=?", (id_sel,))
                conn.commit()
                conn.close()
                st.success("Enseignant supprime avec succes")
                st.rerun()

    with tab4:
        st.subheader("Importer une liste d enseignants")
        st.info("Le fichier doit contenir les colonnes : nom, prenom, email, mot_de_passe")

        if st.session_state.get("enseignant_imported", False):
            st.success("Fichier importe avec succes dans la base de donnees")
            if st.button("Importer un nouveau fichier", key="reset_import_ens"):
                st.session_state["enseignant_imported"] = False
                st.rerun()
        else:
            uploaded_file = st.file_uploader(
                "Choisir un fichier (CSV, Excel, JSON)",
                type=["csv", "xlsx", "xls", "json"],
                key="import_enseignants"
            )

            if uploaded_file:
                df_import = parse_file(uploaded_file)
                if df_import is not None:
                    st.markdown("**Apercu du fichier**")
                    st.dataframe(df_import.head(10), use_container_width=True)

                    df_import.columns = [c.lower() for c in df_import.columns]
                    colonnes_requises = ["nom", "prenom", "email", "mot_de_passe"]
                    manquantes = [c for c in colonnes_requises if c not in df_import.columns]

                    if manquantes:
                        st.error(f"Colonnes manquantes : {', '.join(manquantes)}")
                    else:
                        st.success(f"{len(df_import)} enseignant(s) detecte(s)")

                        if st.button("Importer dans la base de donnees", key="import_btn"):
                            conn = get_conn()
                            cursor = conn.cursor()
                            nb_inseres = 0
                            nb_doublons = 0

                            for _, row in df_import.iterrows():
                                cursor.execute("SELECT COUNT(*) FROM ENSEIGNANTS WHERE LOWER(email)=LOWER(?)",
                                               (str(row["email"]),))
                                existe = cursor.fetchone()[0]

                                if existe == 0:
                                    cursor.execute("INSERT INTO ENSEIGNANTS (nom, prenom, email, mot_de_passe) VALUES (?, ?, ?, ?)",
                                                   (str(row["nom"]), str(row["prenom"]),
                                                    str(row["email"]), str(row["mot_de_passe"])))
                                    id_enseignant = cursor.lastrowid

                                    if "cours_enseignes" in df_import.columns and pd.notna(row["cours_enseignes"]):
                                        cursor.execute("SELECT id_cours, nom_cours FROM COURS")
                                        tous_cours = cursor.fetchall()
                                        cours_trouve = None
                                        for id_c, nom_c in tous_cours:
                                            if normalize(nom_c) == normalize(str(row["cours_enseignes"])):
                                                cours_trouve = id_c
                                                break
                                        if cours_trouve:
                                            cursor.execute("UPDATE COURS SET id_enseignant=? WHERE id_cours=?",
                                                           (id_enseignant, cours_trouve))
                                    nb_inseres += 1
                                else:
                                    nb_doublons += 1

                            conn.commit()
                            conn.close()
                            st.success(f"{nb_inseres} enseignant(s) importe(s) avec succes")
                            if nb_doublons > 0:
                                st.warning(f"{nb_doublons} enseignant(s) ignore(s) car deja existant(s)")
                            st.session_state["enseignant_imported"] = True
                            st.rerun()
