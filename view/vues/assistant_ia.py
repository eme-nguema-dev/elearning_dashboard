import streamlit as st
import pandas as pd
import sqlite3
from google import genai
from dotenv import load_dotenv
import os
import sys
sys.path.append(".")
from controller.ml_model import get_resultats_ia, get_stats_prediction
from controller.etl import *

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_context_data(user=None):
    df = get_resultats_ia()
    stats = get_stats_prediction(df)

    conn = sqlite3.connect("model/elearning.db")

    if user and user.get("role") == "enseignant":
        id_enseignant = user["id"]
        df_cours_info = pd.read_sql(f"""
            SELECT C.id_cours, C.nom_cours
            FROM COURS C
            WHERE C.id_enseignant = {id_enseignant}
        """, conn)
    else:
        df_cours_info = pd.read_sql("""
            SELECT C.id_cours, C.nom_cours
            FROM COURS C
        """, conn)

    taux_rows = []
    for _, cours in df_cours_info.iterrows():
        id_cours = cours["id_cours"]
        nom_cours = cours["nom_cours"]

        df_etu_cours = pd.read_sql(f"""
            SELECT DISTINCT N.id_etudiant
            FROM NOTES N
            WHERE N.id_cours = {id_cours}
        """, conn)

        ids = df_etu_cours["id_etudiant"].tolist()

        if not ids:
            taux_rows.append({
                "nom_cours": nom_cours,
                "nb_etudiants": 0,
                "moyenne": 0,
                "recus_pred": 0,
                "echecs_pred": 0,
                "taux_reussite_pred": 0.0
            })
            continue

        df_pred = df[df["id_etudiant"].isin(ids)]
        total = len(df_pred)
        recus = len(df_pred[df_pred["prediction"] == "Recu"])
        echecs = total - recus
        taux = round(recus / total * 100, 1) if total > 0 else 0

        moyenne = pd.read_sql(f"""
            SELECT ROUND(AVG(note), 2) as moy FROM NOTES WHERE id_cours = {id_cours}
        """, conn).iloc[0]["moy"]

        taux_rows.append({
            "nom_cours": nom_cours,
            "nb_etudiants": total,
            "moyenne": moyenne,
            "recus_pred": recus,
            "echecs_pred": echecs,
            "taux_reussite_pred": taux
        })

    df_taux_cours = pd.DataFrame(taux_rows).sort_values("taux_reussite_pred", ascending=True)

    df_activite = pd.read_sql("""
        SELECT E.nom, E.prenom, E.classe,
               ROUND(SUM(A.temps_passe), 2) as total_temps,
               COUNT(DISTINCT A.date_connexion) as nb_connexions
        FROM ACTIVITE A
        JOIN ETUDIANTS E ON A.id_etudiant = E.id_etudiant
        GROUP BY E.id_etudiant
        ORDER BY total_temps DESC
    """, conn)

    df_enseignants = pd.read_sql("""
        SELECT E.nom, E.prenom,
               GROUP_CONCAT(C.nom_cours, ', ') as cours_enseignes
        FROM ENSEIGNANTS E
        LEFT JOIN COURS C ON C.id_enseignant = E.id_enseignant
        GROUP BY E.id_enseignant
    """, conn)

    nb_notes = pd.read_sql("SELECT COUNT(*) as total FROM NOTES", conn).iloc[0]["total"]
    conn.close()

    context = f"""
Tu es un assistant pedagogique intelligent pour un systeme e-learning.
Tu as acces aux donnees du systeme. Utilise-les pour faire des analyses precises.

STATISTIQUES GENERALES:
- Total etudiants: {stats['total']}
- Moyenne globale: {get_moyenne_globale()} / 20
- Taux de reussite reel: {get_taux_reussite()} %
- Total notes enregistrees: {nb_notes}

PREDICTIONS IA (Random Forest):
- Etudiants predicted recus: {stats['recus_pred']} ({stats['taux_reussite_pred']}%)
- Etudiants predicted echec: {stats['echecs_pred']}

CLASSIFICATION IA (K-Means):
- Niveau Bon: {stats['bon']} etudiants
- Niveau Moyen: {stats['moyen']} etudiants
- Niveau Risque: {stats['risque']} etudiants

TAUX DE REUSSITE PREDIT PAR COURS (Random Forest):
{df_taux_cours[['nom_cours', 'moyenne', 'recus_pred', 'echecs_pred', 'taux_reussite_pred', 'nb_etudiants']].to_string(index=False)}

CLASSEMENT ETUDIANTS (niveau IA et prediction):
{df[['nom', 'prenom', 'classe', 'moyenne', 'niveau', 'prediction', 'probabilite']].sort_values('moyenne', ascending=False).to_string(index=False)}

ACTIVITE DES ETUDIANTS:
{df_activite.to_string(index=False)}

ENSEIGNANTS ET LEURS COURS:
{df_enseignants.to_string(index=False)}
"""
    return context, df, stats, df_taux_cours


