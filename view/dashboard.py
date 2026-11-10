import streamlit as st
import plotly.express as px
import sqlite3
import pandas as pd
import sys
sys.path.append(".")
from view.login import show_login, init_session_from_file, clear_session
from controller.etl import *

st.set_page_config(
    page_title="E-Learning Dashboard",
    page_icon="📊",
    layout="wide"
)

def get_reussite_par_classe():
    conn = sqlite3.connect("model/elearning.db")
    df = pd.read_sql("""
        SELECT classe,
               COUNT(*) as total_etudiants,
               SUM(CASE WHEN moyenne >= 10 THEN 1 ELSE 0 END) as recus,
               SUM(CASE WHEN moyenne < 10 THEN 1 ELSE 0 END) as echecs,
               ROUND(SUM(CASE WHEN moyenne >= 10 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as taux_reussite
        FROM (
            SELECT E.id_etudiant, E.classe, AVG(N.note) as moyenne
            FROM ETUDIANTS E
            JOIN NOTES N ON E.id_etudiant = N.id_etudiant
            GROUP BY E.id_etudiant, E.classe
        )
        GROUP BY classe
        ORDER BY classe
    """, conn)
    conn.close()
    return df

def show_vue_generale():
    st.header("Vue Generale")

    col1, col2, col3 = st.columns(3)
    col1.metric("Moyenne globale", f"{get_moyenne_globale()} / 20")
    col2.metric("Taux de reussite", f"{get_taux_reussite()} %")
    col3.metric("Total etudiants", get_total_etudiants())

    st.divider()

    df_classes = get_reussite_par_classe()
    colors = ['#1A3A6B', '#2E7D4F', '#C0392B', '#8E44AD', '#E67E22']

    fig_pie = px.pie(
        df_classes,
        values='total_etudiants',
        names='classe',
        title="Repartition et taux de reussite par classe",
        color_discrete_sequence=colors[:len(df_classes)],
        hole=0.35,
        custom_data=['recus', 'echecs', 'taux_reussite']
    )
    fig_pie.update_traces(
        texttemplate='<b>%{label}</b><br>Recus: %{customdata[0]}<br>Echecs: %{customdata[1]}<br>Taux: %{customdata[2]}%',
        textinfo='text',
        hovertemplate='<b>Classe %{label}</b><br>Recus: %{customdata[0]}<br>Echecs: %{customdata[1]}<br>Taux reussite: %{customdata[2]}%<extra></extra>'
    )
    fig_pie.update_layout(showlegend=True, height=450)
    st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Notes par cours")
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

    st.divider()
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

    st.divider()
    st.header("Etudiants en difficulte")
    st.dataframe(get_etudiants_en_difficulte(), use_container_width=True)

def show_sidebar(user):
    with st.sidebar:
        st.markdown(f"### {user['prenom']} {user['nom']}")
        st.markdown(f"**Role :** {user['role'].capitalize()}")
        st.divider()

        if user["role"] == "enseignant":
            pages = ["Vue generale", "Mes cours", "  └ Classes",
                     "Mes etudiants", "  └ Notes",
                     "Gestion des etudiants",
                     "Import des donnees", "  └ Historique des imports",
                     "Rapports", "  └ Assistant IA"]

        elif user["role"] == "responsable":
            pages = ["Vue generale", "Analyse des notes", "  └ Classes",
                     "Activite etudiants", "  └ Notes",
                     "Gestion des etudiants", "Gestion des enseignants",
                     "Gestion des cours",
                     "Import des donnees", "  └ Historique des imports",
                     "Rapports", "  └ Assistant IA"]

        elif user["role"] == "administration":
            pages = ["Vue generale", "Statistiques globales",
                    "Gestion des etudiants", "Gestion des enseignants",
                    "Gestion des responsables",
                    "Rapports", "  └ Assistant IA", "Notifications"]

        page = st.radio("Navigation", pages, key="nav_radio")
        st.divider()

        if st.button("Se deconnecter"):
            clear_session()
            st.session_state.clear()
            st.rerun()

    return page

def main():
    init_session_from_file()

    st.markdown("""
        <style>
        .stApp {
            background-color: #F0F0F0;
        }
        section[data-testid="stSidebar"] {
            background-color: #E8E8E8;
            background-image: none;
        }
        .main .block-container {
            background-image: url("https://www.transparenttextures.com/patterns/cartographer.png");
            background-color: #F0F0F0;
        }
        </style>
    """, unsafe_allow_html=True)

    if "user" not in st.session_state:
        show_login()
        return

    user = st.session_state["user"]
    forced_page = st.session_state.pop("nav_page", None)
    page = show_sidebar(user)

    if forced_page:
        page = forced_page

    if page == "Vue generale":
        st.session_state.pop("imported_df", None)
        st.session_state.pop("imported_nom", None)
        st.session_state.pop("imported_saved", None)
        st.session_state.pop("current_import_id", None)
        if user["role"] == "enseignant":
            from view.vues.enseignant import show_enseignant
            show_enseignant(user, "Vue generale")
        else:
            show_vue_generale()

    elif page == "  └ Assistant IA":
        from view.vues.assistant_ia import show_assistant_ia
        show_assistant_ia(user)

    elif user["role"] == "enseignant":
        from view.vues.enseignant import show_enseignant
        from view.vues.import_donnees import show_import_donnees
        from view.vues.historique_imports import show_historique_imports

        if page == "Import des donnees":
            if "import_id" in st.session_state:
                st.session_state["current_import_id"] = st.session_state.pop("import_id")
            import_id = st.session_state.get("current_import_id", None)
            show_import_donnees(user, import_id)
        elif page == "  └ Historique des imports":
            st.session_state.pop("imported_df", None)
            st.session_state.pop("current_import_id", None)
            show_historique_imports(user)
        elif page == "Rapports":
            from view.vues.rapports.rapport_enseignant import show_rapport_enseignant
            show_rapport_enseignant(user)
        elif page == "  └ Classes":
            show_enseignant(user, "  └ Classes")
        elif page == "  └ Notes":
            show_enseignant(user, "  └ Notes")
        else:
            st.session_state.pop("imported_df", None)
            st.session_state.pop("current_import_id", None)
            show_enseignant(user, page)

    elif user["role"] == "responsable":
        from view.vues.responsable import show_responsable
        from view.vues.import_donnees import show_import_donnees
        from view.vues.historique_imports import show_historique_imports

        if page == "Import des donnees":
            if "import_id" in st.session_state:
                st.session_state["current_import_id"] = st.session_state.pop("import_id")
            import_id = st.session_state.get("current_import_id", None)
            show_import_donnees(user, import_id)
        elif page == "  └ Historique des imports":
            st.session_state.pop("imported_df", None)
            st.session_state.pop("current_import_id", None)
            show_historique_imports(user)
        elif page == "Rapports":
            from view.vues.rapports.rapport_responsable import show_rapport_responsable
            show_rapport_responsable(user)
        else:
            st.session_state.pop("imported_df", None)
            st.session_state.pop("current_import_id", None)
            show_responsable(user, page)

    elif user["role"] == "administration":
        from view.vues.administration import show_administration

        if page == "Rapports":
            from view.vues.rapports.rapport_administration import show_rapport_administration
            show_rapport_administration(user)
        else:
            show_administration(user, page)

if __name__ == "__main__":
    main()