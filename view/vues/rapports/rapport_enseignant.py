import streamlit as st
import pandas as pd
import sqlite3
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
sys.path.append(".")

def get_conn():
    return sqlite3.connect("model/elearning.db")

def generate_pdf(user, moyenne, taux, total, df_cours, df_etudiants, df_diff):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    elements = []

    # Titre
    title_style = ParagraphStyle('title', fontSize=18, alignment=TA_CENTER,
                                  spaceAfter=10, fontName='Helvetica-Bold')
    subtitle_style = ParagraphStyle('subtitle', fontSize=11, alignment=TA_CENTER,
                                     spaceAfter=20, textColor=colors.grey)
    section_style = ParagraphStyle('section', fontSize=13, fontName='Helvetica-Bold',
                                    spaceAfter=8, spaceBefore=15,
                                    textColor=colors.HexColor('#1A3A6B'))

    elements.append(Paragraph("Rapport Enseignant", title_style))
    elements.append(Paragraph(f"Genere pour : {user['prenom']} {user['nom']}", subtitle_style))
    elements.append(Spacer(1, 0.3*cm))

    # Section 1 - Resume
    elements.append(Paragraph("1. Resume des performances", section_style))
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

    # Section 2 - Notes par cours
    elements.append(Paragraph("2. Notes par cours", section_style))
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

    # Section 3 - Classement
    elements.append(Paragraph("3. Classement des etudiants", section_style))
    data_class = [["Nom", "Prenom", "Classe", "Moyenne", "Statut"]]
    for _, row in df_etudiants.iterrows():
        data_class.append([str(row["nom"]), str(row["prenom"]),
                           str(row["classe"]), str(row["moyenne"]), str(row["statut"])])
    table_class = Table(data_class, colWidths=[3.5*cm, 3.5*cm, 2.5*cm, 3*cm, 3*cm])
    table_class.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A3A6B')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#F0F0F0'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(table_class)
    elements.append(Spacer(1, 0.5*cm))

    # Section 4 - Etudiants en difficulte
    elements.append(Paragraph("4. Etudiants en difficulte", section_style))
    if df_diff.empty:
        elements.append(Paragraph("Aucun etudiant en difficulte", styles["Normal"]))
    else:
        data_diff = [["Nom", "Prenom", "Classe", "Moyenne", "Statut"]]
        for _, row in df_diff.iterrows():
            data_diff.append([str(row["nom"]), str(row["prenom"]),
                              str(row["classe"]), str(row["moyenne"]), str(row["statut"])])
        table_diff = Table(data_diff, colWidths=[3.5*cm, 3.5*cm, 2.5*cm, 3*cm, 3*cm])
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

    doc.build(elements)
    buffer.seek(0)
    return buffer

