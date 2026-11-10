import sqlite3
import smtplib
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")

def get_conn():
    return sqlite3.connect("model/elearning.db")

def send_email(to, subject, body_html):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = GMAIL_USER
        msg["To"] = to
        msg.attach(MIMEText(body_html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, to, msg.as_string())
        return True
    except Exception as e:
        print(f"Erreur envoi email a {to}: {e}")
        return False

def get_etudiants_sin_notas_por_profesor():
    conn = get_conn()
    # Etudiants avec note = 0, groupes par enseignant
    df = pd.read_sql("""
        SELECT EN.id_enseignant, EN.nom, EN.prenom, EN.email,
               E.nom as nom_etudiant, E.prenom as prenom_etudiant,
               C.nom_cours
        FROM NOTES N
        JOIN COURS C ON N.id_cours = C.id_cours
        JOIN ENSEIGNANTS EN ON C.id_enseignant = EN.id_enseignant
        JOIN ETUDIANTS E ON N.id_etudiant = E.id_etudiant
        WHERE N.note = 0
        ORDER BY EN.id_enseignant, C.nom_cours, E.nom
    """, conn)
    conn.close()
    return df

def get_peor_profesor():
    conn = get_conn()
    # Cours avec la moyenne la plus basse
    df = pd.read_sql("""
        SELECT EN.nom, EN.prenom, EN.email,
               C.nom_cours,
               ROUND(AVG(N.note), 2) as moyenne
        FROM NOTES N
        JOIN COURS C ON N.id_cours = C.id_cours
        JOIN ENSEIGNANTS EN ON C.id_enseignant = EN.id_enseignant
        GROUP BY C.id_cours
        ORDER BY moyenne ASC
        LIMIT 1
    """, conn)
    conn.close()
    return df

def get_responsables():
    conn = get_conn()
    df = pd.read_sql("SELECT nom, prenom, email FROM RESPONSABLE_PEDAGOGIQUE", conn)
    conn.close()
    return df

def get_administradores():
    conn = get_conn()
    df = pd.read_sql("SELECT nom, prenom, email FROM ADMINISTRATION", conn)
    conn.close()
    return df

def enviar_notificacion_profesores():
    df = get_etudiants_sin_notas_por_profesor()
    if df.empty:
        return 0

    envoyes = 0
    for id_prof, groupe in df.groupby("id_enseignant"):
        email = groupe.iloc[0]["email"]
        nom = groupe.iloc[0]["nom"]
        prenom = groupe.iloc[0]["prenom"]

        lignes = ""
        for _, row in groupe.iterrows():
            lignes += f"""
            <tr>
                <td style='padding:6px;border:1px solid #ddd'>{row['nom_etudiant']} {row['prenom_etudiant']}</td>
                <td style='padding:6px;border:1px solid #ddd'>{row['nom_cours']}</td>
            </tr>"""

        body = f"""
        <html><body style='font-family:Arial,sans-serif;color:#333'>
        <h2 style='color:#1A3A6B'>Alerte - Etudiants avec note 0</h2>
        <p>Bonjour <b>{prenom} {nom}</b>,</p>
        <p>Les etudiants suivants ont une note de <b>0</b> dans vos cours :</p>
        <table style='border-collapse:collapse;width:100%'>
            <thead>
                <tr style='background:#1A3A6B;color:white'>
                    <th style='padding:8px'>Etudiant</th>
                    <th style='padding:8px'>Cours</th>
                </tr>
            </thead>
            <tbody>{lignes}</tbody>
        </table>
        <p style='margin-top:20px;color:#888'>
            Systeme E-Learning Dashboard — {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </p>
        </body></html>
        """
        if send_email(email, "Alerte : Etudiants avec note 0", body):
            envoyes += 1

    return envoyes

def enviar_notificacion_responsables():
    df_cours = get_peor_profesor()
    if df_cours.empty:
        return 0

    row = df_cours.iloc[0]
    df_resp = get_responsables()
    envoyes = 0

    for _, resp in df_resp.iterrows():
        body = f"""
        <html><body style='font-family:Arial,sans-serif;color:#333'>
        <h2 style='color:#1A3A6B'>Rapport - Cours avec la plus faible moyenne</h2>
        <p>Bonjour <b>{resp['prenom']} {resp['nom']}</b>,</p>
        <p>Le cours avec la moyenne la plus basse est :</p>
        <table style='border-collapse:collapse;width:60%'>
            <thead>
                <tr style='background:#1A3A6B;color:white'>
                    <th style='padding:8px'>Enseignant</th>
                    <th style='padding:8px'>Cours</th>
                    <th style='padding:8px'>Moyenne</th>
                </tr>
            </thead>
            <tbody>
                <tr style='background:#FDECEA'>
                    <td style='padding:8px;border:1px solid #ddd'>{row['nom']} {row['prenom']}</td>
                    <td style='padding:8px;border:1px solid #ddd'>{row['nom_cours']}</td>
                    <td style='padding:8px;border:1px solid #ddd;color:#C0392B'><b>{row['moyenne']}/20</b></td>
                </tr>
            </tbody>
        </table>
        <p style='margin-top:20px;color:#888'>
            Systeme E-Learning Dashboard — {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </p>
        </body></html>
        """
        if send_email(resp["email"], "Rapport : Cours avec la plus faible moyenne", body):
            envoyes += 1

    return envoyes

def enviar_notificacion_administradores():
    df_notes = get_etudiants_sin_notas_por_profesor()
    df_cours = get_peor_profesor()
    df_admin = get_administradores()
    envoyes = 0

    # Tableau etudiants avec note 0
    lignes_notes = ""
    if not df_notes.empty:
        for _, row in df_notes.iterrows():
            lignes_notes += f"""
            <tr>
                <td style='padding:6px;border:1px solid #ddd'>{row['nom_etudiant']} {row['prenom_etudiant']}</td>
                <td style='padding:6px;border:1px solid #ddd'>{row['nom_cours']}</td>
                <td style='padding:6px;border:1px solid #ddd'>{row['nom']} {row['prenom']}</td>
            </tr>"""
    else:
        lignes_notes = "<tr><td colspan='3' style='padding:8px;text-align:center'>Aucun etudiant avec note 0</td></tr>"

    # Ligne cours avec la plus faible moyenne
    if not df_cours.empty:
        row_cours = df_cours.iloc[0]
        ligne_cours = f"""
        <tr style='background:#FDECEA'>
            <td style='padding:8px;border:1px solid #ddd'>{row_cours['nom']} {row_cours['prenom']}</td>
            <td style='padding:8px;border:1px solid #ddd'>{row_cours['nom_cours']}</td>
            <td style='padding:8px;border:1px solid #ddd;color:#C0392B'><b>{row_cours['moyenne']}/20</b></td>
        </tr>"""
    else:
        ligne_cours = "<tr><td colspan='3' style='padding:8px;text-align:center'>Aucune donnee disponible</td></tr>"

    for _, admin in df_admin.iterrows():
        body = f"""
        <html><body style='font-family:Arial,sans-serif;color:#333'>
        <h2 style='color:#1A3A6B'>Rapport Administration - Alertes E-Learning</h2>
        <p>Bonjour <b>{admin['prenom']} {admin['nom']}</b>,</p>

        <h3 style='color:#1A3A6B'>1. Etudiants avec note 0</h3>
        <table style='border-collapse:collapse;width:100%'>
            <thead>
                <tr style='background:#1A3A6B;color:white'>
                    <th style='padding:8px'>Etudiant</th>
                    <th style='padding:8px'>Cours</th>
                    <th style='padding:8px'>Enseignant</th>
                </tr>
            </thead>
            <tbody>{lignes_notes}</tbody>
        </table>

        <h3 style='color:#1A3A6B;margin-top:25px'>2. Cours avec la plus faible moyenne</h3>
        <table style='border-collapse:collapse;width:70%'>
            <thead>
                <tr style='background:#1A3A6B;color:white'>
                    <th style='padding:8px'>Enseignant</th>
                    <th style='padding:8px'>Cours</th>
                    <th style='padding:8px'>Moyenne</th>
                </tr>
            </thead>
            <tbody>{ligne_cours}</tbody>
        </table>

        <p style='margin-top:25px;color:#888'>
            Systeme E-Learning Dashboard — {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </p>
        </body></html>
        """
        if send_email(admin["email"], "Rapport Administration : Alertes E-Learning", body):
            envoyes += 1

    return envoyes

def ejecutar_todas_notificaciones():
    print(f"[{datetime.now()}] Lancement de l envoi des notifications...")
    p = enviar_notificacion_profesores()
    r = enviar_notificacion_responsables()
    a = enviar_notificacion_administradores()

    # Mise a jour de la date du dernier envoi
    conn = get_conn()
    conn.execute(
        "UPDATE NOTIFICACIONES_CONFIG SET ultimo_envio = ? WHERE id = 1",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),)
    )
    conn.commit()
    conn.close()

    print(f"Envoyes — Enseignants: {p}, Responsables: {r}, Administrateurs: {a}")
    return p, r, a