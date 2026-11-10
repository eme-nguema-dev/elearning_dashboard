import streamlit as st
import plotly.express as px
import sqlite3
import pandas as pd
import sys
sys.path.append(".")
from controller.etl import *
from view.vues.rapports.rapport_enseignant import show_rapport_enseignant
from view.vues.gestion_etudiants import show_gestion_etudiants

def get_cours_enseignant(id_enseignant):
    conn = sqlite3.connect("model/elearning.db")
    df = pd.read_sql(f"""
        SELECT id_cours, nom_cours, module
        FROM COURS WHERE id_enseignant = {id_enseignant}
    """, conn)
    conn.close()
    return df

def get_etudiants_enseignant(id_enseignant):
    conn = sqlite3.connect("model/elearning.db")
    df = pd.read_sql(f"""
        SELECT DISTINCT E.id_etudiant, E.nom, E.prenom, E.classe,
               ROUND(AVG(N.note), 2) as moyenne,
               CASE WHEN AVG(N.note) >= 10 THEN 'Recu' ELSE 'Echec' END as statut
        FROM ETUDIANTS E
        JOIN NOTES N ON E.id_etudiant = N.id_etudiant
        JOIN COURS C ON N.id_cours = C.id_cours
        WHERE C.id_enseignant = {id_enseignant}
        GROUP BY E.id_etudiant
        ORDER BY moyenne DESC
    """, conn)
    conn.close()
    return df

def get_notes_par_cours_enseignant(id_enseignant):
    conn = sqlite3.connect("model/elearning.db")
    df = pd.read_sql(f"""
        SELECT C.nom_cours, ROUND(AVG(N.note), 2) as moyenne
        FROM NOTES N
        JOIN COURS C ON N.id_cours = C.id_cours
        WHERE C.id_enseignant = {id_enseignant}
        GROUP BY C.nom_cours
    """, conn)
    conn.close()
    return df

def get_notes_detaillees_enseignant(id_enseignant):
    conn = sqlite3.connect("model/elearning.db")
    df = pd.read_sql(f"""
        SELECT E.nom, E.prenom, E.classe, C.nom_cours, N.note
        FROM NOTES N
        JOIN ETUDIANTS E ON N.id_etudiant = E.id_etudiant
        JOIN COURS C ON N.id_cours = C.id_cours
        WHERE C.id_enseignant = {id_enseignant}
        ORDER BY E.nom, C.nom_cours
    """, conn)
    conn.close()
    return df

