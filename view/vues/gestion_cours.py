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

def get_enseignants():
    conn = get_conn()
    df = pd.read_sql("SELECT id_enseignant, nom, prenom FROM ENSEIGNANTS", conn)
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

def show_gestion_cours():
    st.header("Gestion des cours")

    tab0, tab1, tab2, tab3, tab4 = st.tabs(["📋 Liste", "➕ Ajouter", "✏️ Modifier", "🗑️ Supprimer", "📥 Importer liste"])

    df_ens = get_enseignants()
    ens_options = {f"{r['prenom']} {r['nom']}": r['id_enseignant']
                   for _, r in df_ens.iterrows()}

    with tab0:
        st.subheader("Liste des cours")
        conn = get_conn()
        df_list = pd.read_sql("""
            SELECT C.id_cours, C.nom_cours, C.module,
                   E.nom || ' ' || E.prenom as enseignant
            FROM COURS C
            LEFT JOIN ENSEIGNANTS E ON C.id_enseignant = E.id_enseignant
            ORDER BY C.nom_cours
        """, conn)
        conn.close()

        if df_list.empty:
            st.info("Aucun cours disponible")
        else:
            st.markdown(f"**{len(df_list)} cours enregistre(s)**")
            st.dataframe(df_list.rename(columns={
                "id_cours": "ID",
                "nom_cours": "Nom du cours",
                "module": "Module",
                "enseignant": "Enseignant"
            }), use_container_width=True)

    with tab1:
        st.subheader("Ajouter un cours")
        nom_cours = st.text_input("Nom du cours", key="add_nom")
        module = st.text_input("Module", key="add_module")
        enseignant = st.selectbox("Enseignant responsable",
                                   list(ens_options.keys()), key="add_ens")
        if st.button("Ajouter", key="add_btn"):
            if nom_cours and module:
                conn = get_conn()
                conn.execute("INSERT INTO COURS (nom_cours, module, id_enseignant) VALUES (?, ?, ?)",
                             (nom_cours, module, ens_options[enseignant]))
                conn.commit()
                conn.close()
                st.success(f"Cours '{nom_cours}' ajoute avec succes")
                st.rerun()
            else:
                st.error("Veuillez remplir tous les champs")

    with tab2:
        st.subheader("Modifier un cours")
        conn = get_conn()
        df = pd.read_sql("SELECT * FROM COURS", conn)
        conn.close()

        if df.empty:
            st.info("Aucun cours disponible")
        else:
            options = {f"{r['nom_cours']} ({r['module']})": r['id_cours']
                       for _, r in df.iterrows()}
            choix = st.selectbox("Selectionner un cours", list(options.keys()), key="mod_select")
            id_sel = options[choix]
            cours = df[df["id_cours"] == id_sel].iloc[0]

            nom_m = st.text_input("Nom du cours", value=cours["nom_cours"], key="mod_nom")
            module_m = st.text_input("Module", value=cours["module"], key="mod_module")

            ens_actuel = df_ens[df_ens["id_enseignant"] == cours["id_enseignant"]]
            ens_actuel_nom = f"{ens_actuel['prenom'].values[0]} {ens_actuel['nom'].values[0]}" \
                             if not ens_actuel.empty else list(ens_options.keys())[0]
            ens_index = list(ens_options.keys()).index(ens_actuel_nom) \
                        if ens_actuel_nom in ens_options else 0

            enseignant_m = st.selectbox("Enseignant responsable",
                                         list(ens_options.keys()),
                                         index=ens_index, key="mod_ens")

            if st.button("Modifier", key="mod_btn"):
                conn = get_conn()
                conn.execute("UPDATE COURS SET nom_cours=?, module=?, id_enseignant=? WHERE id_cours=?",
                             (nom_m, module_m, ens_options[enseignant_m], id_sel))
                conn.commit()
                conn.close()
                st.success("Cours modifie avec succes")
                st.rerun()

    with tab3:
        st.subheader("Supprimer un cours")
        conn = get_conn()
        df = pd.read_sql("SELECT * FROM COURS", conn)
        conn.close()

        if df.empty:
            st.info("Aucun cours disponible")
        else:
            options = {f"{r['nom_cours']} ({r['module']})": r['id_cours']
                       for _, r in df.iterrows()}
            choix = st.selectbox("Selectionner un cours", list(options.keys()), key="del_select")
            id_sel = options[choix]

            st.warning(f"Vous allez supprimer : {choix}")
            if st.button("Supprimer", type="primary", key="del_btn"):
                conn = get_conn()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM NOTES WHERE id_cours=?", (id_sel,))
                cursor.execute("DELETE FROM COURS WHERE id_cours=?", (id_sel,))
                conn.commit()
                conn.close()
                st.success("Cours supprime avec succes")
                st.rerun()

    with tab4:
        st.subheader("Importer une liste de cours")
        st.info("Le fichier doit contenir les colonnes : nom_cours, module")

        if st.session_state.get("cours_imported", False):
            st.success("Fichier importe avec succes dans la base de donnees")
            if st.button("Importer un nouveau fichier", key="reset_import_cours"):
                st.session_state["cours_imported"] = False
                st.rerun()
        else:
            uploaded_file = st.file_uploader(
                "Choisir un fichier (CSV, Excel, JSON)",
                type=["csv", "xlsx", "xls", "json"],
                key="import_cours"
            )

            if uploaded_file:
                df_import = parse_file(uploaded_file)
                if df_import is not None:
                    st.markdown("**Apercu du fichier**")
                    st.dataframe(df_import.head(10), use_container_width=True)

                    df_import.columns = [c.lower() for c in df_import.columns]
                    colonnes_requises = ["nom_cours", "module"]
                    manquantes = [c for c in colonnes_requises if c not in df_import.columns]

                    if manquantes:
                        st.error(f"Colonnes manquantes : {', '.join(manquantes)}")
                    else:
                        st.success(f"{len(df_import)} cours detecte(s)")

                        if st.button("Importer dans la base de donnees", key="import_btn"):
                            conn = get_conn()
                            cursor = conn.cursor()
                            nb_inseres = 0
                            nb_doublons = 0

                            for _, row in df_import.iterrows():
                                cursor.execute("""
                                    SELECT COUNT(*) FROM COURS
                                    WHERE LOWER(nom_cours)=LOWER(?) AND LOWER(module)=LOWER(?)
                                """, (str(row["nom_cours"]), str(row["module"])))
                                existe = cursor.fetchone()[0]

                                if existe == 0:
                                    id_enseignant = None
                                    if "enseignant" in df_import.columns and pd.notna(row.get("enseignant")):
                                        cursor.execute("SELECT id_enseignant, nom, prenom FROM ENSEIGNANTS")
                                        tous_ens = cursor.fetchall()
                                        for id_e, nom_e, prenom_e in tous_ens:
                                            # Comparar "Prenom Nom" y "Nom Prenom"
                                            nom_complet1 = normalize(f"{prenom_e} {nom_e}")
                                            nom_complet2 = normalize(f"{nom_e} {prenom_e}")
                                            nom_fichier = normalize(str(row["enseignant"]))
                                            if nom_fichier == nom_complet1 or nom_fichier == nom_complet2:
                                                id_enseignant = id_e
                                                break

                                    cursor.execute("INSERT INTO COURS (nom_cours, module, id_enseignant) VALUES (?, ?, ?)",
                                                (str(row["nom_cours"]), str(row["module"]), id_enseignant))
                                    nb_inseres += 1
                                else:
                                    nb_doublons += 1
                            conn.commit()
                            conn.close()
                            st.success(f"{nb_inseres} cours importe(s) avec succes")
                            if nb_doublons > 0:
                                st.warning(f"{nb_doublons} cours ignore(s) car deja existant(s)")
                            st.session_state["cours_imported"] = True
                            st.rerun()
