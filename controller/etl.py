import sqlite3
import pandas as pd

def get_connection():
    return sqlite3.connect("model/elearning.db")

def get_moyenne_globale():
    conn = get_connection()
    df = pd.read_sql("SELECT AVG(note) as moyenne_globale FROM NOTES", conn)
    conn.close()
    return round(df["moyenne_globale"][0], 2)

def get_taux_reussite():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN moyenne >= 10 THEN 1 ELSE 0 END) as recus
        FROM (
            SELECT E.id_etudiant, AVG(N.note) as moyenne
            FROM ETUDIANTS E
            JOIN NOTES N ON E.id_etudiant = N.id_etudiant
            GROUP BY E.id_etudiant
        )
    """, conn)
    conn.close()
    taux = round(df["recus"][0] / df["total"][0] * 100, 2)
    return taux

def get_total_etudiants():
    conn = get_connection()
    df = pd.read_sql("SELECT COUNT(*) as total FROM ETUDIANTS", conn)
    conn.close()
    return int(df["total"][0])

def get_notes_par_cours():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT C.nom_cours, ROUND(AVG(N.note), 2) as moyenne
        FROM NOTES N
        JOIN COURS C ON N.id_cours = C.id_cours
        GROUP BY C.nom_cours
    """, conn)
    conn.close()
    return df

def get_classement_etudiants():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT E.nom, E.prenom, E.classe, ROUND(AVG(N.note), 2) as moyenne
        FROM NOTES N
        JOIN ETUDIANTS E ON N.id_etudiant = E.id_etudiant
        GROUP BY E.id_etudiant
        ORDER BY moyenne DESC
    """, conn)
    conn.close()
    return df

def get_temps_passe():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT E.nom, E.prenom, ROUND(SUM(A.temps_passe), 2) as total_temps
        FROM ACTIVITE A
        JOIN ETUDIANTS E ON A.id_etudiant = E.id_etudiant
        GROUP BY E.id_etudiant
        ORDER BY total_temps DESC
    """, conn)
    conn.close()
    return df

def get_frequence_connexion():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT E.nom, E.prenom, COUNT(A.date_connexion) as nb_connexions
        FROM ACTIVITE A
        JOIN ETUDIANTS E ON A.id_etudiant = E.id_etudiant
        GROUP BY E.id_etudiant
        ORDER BY nb_connexions DESC
    """, conn)
    conn.close()
    return df

def get_etudiants_en_difficulte():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT E.nom, E.prenom, E.classe, ROUND(AVG(N.note), 2) as moyenne
        FROM NOTES N
        JOIN ETUDIANTS E ON N.id_etudiant = E.id_etudiant
        GROUP BY E.id_etudiant
        HAVING moyenne < 10
        ORDER BY moyenne ASC
    """, conn)
    conn.close()
    return df

def get_notes_detaillees():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT E.nom, E.prenom, E.classe, C.nom_cours, N.note
        FROM NOTES N
        JOIN ETUDIANTS E ON N.id_etudiant = E.id_etudiant
        JOIN COURS C ON N.id_cours = C.id_cours
        ORDER BY E.nom, C.nom_cours
    """, conn)
    conn.close()
    return df

print("✅ ETL charge avec succes")
