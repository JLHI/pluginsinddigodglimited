from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from qgis.core import (QgsProject,
                       
                       )
import datetime
import re

############################### Pas de table isochrone crée dans la BDD APPLICATIFS
def saveInDbIso(mode) : 
    try :
        # Étape 1 : Configuration de la connexion PostgreSQL
        db = QSqlDatabase.addDatabase("QPSQL")
        db.setConnectOptions("service=appli")  # Utilise le fichier service appli

        if not db.open():
            print("Erreur de connexion à la base de données.")
        else:
            print("Connexion réussie.")

        # Étape 2 : Effectuer une modification SQL
        query = QSqlQuery(db)
        titre = getProjectName()
        now = datetime.datetime.now()
        date = now.strftime("%d/%m/%Y%H:%M:%S")

        # Étape 3 : Ajouter une nouvelle ligne dans la table
        # SQL with placeholders
        sql_insert = """
        INSERT INTO multimode.compteur_multimode (projet, type, date) 
        VALUES (?, ?, ?);
        """

        # Prepare the query
        query.prepare(sql_insert)

        # Lier les valeurs aux paramètres
        query.bindValue(0, titre)  # Lier le titre à la première position (%s)
        query.bindValue(1, f'iso - {mode}')   # Lier le mode à la deuxième position (%s)
        query.bindValue(2, date)   # Lier la date à la troisième position (%s)

        if query.exec():
            print("Insertion effectuée avec succès.")
        else:
            print(f"Erreur lors de l'insertion : {query.lastError().text()}")

        # Étape 4 : Fermer la connexion
        db.close()
    except Exception as e :
        print(e)

def getProjectName():
    # Récupère le chemin et le nom du projet
    title = QgsProject.instance().baseName()
    print(title)
    if title == "":
        # Pour enregistrer le projet sans titre ds une variable
        title = 'Un projet sans nom'
        return title
    else :
        return title
    

def clean_intermediate_values(texte):
    if texte is None:
        return None
    texte = str(texte)  # Convertit en chaîne de texte si ce n'est pas déjà le cas
    
    if texte.strip() == "":
        return ""  # Retourne une chaîne vide si le texte est vide ou ne contient que des espaces
    
    # Remplace les virgules entourées d'espaces ou non, par des virgules simples
    return re.sub(r'\s*,\s*', ',', texte)

def multiply_by_60(values):
        """
        Multiplie chaque valeur donnée en argument par 60 et retourne une chaîne de texte formatée.
        - Supporte une seule valeur ou plusieurs.
        - Ignore les valeurs non numériques et affiche un message d'erreur.
        """
        if values is None:
            return None
        
        values = str(values)  # Convertit en chaîne de texte si ce n'est pas déjà le cas

        results = []
        items = values.replace(" ", "").split(",")

        for v in items:
            if v == "":
                continue  # Ignore les éléments vides
            try:
                results.append(str(int(float(v)) * 60))
            except ValueError:
                raise ValueError(f"Valeur non numérique : {v}")

        return ", ".join(results)  # Retourne les résultats sous forme de texte