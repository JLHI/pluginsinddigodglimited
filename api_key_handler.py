from qgis.core import QgsExpressionContextUtils
from PyQt5.QtWidgets import QMessageBox
import requests

class HereAPIHandler:
    def __init__(self):
        self.api_keys = []
        self.current_key_index = 0
        self.variable_name = 'hereapikey'
        self.load_api_keys()

    def load_api_keys(self):
        """
        Récupère les clés API depuis une variable globale QGIS,
        gère plusieurs clés séparées par des virgules.
        """
        Herekey = QgsExpressionContextUtils.globalScope().variable(self.variable_name)
        if Herekey:
            self.api_keys = [key.strip() for key in Herekey.split(',')]
        
        if not self.api_keys:
            QMessageBox.warning(
                None,
                "Clé manquante",
                "Attention : La clé Here n'est pas configurée. Vous devez ajouter une variable globale 'hereapikey' et saisir votre clé API Here, puis recharger le plugin."
            )

    def get_current_key(self):
        """Retourne la clé API actuelle."""
        if not self.api_keys:
            self.load_api_keys()
        return self.api_keys[self.current_key_index]

    def switch_key(self):
        """
        Passe à la clé API suivante en cas d'erreur 429.
        """
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        print(f"Passage à la clé suivante : {self.get_current_key()}")

    def make_request(self, url, params=None):
        """
        Effectue une requête API avec une URL personnalisée et gère l'erreur 429.
        """
        if params is None:
            params = {}
        while True:
            params["apikey"] = self.get_current_key()
            response = requests.get(url, params=params)
            if response.status_code == 429:
                print("Quota dépassé. Changement de clé API.")
                self.switch_key()
            else:
                return response


