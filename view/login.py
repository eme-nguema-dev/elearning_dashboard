import streamlit as st
import sqlite3
import json
import os
import sys
sys.path.append(".")

SESSION_FILE = "model/session.json"

def verify_login(email, password):
    conn = sqlite3.connect("model/elearning.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id_enseignant, nom, prenom FROM ENSEIGNANTS WHERE email=? AND mot_de_passe=?", (email, password))
    user = cursor.fetchone()
    if user:
        conn.close()
        return {"id": user[0], "nom": user[1], "prenom": user[2], "role": "enseignant"}

    cursor.execute("SELECT id_admin, nom, prenom FROM ADMINISTRATION WHERE email=? AND mot_de_passe=?", (email, password))
    user = cursor.fetchone()
    if user:
        conn.close()
        return {"id": user[0], "nom": user[1], "prenom": user[2], "role": "administration"}

    cursor.execute("SELECT id_responsable, nom, prenom FROM RESPONSABLE_PEDAGOGIQUE WHERE email=? AND mot_de_passe=?", (email, password))
    user = cursor.fetchone()
    if user:
        conn.close()
        return {"id": user[0], "nom": user[1], "prenom": user[2], "role": "responsable"}

    conn.close()
    return None

def save_session(user):
    with open(SESSION_FILE, "w") as f:
        json.dump(user, f)

def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    return None

def clear_session():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

def init_session_from_file():
    if "user" not in st.session_state:
        user = load_session()
        if user:
            st.session_state["user"] = user

def show_login():
    st.title("🎓 E-Learning Dashboard")
    st.subheader("Connexion")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("Se connecter")

    if submit:
        user = verify_login(email, password)
        if user:
            st.session_state["user"] = user
            save_session(user)
            st.rerun()
        else:
            st.error("❌ Email ou mot de passe incorrect")