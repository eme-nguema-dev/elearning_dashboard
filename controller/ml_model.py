import sqlite3
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings("ignore")

def get_data():
    conn = sqlite3.connect("model/elearning.db")
    df = pd.read_sql("""
        SELECT
            E.id_etudiant,
            E.nom,
            E.prenom,
            E.classe,
            ROUND(AVG(N.note), 2) as moyenne,
            ROUND(SUM(A.temps_passe), 2) as temps_passe,
            COUNT(DISTINCT A.date_connexion) as nb_connexions
        FROM ETUDIANTS E
        JOIN NOTES N ON E.id_etudiant = N.id_etudiant
        JOIN ACTIVITE A ON E.id_etudiant = A.id_etudiant
        GROUP BY E.id_etudiant
    """, conn)
    conn.close()
    return df

def run_kmeans(df):
    features = df[["moyenne", "temps_passe", "nb_connexions"]].copy()
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df["cluster"] = kmeans.fit_predict(features_scaled)

    # Identifier les clusters par moyenne
    cluster_means = df.groupby("cluster")["moyenne"].mean()
    sorted_clusters = cluster_means.sort_values(ascending=False).index.tolist()

    niveau_map = {
        sorted_clusters[0]: "Bon",
        sorted_clusters[1]: "Moyen",
        sorted_clusters[2]: "Risque"
    }
    df["niveau"] = df["cluster"].map(niveau_map)
    return df

def run_random_forest(df):
    df["reussite"] = (df["moyenne"] >= 10).astype(int)
    features = df[["moyenne", "temps_passe", "nb_connexions"]]
    target = df["reussite"]

    if len(df) < 5:
        df["prediction"] = df["reussite"].map({1: "Recu", 0: "Echec"})
        df["probabilite"] = df["moyenne"].apply(lambda x: round(min(x / 20, 1.0), 2))
        return df

    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(features, target)

    df["prediction"] = rf.predict(features)
    df["prediction"] = df["prediction"].map({1: "Recu", 0: "Echec"})
    probas = rf.predict_proba(features)
    df["probabilite"] = [round(p[1], 2) for p in probas]
    return df

def get_resultats_ia():
    df = get_data()
    df = run_kmeans(df)
    df = run_random_forest(df)
    return df

def get_stats_prediction(df):
    total = len(df)
    recus_pred = len(df[df["prediction"] == "Recu"])
    echecs_pred = len(df[df["prediction"] == "Echec"])
    bon = len(df[df["niveau"] == "Bon"])
    moyen = len(df[df["niveau"] == "Moyen"])
    risque = len(df[df["niveau"] == "Risque"])
    return {
        "total": total,
        "recus_pred": recus_pred,
        "echecs_pred": echecs_pred,
        "taux_reussite_pred": round(recus_pred / total * 100, 1),
        "bon": bon,
        "moyen": moyen,
        "risque": risque
    }

print("ML model charge avec succes")