def show_vue_generale_enseignant(user):
    id_enseignant = user["id"]
    st.header("Vue Generale")

    df_cours = get_cours_enseignant(id_enseignant)
    df_etudiants = get_etudiants_enseignant(id_enseignant)
    df_notes_cours = get_notes_par_cours_enseignant(id_enseignant)

    nb_recus = len(df_etudiants[df_etudiants["statut"] == "Recu"])
    taux = round(nb_recus / len(df_etudiants) * 100, 1) if len(df_etudiants) > 0 else 0
    moyenne = round(df_etudiants["moyenne"].mean(), 2) if not df_etudiants.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Mes cours", len(df_cours))
    col2.metric("Mes etudiants", len(df_etudiants))
    col3.metric("Moyenne globale", f"{moyenne} / 20")
    col4.metric("Taux de reussite", f"{taux} %")

    st.divider()

    st.subheader("Taux de reussite par classe")
    conn = sqlite3.connect("model/elearning.db")
    df_reussite_classe = pd.read_sql(f"""
        SELECT E.classe,
            COUNT(DISTINCT E.id_etudiant) as total_etudiants,
            SUM(CASE WHEN N.note >= 10 THEN 1 ELSE 0 END) as recus,
            SUM(CASE WHEN N.note < 10 THEN 1 ELSE 0 END) as echecs,
            ROUND(SUM(CASE WHEN N.note >= 10 THEN 1 ELSE 0 END) * 100.0 / COUNT(N.note), 1) as taux_reussite
        FROM ETUDIANTS E
        JOIN NOTES N ON E.id_etudiant = N.id_etudiant
        JOIN COURS C ON N.id_cours = C.id_cours
        WHERE C.id_enseignant = {id_enseignant}
        GROUP BY E.classe
        ORDER BY E.classe
    """, conn)
    conn.close()

    if not df_reussite_classe.empty:
        colors = ['#1A3A6B', '#2E7D4F', '#C0392B', '#8E44AD', '#E67E22']
        fig_pie = px.pie(
            df_reussite_classe,
            values='total_etudiants',
            names='classe',
            title="Repartition et taux de reussite par classe",
            color_discrete_sequence=colors[:len(df_reussite_classe)],
            hole=0.35,
            custom_data=['recus', 'echecs', 'taux_reussite']
        )
        fig_pie.update_traces(
            texttemplate='<b>%{label}</b><br>Recus: %{customdata[0]}<br>Echecs: %{customdata[1]}<br>Taux: %{customdata[2]}%',
            textinfo='text',
            hovertemplate='<b>Classe %{label}</b><br>Taux reussite: %{customdata[2]}%<extra></extra>'
        )
        fig_pie.update_layout(showlegend=True, height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Moyenne par cours")
        if not df_notes_cours.empty:
            fig = px.bar(df_notes_cours, x="nom_cours", y="moyenne",
                         labels={"moyenne": "Moyenne", "nom_cours": "Cours"},
                         color="moyenne", color_continuous_scale="blues")
            fig.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Classement de mes etudiants")
        if not df_etudiants.empty:
            fig2 = px.bar(df_etudiants, x="nom", y="moyenne",
                          labels={"moyenne": "Moyenne", "nom": "Etudiant"},
                          color="moyenne", color_continuous_scale="blues")
            fig2.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("Etudiants en difficulte")
    df_diff = df_etudiants[df_etudiants["moyenne"] < 10]
    if df_diff.empty:
        st.success("Aucun etudiant en difficulte")
    else:
        st.dataframe(df_diff, use_container_width=True)

def show_enseignant(user, page):
    id_enseignant = user["id"]

    if page == "Vue generale":
        show_vue_generale_enseignant(user)

    elif page == "Mes cours":
        st.header("Mes cours")
        df = get_notes_par_cours_enseignant(id_enseignant)
        if df.empty:
            st.info("Aucun cours assigne")
        else:
            fig = px.bar(df, x="nom_cours", y="moyenne",
                         labels={"moyenne": "Moyenne", "nom_cours": "Cours"},
                         color="moyenne", color_continuous_scale="blues")
            fig.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df, use_container_width=True)

    elif page == "  └ Classes":
        st.header("Classes")
        conn = sqlite3.connect("model/elearning.db")

        df_classes = pd.read_sql(f"""
            SELECT E.classe,
                   COUNT(DISTINCT E.id_etudiant) as nb_etudiants,
                   ROUND(AVG(N.note), 2) as moyenne_classe,
                   ROUND(SUM(CASE WHEN N.note >= 10 THEN 1 ELSE 0 END) * 100.0 / COUNT(N.note), 2) as taux_reussite
            FROM ETUDIANTS E
            JOIN NOTES N ON E.id_etudiant = N.id_etudiant
            JOIN COURS C ON N.id_cours = C.id_cours
            WHERE C.id_enseignant = {id_enseignant}
            GROUP BY E.classe
            ORDER BY E.classe
        """, conn)

        if df_classes.empty:
            st.info("Aucune classe associee a vos cours")
        else:
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
            st.subheader("Etudiants par classe")
            for classe in df_classes["classe"].tolist():
                st.markdown(f"#### Classe {classe}")
                df_etu = pd.read_sql(f"""
                    SELECT DISTINCT E.nom, E.prenom,
                           ROUND(AVG(N.note), 2) as moyenne,
                           CASE WHEN AVG(N.note) >= 10 THEN 'Recu' ELSE 'Echec' END as statut
                    FROM ETUDIANTS E
                    JOIN NOTES N ON E.id_etudiant = N.id_etudiant
                    JOIN COURS C ON N.id_cours = C.id_cours
                    WHERE C.id_enseignant = {id_enseignant} AND E.classe = '{classe}'
                    GROUP BY E.id_etudiant
                    ORDER BY moyenne DESC
                """, conn)
                st.dataframe(df_etu, use_container_width=True)
                st.divider()

        conn.close()

    elif page == "Mes etudiants":
        st.header("Mes etudiants")
        df = get_etudiants_enseignant(id_enseignant)
        if df.empty:
            st.info("Aucun etudiant associe a vos cours")
        else:
            fig = px.bar(df, x="nom", y="moyenne",
                         labels={"moyenne": "Moyenne", "nom": "Etudiant"},
                         color="moyenne", color_continuous_scale="blues")
            fig.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Etudiants en difficulte")
            df_diff = df[df["moyenne"] < 10]
            if df_diff.empty:
                st.success("Aucun etudiant en difficulte")
            else:
                st.dataframe(df_diff, use_container_width=True)

    elif page == "  └ Notes":
        st.header("Notes detaillees")
        df_detail = get_notes_detaillees_enseignant(id_enseignant)

        if df_detail.empty:
            st.info("Aucune note disponible")
        else:
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
                         title=f"Notes de {etudiant_sel}")
            fig.add_hline(y=10, line_dash="dash", line_color="red",
                          annotation_text="Seuil de reussite")
            fig.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)

    elif page == "Gestion des etudiants":
        show_gestion_etudiants()

    elif page == "Rapports":
        show_rapport_enseignant(user)