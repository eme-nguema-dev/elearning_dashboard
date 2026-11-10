import sqlite3
conn = sqlite3.connect('model/elearning.db')
cursor = conn.cursor()

# Eliminar profesores basura manteniendo los originales
cursor.execute('UPDATE COURS SET id_enseignant=NULL WHERE id_enseignant > 4')
cursor.execute('DELETE FROM ENSEIGNANTS WHERE id_enseignant > 4')

# Restaurar asignaciones originales
cursor.execute('UPDATE COURS SET id_enseignant=1 WHERE id_cours IN (1, 2)')
cursor.execute('UPDATE COURS SET id_enseignant=2 WHERE id_cours IN (3, 4)')
cursor.execute('UPDATE COURS SET id_enseignant=3 WHERE id_cours=5')
cursor.execute('UPDATE COURS SET id_enseignant=4 WHERE id_cours=6')

conn.commit()

cursor.execute('SELECT E.id_enseignant, E.nom, E.prenom FROM ENSEIGNANTS E ORDER BY id_enseignant')
print("ENSEIGNANTS:")
for r in cursor.fetchall():
    print(r)

cursor.execute('SELECT C.id_cours, C.nom_cours, E.nom, E.prenom FROM COURS C LEFT JOIN ENSEIGNANTS E ON C.id_enseignant=E.id_enseignant ORDER BY id_cours')
print("\nCOURS:")
for r in cursor.fetchall():
    print(r)

conn.close()