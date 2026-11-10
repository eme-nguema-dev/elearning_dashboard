import streamlit as st
import pandas as pd
import sys
sys.path.append(".")
from controller.etl import *

def show_rapport_responsable(user):
    st.header("📄 Rapport Responsable Pédagogique")
    st.markdown(f"**Généré pour :** {user['prenom']} {user['nom']}")

    st.subheader("1. Indicateurs globaux")
    col1, col2, col3 = st.columns(3)
    col1.metric("Moyenne globale", f"{get_moyenne_globale()} / 20")
    col2.metric("Taux de réussite", f"{get_taux_reussite()} %")
    col3.metric("Total étudiants", get_total_etudiants())

    st.subheader("2. Analyse des notes par cours")
    st.dataframe(get_notes_par_cours(), use_container_width=True)

    st.subheader("3. Classement complet des étudiants")
    st.dataframe(get_classement_etudiants(), use_container_width=True)

    st.subheader("4. Activité des étudiants")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Temps passé (heures)**")
        st.dataframe(get_temps_passe(), use_container_width=True)
    with col2:
        st.markdown("**Fréquence de connexion**")
        st.dataframe(get_frequence_connexion(), use_container_width=True)

    st.subheader("5. Étudiants en difficulté")
    st.dataframe(get_etudiants_en_difficulte(), use_container_width=True)

    st.divider()
    st.subheader("📥 Exporter le rapport")

    csv = pd.concat([
        get_notes_par_cours().assign(section="Notes par cours"),
        get_classement_etudiants().assign(section="Classement"),
        get_temps_passe().assign(section="Temps passé"),
        get_frequence_connexion().assign(section="Fréquence connexion"),
        get_etudiants_en_difficulte().assign(section="En difficulté")
    ]).to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇️ Télécharger en CSV",
        data=csv,
        file_name=f"rapport_responsable_{user['nom']}.csv",
        mime="text/csv"
    )