def show_rapport_enseignant(user):
    id_enseignant = user["id"]
    conn = get_conn()

    # Données filtrées par enseignant
    df_cours = pd.read_sql(f"""
        SELECT C.nom_cours, ROUND(AVG(N.note), 2) as moyenne
        FROM NOTES N
        JOIN COURS C ON N.id_cours = C.id_cours
        WHERE C.id_enseignant = {id_enseignant}
        GROUP BY C.nom_cours
    """, conn)

    df_etudiants = pd.read_sql(f"""
        SELECT DISTINCT E.nom, E.prenom, E.classe,
               ROUND(AVG(N.note), 2) as moyenne,
               CASE WHEN AVG(N.note) >= 10 THEN 'Recu' ELSE 'Echec' END as statut
        FROM ETUDIANTS E
        JOIN NOTES N ON E.id_etudiant = N.id_etudiant
        JOIN COURS C ON N.id_cours = C.id_cours
        WHERE C.id_enseignant = {id_enseignant}
        GROUP BY E.id_etudiant
        ORDER BY moyenne DESC
    """, conn)

    df_diff = df_etudiants[df_etudiants["moyenne"] < 10].copy()

    nb_recus = len(df_etudiants[df_etudiants["statut"] == "Recu"])
    total = len(df_etudiants)
    taux = round(nb_recus / total * 100, 1) if total > 0 else 0
    moyenne = round(df_etudiants["moyenne"].mean(), 2) if not df_etudiants.empty else 0

    conn.close()

    st.header("Rapport Enseignant")
    st.markdown(f"**Genere pour :** {user['prenom']} {user['nom']}")

    st.subheader("1. Resume des performances")
    col1, col2, col3 = st.columns(3)
    col1.metric("Moyenne globale", f"{moyenne} / 20")
    col2.metric("Taux de reussite", f"{taux} %")
    col3.metric("Total etudiants", total)

    st.subheader("2. Notes par cours")
    st.dataframe(df_cours, use_container_width=True)

    st.subheader("3. Classement des etudiants")
    st.dataframe(df_etudiants, use_container_width=True)

    st.subheader("4. Etudiants en difficulte")
    if df_diff.empty:
        st.success("Aucun etudiant en difficulte")
    else:
        st.dataframe(df_diff, use_container_width=True)

    st.divider()
    st.subheader("Exporter le rapport")

    # Export CSV bien structure
    lignes = []

    lignes.append(["RAPPORT ENSEIGNANT"])
    lignes.append([f"Genere pour: {user['prenom']} {user['nom']}"])
    lignes.append([])

    lignes.append(["1. RESUME DES PERFORMANCES"])
    lignes.append(["Moyenne globale", "Taux de reussite", "Total etudiants"])
    lignes.append([f"{moyenne} / 20", f"{taux} %", total])
    lignes.append([])

    lignes.append(["2. NOTES PAR COURS"])
    lignes.append(df_cours.columns.tolist())
    for _, row in df_cours.iterrows():
        lignes.append(row.tolist())
    lignes.append([])

    lignes.append(["3. CLASSEMENT DES ETUDIANTS"])
    lignes.append(df_etudiants.columns.tolist())
    for _, row in df_etudiants.iterrows():
        lignes.append(row.tolist())
    lignes.append([])

    lignes.append(["4. ETUDIANTS EN DIFFICULTE"])
    if not df_diff.empty:
        lignes.append(df_diff.columns.tolist())
        for _, row in df_diff.iterrows():
            lignes.append(row.tolist())
    else:
        lignes.append(["Aucun etudiant en difficulte"])

    df_export = pd.DataFrame(lignes)
    csv = df_export.to_csv(index=False, header=False).encode("utf-8")

    # Export CSV (sin cambios)
    lignes = []
    lignes.append(["RAPPORT ENSEIGNANT"])
    lignes.append([f"Genere pour: {user['prenom']} {user['nom']}"])
    lignes.append([])
    lignes.append(["1. RESUME DES PERFORMANCES"])
    lignes.append(["Moyenne globale", "Taux de reussite", "Total etudiants"])
    lignes.append([f"{moyenne} / 20", f"{taux} %", total])
    lignes.append([])
    lignes.append(["2. NOTES PAR COURS"])
    lignes.append(df_cours.columns.tolist())
    for _, row in df_cours.iterrows():
        lignes.append(row.tolist())
    lignes.append([])
    lignes.append(["3. CLASSEMENT DES ETUDIANTS"])
    lignes.append(df_etudiants.columns.tolist())
    for _, row in df_etudiants.iterrows():
        lignes.append(row.tolist())
    lignes.append([])
    lignes.append(["4. ETUDIANTS EN DIFFICULTE"])
    if not df_diff.empty:
        lignes.append(df_diff.columns.tolist())
        for _, row in df_diff.iterrows():
            lignes.append(row.tolist())
    else:
        lignes.append(["Aucun etudiant en difficulte"])

    df_export = pd.DataFrame(lignes)
    csv = df_export.to_csv(index=False, header=False).encode("utf-8")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Telecharger en CSV",
            data=csv,
            file_name=f"rapport_enseignant_{user['nom']}.csv",
            mime="text/csv"
        )
    with col2:
        pdf_key = f"pdf_rapport_{user['nom']}"

        if st.button("Generer le PDF"):
            pdf_buffer = generate_pdf(
                user, moyenne, taux, total, df_cours, df_etudiants, df_diff
            )
            st.session_state[pdf_key] = pdf_buffer.getvalue()

        if pdf_key in st.session_state:
            st.download_button(
                label="⬇️ Telecharger en PDF",
                data=st.session_state[pdf_key],
                file_name=f"rapport_enseignant_{user['nom']}.pdf",
                mime="application/pdf",
                key=f"dl_{pdf_key}"
            )