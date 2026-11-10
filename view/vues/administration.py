import streamlit as st
import plotly.express as px
import sqlite3
import pandas as pd
import subprocess
import os
import sys
sys.path.append(".")
from controller.etl import *
from controller.notificaciones import (
    enviar_notificacion_profesores,
    enviar_notificacion_responsables,
    enviar_notificacion_administradores,
    ejecutar_todas_notificaciones,
    get_etudiants_sin_notas_por_profesor,
    get_peor_profesor
)
from view.vues.rapports.rapport_administration import show_rapport_administration
from view.vues.gestion_etudiants import show_gestion_etudiants
from view.vues.gestion_enseignants import show_gestion_enseignants
from view.vues.gestion_responsables import show_gestion_responsables

FRECUENCIAS = {
    "Quotidien": "quotidien",
    "Hebdomadaire": "hebdomadaire",
    "Mensuel": "mensuel"
}
FRECUENCIAS_INV = {v: k for k, v in FRECUENCIAS.items()}

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
JOURS_MAP = {
    "Lundi": "MON", "Mardi": "TUE", "Mercredi": "WED",
    "Jeudi": "THU", "Vendredi": "FRI", "Samedi": "SAT", "Dimanche": "SUN"
}

def get_conn():
    return sqlite3.connect("model/elearning.db")

def get_config():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM NOTIFICACIONES_CONFIG WHERE id = 1", conn)
    conn.close()
    return df.iloc[0]

def save_config(activa, frecuencia, hora, dia_semana):
    conn = get_conn()
    conn.execute("""
        UPDATE NOTIFICACIONES_CONFIG
        SET activa=?, frecuencia=?, hora=?, dia_semana=?
        WHERE id=1
    """, (activa, frecuencia, hora, dia_semana))
    conn.commit()
    conn.close()

def setup_windows_task(hora, frecuencia, dia_semana):
    script_path = os.path.abspath("controller/scheduler_script.py")
    python_path = sys.executable
    task_name = "ElearningNotificaciones"

    subprocess.run(
        f'schtasks /delete /tn "{task_name}" /f',
        shell=True, capture_output=True
    )

    if frecuencia == "quotidien":
        schedule = f'/sc DAILY /st {hora}'
    elif frecuencia == "hebdomadaire":
        day = JOURS_MAP.get(dia_semana, "MON")
        schedule = f'/sc WEEKLY /d {day} /st {hora}'
    elif frecuencia == "mensuel":
        schedule = f'/sc MONTHLY /d 1 /st {hora}'

    cmd = f'schtasks /create /tn "{task_name}" /tr "{python_path} {script_path}" {schedule} /f'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0

