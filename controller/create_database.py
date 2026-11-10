import sqlite3
import pandas as pd
import os

# Connexion à la base de données
conn = sqlite3.connect("model/elearning.db")
cursor = conn.cursor()

# Table ENSEIGNANTS
cursor.execute("""
CREATE TABLE IF NOT EXISTS ENSEIGNANTS (
    id_enseignant INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    mot_de_passe TEXT NOT NULL
)
""")

# Table ADMINISTRATION
cursor.execute("""
CREATE TABLE IF NOT EXISTS ADMINISTRATION (
    id_admin INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    mot_de_passe TEXT NOT NULL,
    role TEXT NOT NULL
)
""")

# Table RESPONSABLE_PEDAGOGIQUE
cursor.execute("""
CREATE TABLE IF NOT EXISTS RESPONSABLE_PEDAGOGIQUE (
    id_responsable INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    mot_de_passe TEXT NOT NULL,
    departement TEXT NOT NULL
)
""")

# Table ETUDIANTS
cursor.execute("""
CREATE TABLE IF NOT EXISTS ETUDIANTS (
    id_etudiant INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    classe TEXT NOT NULL
)
""")

# Table COURS
cursor.execute("""
CREATE TABLE IF NOT EXISTS COURS (
    id_cours INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_cours TEXT NOT NULL,
    module TEXT NOT NULL,
    id_enseignant INTEGER,
    FOREIGN KEY (id_enseignant) REFERENCES ENSEIGNANTS(id_enseignant)
)
""")

# Table NOTES
cursor.execute("""
CREATE TABLE IF NOT EXISTS NOTES (
    id_note INTEGER PRIMARY KEY AUTOINCREMENT,
    id_etudiant INTEGER,
    id_cours INTEGER,
    note REAL,
    FOREIGN KEY (id_etudiant) REFERENCES ETUDIANTS(id_etudiant),
    FOREIGN KEY (id_cours) REFERENCES COURS(id_cours)
)
""")

# Table ACTIVITE
cursor.execute("""
CREATE TABLE IF NOT EXISTS ACTIVITE (
    id_activite INTEGER PRIMARY KEY AUTOINCREMENT,
    id_etudiant INTEGER,
    temps_passe REAL,
    date_connexion TEXT,
    FOREIGN KEY (id_etudiant) REFERENCES ETUDIANTS(id_etudiant)
)
""")

# Table IMPORTS
cursor.execute("""
CREATE TABLE IF NOT EXISTS IMPORTS (
    id_import INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_import TEXT NOT NULL,
    type_fichier TEXT NOT NULL,
    date_import TEXT NOT NULL,
    id_utilisateur INTEGER NOT NULL,
    role_utilisateur TEXT NOT NULL,
    donnees TEXT NOT NULL
)
""")

# Table RAPPORTS_IMPORTS
cursor.execute("""
CREATE TABLE IF NOT EXISTS RAPPORTS_IMPORTS (
    id_rapport INTEGER PRIMARY KEY AUTOINCREMENT,
    id_import INTEGER NOT NULL,
    contenu_rapport TEXT NOT NULL,
    date_rapport TEXT NOT NULL,
    FOREIGN KEY (id_import) REFERENCES IMPORTS(id_import)
)
""")

conn.commit()
conn.close()
print("✅ Tables créées avec succès")