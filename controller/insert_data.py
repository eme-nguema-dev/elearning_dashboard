import sqlite3
import pandas as pd

# Connexion à la base de données
conn = sqlite3.connect("elearning.db")
cursor = conn.cursor()

# ── ENSEIGNANTS ──────────────────────────────────────────
cursor.executemany("INSERT INTO ENSEIGNANTS (nom, prenom, email, mot_de_passe) VALUES (?,?,?,?)", [
    ("Dupont",   "Jean",    "j.dupont@elearning.com",   "prof123"),
    ("Martin",   "Sophie",  "s.martin@elearning.com",   "prof123"),
    ("Leclerc",  "Paul",    "p.leclerc@elearning.com",  "prof123"),
    ("Bernard",  "Claire",  "c.bernard@elearning.com",  "prof123"),
])

# ── ADMINISTRATION ───────────────────────────────────────
cursor.executemany("INSERT INTO ADMINISTRATION (nom, prenom, email, mot_de_passe, role) VALUES (?,?,?,?,?)", [
    ("Moreau",  "Luc",     "l.moreau@elearning.com",  "admin123", "Directeur"),
    ("Petit",   "Anne",    "a.petit@elearning.com",   "admin123", "Secrétaire"),
])

# ── RESPONSABLE_PEDAGOGIQUE ──────────────────────────────
cursor.executemany("INSERT INTO RESPONSABLE_PEDAGOGIQUE (nom, prenom, email, mot_de_passe, departement) VALUES (?,?,?,?,?)", [
    ("Simon",  "Marc",   "m.simon@elearning.com",  "resp123", "Informatique"),
    ("Leroy",  "Julie",  "j.leroy@elearning.com",  "resp123", "Mathématiques"),
])

# ── ETUDIANTS ────────────────────────────────────────────
cursor.executemany("INSERT INTO ETUDIANTS (nom, prenom, classe) VALUES (?,?,?)", [
    ("Benali",    "Amine",    "L1"), ("Khalil",   "Sara",    "L1"),
    ("Triki",     "Mohamed",  "L2"), ("Mansour",  "Lina",    "M1"),
    ("Haddad",    "Youssef",  "L1"), ("Jabri",    "Rim",     "L2"),
    ("Zouari",    "Karim",    "M1"), ("Dridi",    "Fatma",   "L1"),
    ("Ben Salem", "Tarek",    "L2"), ("Chaari",   "Asma",    "M1"),
    ("Touati",    "Bilel",    "L1"), ("Hamdi",    "Nour",    "L2"),
    ("Boughanmi", "Sami",     "M1"), ("Baraket",  "Ines",    "L1"),
    ("Gharbi",    "Rami",     "L2"), ("Sassi",    "Leila",   "M1"),
    ("Mrad",      "Oussama",  "L1"), ("Ayari",    "Donia",   "L2"),
    ("Chebbi",    "Fares",    "M1"), ("Jebali",   "Mariem",  "L1"),
])

# ── COURS ────────────────────────────────────────────────
cursor.executemany("INSERT INTO COURS (nom_cours, module, id_enseignant) VALUES (?,?,?)", [
    ("Algorithmique avancée",   "Algorithmique",  1),
    ("Structures de données",   "Algorithmique",  1),
    ("Base de données SQL",     "BDD",            2),
    ("Modélisation UML",        "BDD",            2),
    ("Machine Learning",        "IA",             3),
    ("Développement Web",       "Web",            4),
])

# ── NOTES ────────────────────────────────────────────────
import random
random.seed(42)
notes = []
for id_etudiant in range(1, 21):
    for id_cours in range(1, 7):
        note = round(random.uniform(4, 20), 2)
        notes.append((id_etudiant, id_cours, note))
cursor.executemany("INSERT INTO NOTES (id_etudiant, id_cours, note) VALUES (?,?,?)", notes)

# ── ACTIVITE ─────────────────────────────────────────────
from datetime import datetime, timedelta
activites = []
for id_etudiant in range(1, 21):
    for i in range(6):
        temps = round(random.uniform(1, 10), 2)
        date = (datetime(2024, 10, 1) + timedelta(days=i*15)).strftime("%Y-%m-%d")
        activites.append((id_etudiant, temps, date))
cursor.executemany("INSERT INTO ACTIVITE (id_etudiant, temps_passe, date_connexion) VALUES (?,?,?)", activites)

conn.commit()
conn.close()
print("✅ Données insérées avec succès")