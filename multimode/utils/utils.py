from dateutil.parser import isoparse
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from qgis.core import (QgsProject,
                       
                       )
import datetime
def parse_time(time_str, tz, default="N/A"):
    """Convert a time string to a timezone-aware datetime, or return a default."""
    return isoparse(time_str).astimezone(tz).isoformat() if time_str else default

def extract_correspondence(section, tz):
    """Extract transit section details."""
    return {
        "departure_time": parse_time(section["departure"]["time"], tz),
        "arrival_time": parse_time(section["arrival"]["time"], tz),
        "from_station": section["departure"]["place"].get("name", "Unknown"),
        "to_station": section["arrival"]["place"].get("name", "Unknown"),
        "transport_mode": section["transport"]["mode"],
        "transport_name": section["transport"]["name"],
        "agency": section["agency"].get("name", "Unknown"),
    }


def sanitize_value(value, default=None):
    return value if value is not None else default

def safe_string(value):
    """Retourne une chaîne ou une chaîne vide si la valeur est None ou incompatible."""
    if value is None or value == "":
        return ""
    if isinstance(value, list):
        return "; ".join(map(str, value))  # Concatène les valeurs de la liste avec un séparateur
    return str(value)


def saveInDb(mode) : 
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
        date = datetime.datetime.now()
        # Étape 3 : Ajouter une nouvelle ligne dans la table
        # SQL with placeholders
        sql_insert = """
        INSERT INTO schema.table_name (column1, column2, geometry_column)
        VALUES (:titre, :mode, :date);
        """

        # Prepare the query
        query.prepare(sql_insert)

        # Bind values to placeholders
        query.bindValue(":titre", titre)  # String
        query.bindValue(":mode", mode)    # Integer
        query.bindValue(":date", date)    # String (date)
        if query.exec(sql_insert):
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
    if title is "":
        # Pour enregistrer le projet sans titre ds une variable
        title = 'Un projet sans nom'
        return title
    else :
        return title
    