def show_notificaciones(user):
    st.header("Configuration des notifications")

    config = get_config()

    st.subheader("Parametres d envoi automatique")

    activa = st.toggle(
        "Activer les notifications automatiques",
        value=bool(config["activa"])
    )

    # Frecuencia actual en francés
    freq_actual_fr = FRECUENCIAS_INV.get(config["frecuencia"], "Quotidien")

    col1, col2 = st.columns(2)
    with col1:
        freq_label = st.selectbox(
            "Frequence",
            list(FRECUENCIAS.keys()),
            index=list(FRECUENCIAS.keys()).index(freq_actual_fr),
            disabled=not activa
        )
        frecuencia = FRECUENCIAS[freq_label]
    with col2:
        hora = st.time_input(
            "Heure d envoi",
            value=pd.Timestamp(f"2024-01-01 {config['hora']}").time(),
            disabled=not activa
        )

    dia_semana = "Lundi"
    if frecuencia == "hebdomadaire" and activa:
        dia_actual = config["dia_semana"] if config["dia_semana"] in JOURS else "Lundi"
        dia_semana = st.selectbox(
            "Jour de la semaine",
            JOURS,
            index=JOURS.index(dia_actual)
        )

    if st.button("Sauvegarder la configuration", type="primary"):
        hora_str = hora.strftime("%H:%M")
        save_config(int(activa), frecuencia, hora_str, dia_semana)
        if activa:
            ok = setup_windows_task(hora_str, frecuencia, dia_semana)
            if ok:
                st.success("Configuration sauvegardee et tache Windows programmee")
            else:
                st.warning("Configuration sauvegardee mais erreur Windows — verifiez les permissions administrateur")
        else:
            subprocess.run(
                'schtasks /delete /tn "ElearningNotificaciones" /f',
                shell=True, capture_output=True
            )
            st.success("Notifications desactivees")

    if config["ultimo_envio"]:
        st.info(f"Dernier envoi automatique : {config['ultimo_envio']}")

    st.divider()
    st.subheader("Envoi manuel immediat")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Envoyer aux professeurs"):
            with st.spinner("Envoi en cours..."):
                n = enviar_notificacion_profesores()
                st.success(f"{n} email(s) envoye(s) aux professeurs")
    with col2:
        if st.button("Envoyer aux responsables"):
            with st.spinner("Envoi en cours..."):
                n = enviar_notificacion_responsables()
                st.success(f"{n} email(s) envoye(s) aux responsables")
    with col3:
        if st.button("Envoyer a tous"):
            with st.spinner("Envoi en cours..."):
                p, r, a = ejecutar_todas_notificaciones()
                st.success(f"Envoye — Professeurs: {p}, Responsables: {r}, Admins: {a}")

    st.divider()
    st.subheader("Apercu des donnees a envoyer")

    tab1, tab2 = st.tabs(["Etudiants avec note 0", "Cours avec la plus faible moyenne"])

    with tab1:
        df_sin_notas = get_etudiants_sin_notas_por_profesor()
        if df_sin_notas.empty:
            st.success("Aucun etudiant avec note 0")
        else:
            st.dataframe(
                df_sin_notas[["nom", "prenom", "nom_etudiant", "prenom_etudiant", "nom_cours"]].rename(columns={
                    "nom": "Enseignant nom",
                    "prenom": "Enseignant prenom",
                    "nom_etudiant": "Etudiant nom",
                    "prenom_etudiant": "Etudiant prenom",
                    "nom_cours": "Cours"
                }),
                use_container_width=True
            )

    with tab2:
        df_peor = get_peor_profesor()
        if df_peor.empty:
            st.info("Aucune donnee disponible")
        else:
            st.dataframe(df_peor.rename(columns={
                "nom": "Enseignant nom",
                "prenom": "Enseignant prenom",
                "nom_cours": "Cours",
                "moyenne": "Moyenne"
            }), use_container_width=True)


def show_administration(user, page):

    if page == "Statistiques globales":
        st.header("Statistiques globales")
        col1, col2, col3 = st.columns(3)
        col1.metric("Moyenne globale", f"{get_moyenne_globale()} / 20")
        col2.metric("Taux de reussite", f"{get_taux_reussite()} %")
        col3.metric("Total etudiants", get_total_etudiants())
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Reussite par cours")
            df_cours = get_notes_par_cours()
            fig = px.pie(df_cours, names="nom_cours", values="moyenne",
                         title="Repartition des moyennes par cours")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("Etudiants par classe")
            conn = sqlite3.connect("model/elearning.db")
            df_classe = pd.read_sql("""
                SELECT classe, COUNT(*) as total
                FROM ETUDIANTS
                GROUP BY classe
            """, conn)
            conn.close()
            fig2 = px.pie(df_classe, names="classe", values="total",
                          title="Repartition des etudiants par classe")
            st.plotly_chart(fig2, use_container_width=True)
        st.divider()
        st.subheader("Etudiants en difficulte")
        st.dataframe(get_etudiants_en_difficulte(), use_container_width=True)

    elif page == "Gestion des etudiants":
        show_gestion_etudiants()

    elif page == "Gestion des enseignants":
        show_gestion_enseignants()

    elif page == "Gestion des responsables":
        show_gestion_responsables()

    elif page == "Rapports":
        show_rapport_administration(user)

    elif page == "Notifications":
        show_notificaciones(user)