def generate_conclusion(context):
    prompt = f"""
{context}

Redige une analyse concise de l etat de la classe en 5 points maximum.
Chaque point doit etre sur sa propre ligne, commence par un tiret (-) et ne depasse pas 2 lignes.
Pas de titre, pas d introduction, juste les points directement.
Utilise le format Markdown et mets en gras (**texte**) les chiffres cles, niveaux de risque,
noms de cours problematiques et recommandations importantes.
Couvre: performance globale, taux de reussite predit par cours, etudiants a risque, et recommandation cle.
Reponds uniquement avec les points, rien d autre.
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text


def show_assistant_ia(user=None):
    st.header("Assistant IA")

    context, df, stats, df_taux_cours = get_context_data(user)

    # ── KPIs ──
    st.subheader("Resultats des modeles IA")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Niveau Bon", stats["bon"])
    col2.metric("Niveau Moyen", stats["moyen"])
    col3.metric("Niveau Risque", stats["risque"])
    col4.metric("Taux reussite predit", f"{stats['taux_reussite_pred']}%")

    st.divider()

    # ── Taux de réussite prédit par cours ──
    st.subheader("Taux de reussite predit par cours (IA)")

    for _, row in df_taux_cours.iterrows():
        taux = float(row["taux_reussite_pred"])
        couleur = "🟢" if taux >= 70 else "🟡" if taux >= 40 else "🔴"
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
        with col1:
            st.markdown(f"{couleur} **{row['nom_cours']}**")
        with col2:
            st.markdown(f"Moyenne: **{row['moyenne']}/20**")
        with col3:
            st.markdown(f"Recus pred: **{int(row['recus_pred'])}** / {int(row['nb_etudiants'])}")
        with col4:
            st.markdown(f"Taux predit: **{taux}%**")
        with col5:
            st.progress(int(taux) / 100)

    st.divider()

    # ── Clasificación ──
    st.subheader("Classification des etudiants par IA")
    df_display = df[["nom", "prenom", "classe", "moyenne", "niveau", "prediction", "probabilite"]].copy()
    df_display = df_display.sort_values("moyenne", ascending=False)
    st.dataframe(df_display, use_container_width=True)

    st.divider()

    # ── Conclusión IA ──
    st.subheader("Analyse et recommandations de l Assistant IA")

    if "ia_conclusion" not in st.session_state:
        with st.spinner("L Assistant IA analyse les donnees..."):
            try:
                conclusion = generate_conclusion(context)
                st.session_state["ia_conclusion"] = conclusion
            except Exception as e:
                st.error(f"Erreur : {e}")
                return

    st.markdown(st.session_state["ia_conclusion"])

    st.divider()

    # ── Export ──
    col1, col2 = st.columns(2)

    with col1:
        export_txt = f"""ASSISTANT IA - RAPPORT
{'='*50}

STATISTIQUES IA:
- Niveau Bon: {stats['bon']} etudiants
- Niveau Moyen: {stats['moyen']} etudiants
- Niveau Risque: {stats['risque']} etudiants
- Taux reussite predit global: {stats['taux_reussite_pred']}%

TAUX DE REUSSITE PREDIT PAR COURS:
{df_taux_cours[['nom_cours', 'moyenne', 'recus_pred', 'echecs_pred', 'taux_reussite_pred']].to_string(index=False)}

CONCLUSION IA:
{st.session_state.get('ia_conclusion', '')}

CLASSEMENT DES ETUDIANTS:
{df_display.to_string(index=False)}
"""
        st.download_button(
            label="Telecharger rapport TXT",
            data=export_txt.encode("utf-8"),
            file_name="rapport_assistant_ia.txt",
            mime="text/plain"
        )

    with col2:
        export_csv = df_display.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Telecharger classement CSV",
            data=export_csv,
            file_name="classement_ia.csv",
            mime="text/csv"
        )

    st.divider()

    # ── Chat ──
    st.subheader("Poser une question a l Assistant IA")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input("Posez votre question sur les etudiants...")

    if question:
        st.session_state["chat_history"].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Gemini reflechit..."):
                try:
                    history_text = "\n".join([
                        f"{m['role']}: {m['content']}"
                        for m in st.session_state["chat_history"][:-1]
                    ])
                    prompt = f"""
{context}

Historique de la conversation:
{history_text}

Question actuelle: {question}

Reponds en francais de maniere precise et pedagogique.
Utilise le format Markdown et mets en gras (**texte**) les elements importants.
"""
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt
                    )
                    answer = response.text
                    st.markdown(answer)
                    st.session_state["chat_history"].append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Erreur : {e}")

    if st.session_state["chat_history"]:
        if st.button("Effacer la conversation"):
            st.session_state["chat_history"] = []
            st.session_state.pop("ia_conclusion", None)
            st.rerun()