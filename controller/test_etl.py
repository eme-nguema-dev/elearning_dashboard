import sys
sys.path.append(".")
from controller.etl import *

print(f"Moyenne globale     : {get_moyenne_globale()}")
print(f"Taux de réussite    : {get_taux_reussite()}%")
print(f"Total étudiants     : {get_total_etudiants()}")
print(f"\nNotes par cours :\n{get_notes_par_cours()}")
print(f"\nClassement étudiants :\n{get_classement_etudiants()}")
print(f"\nTemps passé :\n{get_temps_passe()}")
print(f"\nFréquence connexion :\n{get_frequence_connexion()}")
print(f"\nÉtudiants en difficulté :\n{get_etudiants_en_difficulte()}")