import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import chardet
import io
import sys
sys.path.append(".")

def get_conn():
    return sqlite3.connect("model/elearning.db")

def get_cours():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM COURS", conn)
    conn.close()
    return df

def get_classes():
    conn = get_conn()
    df = pd.read_sql("SELECT DISTINCT classe FROM ETUDIANTS ORDER BY classe", conn)
    conn.close()
    classes = df["classe"].tolist()
    classes.append("+ Nouvelle classe")
    return classes

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

def show_gestion_etudiants():
    st.header("Gestion des etudiants")

    tab0, tab1, tab2, tab3, tab4 = st.tabs(["📋 Liste", "➕ Ajouter", "✏️ Modifier", "🗑️ Supprimer", "📥 Importer liste"])

    with tab0:
        st.subheader("Liste des etudiants")
        conn = get_conn()
        df_list = pd.read_sql("""
            SELECT E.id_etudiant, E.nom, E.prenom, E.classe,
                   ROUND(AVG(N.note), 2) as moyenne,
                   CASE WHEN AVG(N.note) >= 10 THEN 'Recu' ELSE 'Echec' END as statut
            FROM ETUDIANTS E
            LEFT JOIN NOTES N ON E.id_etudiant = N.id_etudiant
            GROUP BY E.id_etudiant
            ORDER BY moyenne DESC
        """, conn)
        conn.close()

        if df_list.empty:
            st.info("Aucun etudiant disponible")
        else:
            st.markdown(f"**{len(df_list)} etudiant(s) enregistre(s)**")
            st.dataframe(df_list.rename(columns={
                "id_etudiant": "ID",
                "nom": "Nom",
                "prenom": "Prenom",
                "classe": "Classe",
                "moyenne": "Moyenne",
                "statut": "Statut"
            }), use_container_width=True)

    with tab1:
        st.subheader("Ajouter un etudiant")
        st.markdown("**Donnees personnelles**")
        nom = st.text_input("Nom", key="add_nom")
        prenom = st.text_input("Prenom", key="add_prenom")

        classes = get_classes()
        classe_sel = st.selectbox("Classe", classes, key="add_classe")
        if classe_sel == "+ Nouvelle classe":
            classe = st.text_input("Nom de la nouvelle classe", key="add_new_classe")
        else:
            classe = classe_sel

        st.divider()
        st.markdown("**Notes par cours**")
        df_cours = get_cours()
        notes = {}
        for _, cours in df_cours.iterrows():
            notes[cours["id_cours"]] = st.number_input(
                f"{cours['nom_cours']}",
                min_value=0.0, max_value=20.0, value=10.0, step=0.25,
                key=f"add_note_{cours['id_cours']}"
            )
        st.divider()
        st.markdown("**Activite**")
        temps_passe = st.number_input("Temps passe (heures)", min_value=0.0,
                                       max_value=100.0, value=5.0, step=0.5,
                                       key="add_temps")
        date_connexion = st.date_input("Date de connexion", value=date.today(),
                                        key="add_date")
        if st.button("Ajouter", key="add_btn"):
            if nom and prenom and classe:
                conn = get_conn()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO ETUDIANTS (nom, prenom, classe) VALUES (?, ?, ?)",
                               (nom, prenom, classe))
                id_etudiant = cursor.lastrowid
                for id_cours, note in notes.items():
                    cursor.execute("INSERT INTO NOTES (id_etudiant, id_cours, note) VALUES (?, ?, ?)",
                                   (id_etudiant, id_cours, note))
                cursor.execute("INSERT INTO ACTIVITE (id_etudiant, temps_passe, date_connexion) VALUES (?, ?, ?)",
                               (id_etudiant, temps_passe, str(date_connexion)))
                conn.commit()
                conn.close()
                st.success(f"Etudiant {prenom} {nom} ajoute avec succes")
                st.rerun()
            else:
                st.error("Veuillez remplir tous les champs")

    with tab2:
        st.subheader("Modifier un etudiant")
        conn = get_conn()
        df = pd.read_sql("SELECT * FROM ETUDIANTS", conn)
        conn.close()

        if df.empty:
            st.info("Aucun etudiant disponible")
        else:
            options = {f"{r['prenom']} {r['nom']} ({r['classe']})": r['id_etudiant']
                       for _, r in df.iterrows()}
            choix = st.selectbox("Selectionner un etudiant", list(options.keys()), key="mod_select")
            id_sel = options[choix]
            etudiant = df[df["id_etudiant"] == id_sel].iloc[0]

            st.markdown("**Donnees personnelles**")
            nom_m = st.text_input("Nom", value=etudiant["nom"], key="mod_nom")
            prenom_m = st.text_input("Prenom", value=etudiant["prenom"], key="mod_prenom")

            classes = get_classes()
            classe_index = classes.index(etudiant["classe"]) if etudiant["classe"] in classes else 0
            classe_sel_m = st.selectbox("Classe", classes, index=classe_index, key="mod_classe")
            if classe_sel_m == "+ Nouvelle classe":
                classe_m = st.text_input("Nom de la nouvelle classe", key="mod_new_classe")
            else:
                classe_m = classe_sel_m

            st.divider()
            st.markdown("**Notes par cours**")
            df_cours = get_cours()
            conn = get_conn()
            df_notes = pd.read_sql(f"SELECT * FROM NOTES WHERE id_etudiant={id_sel}", conn)
            conn.close()

            notes_m = {}
            for _, cours in df_cours.iterrows():
                note_row = df_notes[df_notes["id_cours"] == cours["id_cours"]]
                val = float(note_row["note"].values[0]) if not note_row.empty else 10.0
                notes_m[cours["id_cours"]] = st.number_input(
                    f"{cours['nom_cours']}",
                    min_value=0.0, max_value=20.0, value=val, step=0.25,
                    key=f"mod_note_{cours['id_cours']}"
                )
            st.divider()
            st.markdown("**Activite**")
            conn = get_conn()
            df_act = pd.read_sql(f"SELECT * FROM ACTIVITE WHERE id_etudiant={id_sel}", conn)
            conn.close()

            temps_val = float(df_act["temps_passe"].values[0]) if not df_act.empty else 5.0
            temps_m = st.number_input("Temps passe (heures)", min_value=0.0,
                                       max_value=100.0, value=temps_val, step=0.5,
                                       key="mod_temps")
            date_m = st.date_input("Date de connexion", key="mod_date")

            if st.button("Modifier", key="mod_btn"):
                conn = get_conn()
                cursor = conn.cursor()
                cursor.execute("UPDATE ETUDIANTS SET nom=?, prenom=?, classe=? WHERE id_etudiant=?",
                               (nom_m, prenom_m, classe_m, id_sel))
                for id_cours, note in notes_m.items():
                    if not df_notes[df_notes["id_cours"] == id_cours].empty:
                        cursor.execute("UPDATE NOTES SET note=? WHERE id_etudiant=? AND id_cours=?",
                                       (note, id_sel, id_cours))
                    else:
                        cursor.execute("INSERT INTO NOTES (id_etudiant, id_cours, note) VALUES (?, ?, ?)",
                                       (id_sel, id_cours, note))
                if not df_act.empty:
                    cursor.execute("UPDATE ACTIVITE SET temps_passe=?, date_connexion=? WHERE id_etudiant=?",
                                   (temps_m, str(date_m), id_sel))
                else:
                    cursor.execute("INSERT INTO ACTIVITE (id_etudiant, temps_passe, date_connexion) VALUES (?, ?, ?)",
                                   (id_sel, temps_m, str(date_m)))
                conn.commit()
                conn.close()
                st.success("Etudiant modifie avec succes")
                st.rerun()

    with tab3:
        st.subheader("Supprimer un etudiant")
        conn = get_conn()
        df = pd.read_sql("SELECT * FROM ETUDIANTS", conn)
        conn.close()

        if df.empty:
            st.info("Aucun etudiant disponible")
        else:
            options = {f"{r['prenom']} {r['nom']} ({r['classe']})": r['id_etudiant']
                       for _, r in df.iterrows()}
            choix = st.selectbox("Selectionner un etudiant", list(options.keys()), key="del_select")
            id_sel = options[choix]

            st.warning(f"Vous allez supprimer : {choix}")
            if st.button("Supprimer", type="primary", key="del_btn"):
                conn = get_conn()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM NOTES WHERE id_etudiant=?", (id_sel,))
                cursor.execute("DELETE FROM ACTIVITE WHERE id_etudiant=?", (id_sel,))
                cursor.execute("DELETE FROM ETUDIANTS WHERE id_etudiant=?", (id_sel,))
                conn.commit()
                conn.close()
                st.success("Etudiant supprime avec succes")
                st.rerun()

    with tab4:
        st.subheader("Importer une liste d etudiants")
        st.info("Le fichier doit contenir les colonnes : nom, prenom, classe")

        if st.session_state.get("etudiant_imported", False):
            st.success("Fichier importe avec succes dans la base de donnees")
            if st.button("Importer un nouveau fichier", key="reset_import_etu"):
                st.session_state["etudiant_imported"] = False
                st.rerun()
        else:
            uploaded_file = st.file_uploader(
                "Choisir un fichier (CSV, Excel, JSON)",
                type=["csv", "xlsx", "xls", "json"],
                key="import_etudiants"
            )

            if uploaded_file:
                df_import = parse_file(uploaded_file)
                if df_import is not None:
                    st.markdown("**Apercu du fichier**")
                    st.dataframe(df_import.head(10), use_container_width=True)

                    df_import.columns = [c.lower() for c in df_import.columns]
                    colonnes_requises = ["nom", "prenom", "classe"]
                    manquantes = [c for c in colonnes_requises if c not in df_import.columns]

                    if manquantes:
                        st.error(f"Colonnes manquantes : {', '.join(manquantes)}")
                    else:
                        st.success(f"{len(df_import)} etudiant(s) detecte(s)")

                        if st.button("Importer dans la base de donnees", key="import_btn"):
                            conn = get_conn()
                            cursor = conn.cursor()
                            nb_inseres = 0
                            nb_doublons = 0

                            for _, row in df_import.iterrows():
                                cursor.execute("""
                                    SELECT COUNT(*) FROM ETUDIANTS
                                    WHERE LOWER(nom)=LOWER(?) AND LOWER(prenom)=LOWER(?) AND LOWER(classe)=LOWER(?)
                                """, (str(row["nom"]), str(row["prenom"]), str(row["classe"])))
                                existe = cursor.fetchone()[0]

                                if existe == 0:
                                    cursor.execute("INSERT INTO ETUDIANTS (nom, prenom, classe) VALUES (?, ?, ?)",
                                                   (str(row["nom"]), str(row["prenom"]), str(row["classe"])))
                                    id_etudiant = cursor.lastrowid

                                    cursor.execute("SELECT id_cours FROM COURS")
                                    cours_ids = cursor.fetchall()
                                    for (id_cours,) in cours_ids:
                                        cursor.execute("INSERT INTO NOTES (id_etudiant, id_cours, note) VALUES (?, ?, ?)",
                                                       (id_etudiant, id_cours, 0.0))

                                    cursor.execute("INSERT INTO ACTIVITE (id_etudiant, temps_passe, date_connexion) VALUES (?, ?, ?)",
                                                   (id_etudiant, 0.0, '2024-01-01'))
                                    nb_inseres += 1
                                else:
                                    nb_doublons += 1

                            conn.commit()
                            conn.close()
                            st.success(f"{nb_inseres} etudiant(s) importe(s) avec succes")
                            if nb_doublons > 0:
                                st.warning(f"{nb_doublons} etudiant(s) ignore(s) car deja existant(s)")
                            st.session_state["etudiant_imported"] = True
                            st.rerun()