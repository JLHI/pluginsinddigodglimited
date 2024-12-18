from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from qgis.core import (QgsProject,
                       
                       )
import datetime
import re

################################ Pas de table isochrone crée dans la BDD APPLICATIFS
# def saveInDb(mode) : 
#     try :
#         # Étape 1 : Configuration de la connexion PostgreSQL
#         db = QSqlDatabase.addDatabase("QPSQL")
#         db.setConnectOptions("service=appli")  # Utilise le fichier service appli

#         if not db.open():
#             print("Erreur de connexion à la base de données.")
#         else:
#             print("Connexion réussie.")

#         # Étape 2 : Effectuer une modification SQL
#         query = QSqlQuery(db)
#         titre = getProjectName()
#         now = datetime.datetime.now()
#         date = now.strftime("%d/%m/%Y%H:%M:%S")

#         # Étape 3 : Ajouter une nouvelle ligne dans la table
#         # SQL with placeholders
#         sql_insert = """
#         INSERT INTO multimode.compteur_multimode (projet, type, date) 
#         VALUES (?, ?, ?);
#         """

#         # Prepare the query
#         query.prepare(sql_insert)

#         # Lier les valeurs aux paramètres
#         query.bindValue(0, titre)  # Lier le titre à la première position (%s)
#         query.bindValue(1, mode)   # Lier le mode à la deuxième position (%s)
#         query.bindValue(2, date)   # Lier la date à la troisième position (%s)

#         if query.exec():
#             print("Insertion effectuée avec succès.")
#         else:
#             print(f"Erreur lors de l'insertion : {query.lastError().text()}")

#         # Étape 4 : Fermer la connexion
#         db.close()
#     except Exception as e :
#         print(e)

def getProjectName():
    # Récupère le chemin et le nom du projet
    title = QgsProject.instance().baseName()
    print(title)
    if title is (''):
        # Pour enregistrer le projet sans titre ds une variable
        title = 'Un projet sans nom'
        return title
    else :
        return title
    

def clean_intermediate_values(texte):
    if texte is (''):
        return texte
    else :
        # Remplace les virgules entourées d'espaces ou non, par des virgules simples
        txt_nettoye = re.sub(r'\s*,\s*', ',', texte)
    return txt_nettoye