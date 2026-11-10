import streamlit as st
import pandas as pd
import sqlite3
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER
import io
sys.path.append(".")
from controller.etl import *

def get_conn():
    return sqlite3.connect("model/elearning.db")

def generate_pdf(user, moyenne, taux, total, df_classe, df_cours, df_diff, df_temps, df_conn):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    elements = []

    title_style = ParagraphStyle('title', fontSize=18, alignment=TA_CENTER,
                                  spaceAfter=10, fontName='Helvetica-Bold')
    subtitle_style = ParagraphStyle('subtitle', fontSize=11, alignment=TA_CENTER,
                                     spaceAfter=20, textColor=colors.grey)
    section_style = ParagraphStyle('section', fontSize=13, fontName='Helvetica-Bold',
                                    spaceAfter=8, spaceBefore=15,
                                    textColor=colors.HexColor('#1A3A6B'))
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Rapport Administration", title_style))
    elements.append(Paragraph(f"Genere pour : {user['prenom']} {user['nom']}", subtitle_style))
    elements.append(Spacer(1, 0.3*cm))

    # Section 1 - Statistiques
    elements.append(Paragraph("1. Statistiques institutionnelles", section_style))
    data_resume = [
        ["Moyenne globale", "Taux de reussite", "Total etudiants"],
        [f"{moyenne} / 20", f"{taux} %", str(total)]
    ]
    table_resume = Table(data_resume, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    table_resume.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A3A6B')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 11),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#F0F0F0'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(table_resume)
    elements.append(Spacer(1, 0.5*cm))

    # Section 2 - Répartition par classe
    elements.append(Paragraph("2. Repartition des etudiants par classe", section_style))
    data_classe = [["Classe", "Total etudiants"]]
    for _, row in df_classe.iterrows():
        data_classe.append([str(row["classe"]), str(row["total_etudiants"])])
    table_classe = Table(data_classe, colWidths=[8*cm, 8.5*cm])
    table_classe.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A3A6B')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#F0F0F0'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 7),
    ]))
    elements.append(table_classe)
    elements.append(Spacer(1, 0.5*cm))

    # Section 3 - Performance par cours
    elements.append(Paragraph("3. Performance par cours", section_style))
    data_cours = [["Cours", "Moyenne"]]
    for _, row in df_cours.iterrows():
        data_cours.append([str(row["nom_cours"]), str(row["moyenne"])])
    table_cours = Table(data_cours, colWidths=[12*cm, 4.5*cm])
    table_cours.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A3A6B')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#F0F0F0'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 7),
    ]))
    elements.append(table_cours)
    elements.append(Spacer(1, 0.5*cm))

    # Section 4 - Etudiants en difficulté
    elements.append(Paragraph("4. Etudiants en difficulte", section_style))
    if df_diff.empty:
        elements.append(Paragraph("Aucun etudiant en difficulte", styles["Normal"]))
    else:
        data_diff = [["Nom", "Prenom", "Classe", "Moyenne"]]
        for _, row in df_diff.iterrows():
            data_diff.append([str(row["nom"]), str(row["prenom"]),
                               str(row["classe"]), str(row["moyenne"])])
        table_diff = Table(data_diff, colWidths=[4*cm, 4*cm, 3*cm, 5.5*cm])
        table_diff.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#C0392B')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#FDECEA'), colors.white]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(table_diff)
    elements.append(Spacer(1, 0.5*cm))

    # Section 5 - Temps passé
    elements.append(Paragraph("5. Activite globale - Temps passe (heures)", section_style))
    data_temps = [["Nom", "Prenom", "Total heures"]]
    for _, row in df_temps.iterrows():
        data_temps.append([str(row["nom"]), str(row["prenom"]), str(row["total_temps"])])
    table_temps = Table(data_temps, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    table_temps.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A3A6B')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#F0F0F0'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(table_temps)
    elements.append(Spacer(1, 0.5*cm))

    # Section 6 - Fréquence connexion
    elements.append(Paragraph("6. Activite globale - Frequence de connexion", section_style))
    data_conn = [["Nom", "Prenom", "Nb connexions"]]
    for _, row in df_conn.iterrows():
        data_conn.append([str(row["nom"]), str(row["prenom"]), str(row["nb_connexions"])])
    table_conn = Table(data_conn, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    table_conn.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A3A6B')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#F0F0F0'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(table_conn)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def show_rapport_administration(user):
    st.header("Rapport Administration")
    st.markdown(f"**Genere pour :** {user['prenom']} {user['nom']}")

    conn = get_conn()
    df_classe = pd.read_sql("""
        SELECT classe, COUNT(*) as total_etudiants
        FROM ETUDIANTS
        GROUP BY classe
    """, conn)
    conn.close()

    moyenne = get_moyenne_globale()
    taux = get_taux_reussite()
    total = get_total_etudiants()
    df_cours = get_notes_par_cours()
    df_diff = get_etudiants_en_difficulte()
    df_temps = get_temps_passe()
    df_conn_freq = get_frequence_connexion()

    st.subheader("1. Statistiques institutionnelles")
    col1, col2, col3 = st.columns(3)
    col1.metric("Moyenne globale", f"{moyenne} / 20")
    col2.metric("Taux de reussite", f"{taux} %")
    col3.metric("Total etudiants", total)

    st.subheader("2. Repartition des etudiants par classe")
    st.dataframe(df_classe, use_container_width=True)

    st.subheader("3. Performance par cours")
    st.dataframe(df_cours, use_container_width=True)

    st.subheader("4. Etudiants en difficulte")
    st.metric("Nombre d etudiants en difficulte", len(df_diff))
    st.dataframe(df_diff, use_container_width=True)

    st.subheader("5. Activite globale")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Temps passe (heures)**")
        st.dataframe(df_temps, use_container_width=True)
    with col2:
        st.markdown("**Frequence de connexion**")
        st.dataframe(df_conn_freq, use_container_width=True)

    st.divider()
    st.subheader("Exporter le rapport")

    # ── CSV estructurado ──
    lignes = []
    lignes.append(["RAPPORT ADMINISTRATION"])
    lignes.append([f"Genere pour: {user['prenom']} {user['nom']}"])
    lignes.append([])

    lignes.append(["1. STATISTIQUES INSTITUTIONNELLES"])
    lignes.append(["Moyenne globale", "Taux de reussite", "Total etudiants"])
    lignes.append([f"{moyenne} / 20", f"{taux} %", total])
    lignes.append([])

    lignes.append(["2. REPARTITION DES ETUDIANTS PAR CLASSE"])
    lignes.append(df_classe.columns.tolist())
    for _, row in df_classe.iterrows():
        lignes.append(row.tolist())
    lignes.append([])

    lignes.append(["3. PERFORMANCE PAR COURS"])
    lignes.append(df_cours.columns.tolist())
    for _, row in df_cours.iterrows():
        lignes.append(row.tolist())
    lignes.append([])

    lignes.append(["4. ETUDIANTS EN DIFFICULTE"])
    if not df_diff.empty:
        lignes.append(df_diff.columns.tolist())
        for _, row in df_diff.iterrows():
            lignes.append(row.tolist())
    else:
        lignes.append(["Aucun etudiant en difficulte"])
    lignes.append([])

    lignes.append(["5. ACTIVITE GLOBALE - TEMPS PASSE"])
    lignes.append(df_temps.columns.tolist())
    for _, row in df_temps.iterrows():
        lignes.append(row.tolist())
    lignes.append([])

    lignes.append(["6. ACTIVITE GLOBALE - FREQUENCE CONNEXION"])
    lignes.append(df_conn_freq.columns.tolist())
    for _, row in df_conn_freq.iterrows():
        lignes.append(row.tolist())

    df_export = pd.DataFrame(lignes)
    csv = df_export.to_csv(index=False, header=False).encode("utf-8")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Telecharger en CSV",
            data=csv,
            file_name=f"rapport_administration_{user['nom']}.csv",
            mime="text/csv"
        )
    with col2:
        pdf_key = f"pdf_rapport_admin_{user['nom']}"
        if st.button("Generer le PDF"):
            pdf_buffer = generate_pdf(
                user, moyenne, taux, total,
                df_classe, df_cours, df_diff, df_temps, df_conn_freq
            )
            st.session_state[pdf_key] = pdf_buffer.getvalue()

        if pdf_key in st.session_state:
            st.download_button(
                label="Telecharger en PDF",
                data=st.session_state[pdf_key],
                file_name=f"rapport_administration_{user['nom']}.pdf",
                mime="application/pdf",
                key=f"dl_{pdf_key}"
            )