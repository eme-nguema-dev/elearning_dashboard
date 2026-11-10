import streamlit as st
import plotly.express as px
import sqlite3
import pandas as pd
import sys
sys.path.append(".")
from controller.etl import *
from view.vues.rapports.rapport_responsable import show_rapport_responsable
from view.vues.gestion_etudiants import show_gestion_etudiants
from view.vues.gestion_enseignants import show_gestion_enseignants
from view.vues.gestion_cours import show_gestion_cours

def show_responsable(user, page):

    if page == "Analyse des notes":
        st.header("Analyse des notes")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Moyenne par cours")
            df_cours = get_notes_par_cours()
            fig = px.bar(df_cours, x="nom_cours", y="moyenne",
                         labels={"moyenne": "Moyenne", "nom_cours": "Cours"},
                         color="moyenne", color_continuous_scale="blues")
            fig.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("Classement des etudiants")
            df_class = get_classement_etudiants()
            fig2 = px.bar(df_class, x="nom", y="moyenne",
                          labels={"moyenne": "Moyenne", "nom": "Etudiant"},
                          color="moyenne", color_continuous_scale="blues")
            fig2.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Etudiants en difficulte")
        st.dataframe(get_etudiants_en_difficulte(), use_container_width=True)

    elif page == "  └ Classes":
        st.header("Classes")
        conn = sqlite3.connect("model/elearning.db")

        df_classes = pd.read_sql("""
            SELECT classe,
                   COUNT(*) as nb_etudiants,
                   ROUND(AVG(moyenne), 2) as moyenne_classe,
                   ROUND(MIN(moyenne), 2) as note_min,
                   ROUND(MAX(moyenne), 2) as note_max,
                   ROUND(SUM(CASE WHEN moyenne >= 10 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as taux_reussite
            FROM (
                SELECT E.id_etudiant, E.classe, AVG(N.note) as moyenne
                FROM ETUDIANTS E
                JOIN NOTES N ON E.id_etudiant = N.id_etudiant
                GROUP BY E.id_etudiant, E.classe
            )
            GROUP BY classe
            ORDER BY classe
        """, conn)

        st.subheader("Statistiques par classe")
        cols_kpi = st.columns(len(df_classes))
        for i, row in df_classes.iterrows():
            with cols_kpi[i]:
                st.metric(f"Classe {row['classe']}", f"{row['moyenne_classe']} / 20",
                          f"Taux reussite: {row['taux_reussite']}%")

        st.divider()
        st.subheader("Detail par classe")
        st.dataframe(df_classes, use_container_width=True)

        st.divider()
        st.subheader("Comparaison des classes")
        fig = px.bar(df_classes, x="classe", y="moyenne_classe",
                     labels={"moyenne_classe": "Moyenne", "classe": "Classe"},
                     color="moyenne_classe", color_continuous_scale="blues")
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("Taux de reussite par classe")
        df_reussite = pd.read_sql("""
            SELECT classe,
                   SUM(CASE WHEN moyenne >= 10 THEN 1 ELSE 0 END) as recus,
                   SUM(CASE WHEN moyenne < 10 THEN 1 ELSE 0 END) as echecs
            FROM (
                SELECT E.id_etudiant, E.classe, AVG(N.note) as moyenne
                FROM ETUDIANTS E
                JOIN NOTES N ON E.id_etudiant = N.id_etudiant
                GROUP BY E.id_etudiant, E.classe
            )
            GROUP BY classe
            ORDER BY classe
        """, conn)

        cols_pie = st.columns(len(df_reussite))
        for i, row in df_reussite.iterrows():
            with cols_pie[i]:
                fig = px.pie(
                    values=[row['recus'], row['echecs']],
                    names=['Recus', 'Echecs'],
                    title=f"Classe {row['classe']}",
                    color_discrete_map={'Recus': '#1D9E75', 'Echecs': '#E24B4A'},
                    hole=0.4
                )
                fig.update_traces(textinfo='percent+label')
                fig.update_layout(showlegend=False, margin=dict(t=40, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("Etudiants par classe")
        classes = df_classes["classe"].tolist()
        for classe in classes:
            st.markdown(f"#### Classe {classe}")
            df_etu_classe = pd.read_sql(f"""
                SELECT E.nom, E.prenom,
                       ROUND(AVG(N.note), 2) as moyenne,
                       CASE WHEN AVG(N.note) >= 10 THEN 'Recu' ELSE 'Echec' END as statut
                FROM ETUDIANTS E
                JOIN NOTES N ON E.id_etudiant = N.id_etudiant
                WHERE E.classe = '{classe}'
                GROUP BY E.id_etudiant
                ORDER BY moyenne DESC
            """, conn)
            st.dataframe(df_etu_classe, use_container_width=True)
            st.divider()

        conn.close()

    elif page == "Activite etudiants":
        st.header("Activite des etudiants")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Temps passe (heures)")
            df_temps = get_temps_passe()
            fig3 = px.bar(df_temps, x="nom", y="total_temps",
                          labels={"total_temps": "Heures", "nom": "Etudiant"},
                          color="total_temps", color_continuous_scale="teal")
            fig3.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig3, use_container_width=True)
        with col2:
            st.subheader("Frequence de connexion")
            df_conn = get_frequence_connexion()
            fig4 = px.bar(df_conn, x="nom", y="nb_connexions",
                          labels={"nb_connexions": "Connexions", "nom": "Etudiant"},
                          color="nb_connexions", color_continuous_scale="teal")
            fig4.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig4, use_container_width=True)

    elif page == "  └ Notes":
        st.header("Notes detaillees des etudiants")

        df_detail = get_notes_detaillees()
        df_pivot = df_detail.pivot_table(
            index=["nom", "prenom", "classe"],
            columns="nom_cours",
            values="note"
        ).reset_index()
        df_pivot.columns.name = None
        df_pivot = df_pivot.rename(columns={"nom": "Nom", "prenom": "Prenom", "classe": "Classe"})

        st.subheader("Tableau des notes")
        st.dataframe(df_pivot.set_index("Nom"), use_container_width=True)

        st.divider()
        st.subheader("Analyse d un etudiant")
        etudiants = df_detail["nom"].unique().tolist()
        etudiant_sel = st.selectbox("Selectionner un etudiant", etudiants)

        df_etu = df_detail[df_detail["nom"] == etudiant_sel]
        fig = px.bar(df_etu, x="nom_cours", y="note",
                     labels={"note": "Note", "nom_cours": "Cours"},
                     color="note", color_continuous_scale="blues",
                     title=f"Notes de {etudiant_sel}")
        fig.add_hline(y=10, line_dash="dash", line_color="red",
                      annotation_text="Seuil de reussite")
        fig.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    elif page == "Gestion des etudiants":
        show_gestion_etudiants()

    elif page == "Gestion des enseignants":
        show_gestion_enseignants()

    elif page == "Gestion des cours":
        show_gestion_cours()

    elif page == "Rapports":
        show_rapport_responsable(user)
