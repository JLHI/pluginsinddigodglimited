from qgis.PyQt.QtCore import QCoreApplication,QVariant
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsFeature,
    QgsProcessing,QgsWkbTypes,
    QgsFeatureSink,QgsGeometry,QgsFields,QgsField,
    QgsMessageLog,QgsPointXY,QgsProcessingException,QgsExpressionContextUtils
)
from PyQt5.Qt import QMessageBox
from ..api_key_handler import HereAPIHandler
api_handler = HereAPIHandler()

import requests,platform, subprocess,sys
try:
    import flexpolyline
    print('import completed')
except ModuleNotFoundError:
    print('installing flexpolyline')
    if platform.system() == 'Windows':
        # subprocess.call(['pip3', 'install', 'flexpolyline', '--user'])
        subprocess.check_call(['python', "-m", 'pip', 'install', 'flexpolyline'])
    else:
        subprocess.call(['python3', '-m', 'pip', 'install', 'flexpolyline' , "--user"])
    try:
        import flexpolyline
        print('installation completed')
    except ModuleNotFoundError:
        QMessageBox.information(None, 'ERROR', "Oops ! L'installation du module flexpolyline à échouée. Désolé de ne pas pouvoir aller plus loin...")


class WaypointSequences(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    ID_FIELD = 'ID_FIELD'
    WAYPOINTS_OUTPUT = 'WAYPOINTS_OUTPUT'
    ROUTE_OUTPUT = 'ROUTE_OUTPUT'
    GROUP_FIELD = 'GROUP_FIELD'
    SEQUENCE_FIELD = 'SEQUENCE_FIELD'
    CHECKBOXES_MODES = 'CHECKBOXES_MODES'
    
  
    
  
    
    def initAlgorithm(self, config=None):

        # HERE API URLs
        self.sequence_url = "https://wps.hereapi.com/v8/findsequence2"
        self.routing_url = "https://router.hereapi.com/v8/routes"

        # Paramètre pour la couche en entrée
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Couche d\'entrée'),
                [QgsProcessing.TypeVectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.ID_FIELD,
                self.tr("Champ contenant un identifiant unique"),
                parentLayerParameterName=self.INPUT,
                optional=False
            )
        )

        # Paramètre pour le champ de regroupement
        self.addParameter(
            QgsProcessingParameterField(
                self.GROUP_FIELD,
                self.tr('Un champ pour regrouper les points par tournée'),
                parentLayerParameterName=self.INPUT,
            )
        )

        # Paramètre pour le champ de séquence
        self.addParameter(
            QgsProcessingParameterField(
                self.SEQUENCE_FIELD,
                self.tr('Le champ contenant la séquence (1 pour le départ, 2 pour le dernier point. Le point 2 est optionnel)'),
                parentLayerParameterName=self.INPUT,
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.CHECKBOXES_MODES,
                self.tr("Selectionnez les modes que vous voulez requêter"),
                options=["Piéton", "Voiture", "camion"],
                defaultValue=0 # Option 1 et 2 cochées par défaut
            )
        )

        # Paramètre pour la sortie des waypoints
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.WAYPOINTS_OUTPUT,
                self.tr('Waypoints Output')
            )
        )

        # Paramètre pour la sortie des itinéraires
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.ROUTE_OUTPUT,
                self.tr('Route Output')
            )
        )


    def processAlgorithm(self, parameters, context, feedback):
        # Récupérer les paramètres
        layer = self.parameterAsSource(parameters, self.INPUT, context)
        group_field = self.parameterAsString(parameters, self.GROUP_FIELD, context)
        sequence_field = self.parameterAsString(parameters, self.SEQUENCE_FIELD, context)
        id_field = self.parameterAsString(parameters, self.ID_FIELD, context)
        #Get mode
        real_values = ["pedestrian", "car", "truck"]
        selected_index = parameters[self.CHECKBOXES_MODES]
        selected_mode = real_values[selected_index]


        # Initialiser les champs pour les couches de sortie
        waypoint_fields = QgsFields()
        waypoint_fields.append(QgsField("fid", QVariant.Int))
        waypoint_fields.append(QgsField("waypointID", QVariant.String))
        waypoint_fields.append(QgsField("sequence", QVariant.Int))
        waypoint_fields.append(QgsField("latitude", QVariant.Double))
        waypoint_fields.append(QgsField("longitude", QVariant.Double))

        route_fields = QgsFields()
        route_fields.append(QgsField("routeID", QVariant.Int))
        route_fields.append(QgsField("start_lat", QVariant.Double))
        route_fields.append(QgsField("start_lng", QVariant.Double))
        route_fields.append(QgsField("end_lat", QVariant.Double))
        route_fields.append(QgsField("end_lng", QVariant.Double))
        route_fields.append(QgsField("length", QVariant.Double))
        route_fields.append(QgsField("duration", QVariant.Double))
        route_fields.append(QgsField("start_id", QVariant.String))  # ID du point de départ
        route_fields.append(QgsField("end_id", QVariant.String))    # ID du point d'arrivée
        route_fields.append(QgsField("sequence", QVariant.Int))     # Séquence de l'itinéraire

        # Créer les couches de sortie
        (waypoints_sink, waypoints_sink_id) = self.parameterAsSink(
            parameters, self.WAYPOINTS_OUTPUT, context,
            waypoint_fields, QgsWkbTypes.Point, layer.sourceCrs()
        )

        (route_sink, route_sink_id) = self.parameterAsSink(
            parameters, self.ROUTE_OUTPUT, context,
            route_fields, QgsWkbTypes.LineString, layer.sourceCrs()
        )

        # Grouper les points par champ de regroupement
        grouped_features = {}
        for feature in layer.getFeatures():
            group = feature[group_field]
            grouped_features.setdefault(group, []).append(feature)

        fid_counter = 0

        # Traiter chaque groupe
        for group, features in grouped_features.items():
            start_coords = None
            end_coords = None
            destinations = []

            for feature in features:
                sequence = feature[sequence_field]
                geom = feature.geometry()
                feature_id = feature[id_field]  # Obtenir l'identifiant unique de l'utilisateur

                if geom and QgsWkbTypes.geometryType(geom.wkbType()) == QgsWkbTypes.PointGeometry:
                    point = geom.asPoint()
                    lat, lng = point.y(), point.x()

                    # Identifier le point de départ (1) et le point de fin (2)
                    if sequence == 1:
                        start_coords = f"{lat},{lng}"
                    elif sequence == 2:
                        end_coords = f"{lat},{lng}"
                    else:
                        destinations.append(f"{feature_id};{lat},{lng}")

            # Utiliser le dernier point comme fin si "2" n'est pas fourni
            if not end_coords and destinations:
                end_coords = destinations.pop().split(";")[1]

            if not start_coords or not end_coords:
                raise QgsProcessingException(f"Tournée {group} ne contient pas de point de départ ou de fin valide.")

            feedback.pushInfo(f"Tournée {group}: Start {start_coords}, End {end_coords}, Destinations: {len(destinations)}")

            # Appel API pour séquencer les waypoints
            sequence_data = self.get_sequence_data(start_coords, destinations,selected_mode, feedback)
            waypoints = sequence_data.get('results', [])[0].get('waypoints', [])
            waypoints_sorted = sorted(waypoints, key=lambda x: x['sequence'])

            # Écrire les waypoints dans la couche
            for waypoint in waypoints_sorted:
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(waypoint['lng'], waypoint['lat'])))
                feature.setAttributes([
                    fid_counter,
                    waypoint['id'],
                    waypoint['sequence'],
                    waypoint['lat'],
                    waypoint['lng']
                ])
                waypoints_sink.addFeature(feature, QgsFeatureSink.FastInsert)
                fid_counter += 1

            # Construire les itinéraires pour ce groupe
            for i in range(len(waypoints_sorted) - 1):
                start_point = waypoints_sorted[i]
                end_point = waypoints_sorted[i + 1]

                route_response = self.call_here_routing_api(start_point, end_point,selected_mode,feedback)
                route_sections = route_response.get('routes', [])[0].get('sections', [])
                for section in route_sections:
                    summary = section.get('summary', {})
                    geometry = section.get('polyline')

                    # Décoder et créer une géométrie de type ligne
                    line_geometry = self.decode_and_create_line_geometry(geometry)

                    # Créer une entité pour chaque segment de route
                    feature = QgsFeature()
                    feature.setGeometry(line_geometry)
                    feature.setAttributes([
                        i,  # Numéro du segment (séquence)
                        start_point['lat'],  # Latitude du point de départ
                        start_point['lng'],  # Longitude du point de départ
                        end_point['lat'],    # Latitude du point d'arrivée
                        end_point['lng'],    # Longitude du point d'arrivée
                        summary.get('length', 0),  # Longueur de l'itinéraire
                        summary.get('duration', 0),  # Durée de l'itinéraire
                        start_point['id'],   # ID unique du point de départ
                        end_point['id'],     # ID unique du point d'arrivée
                        i + 1                # Séquence de l'itinéraire (1-based index)
                    ])
                    route_sink.addFeature(feature, QgsFeatureSink.FastInsert)

        feedback.pushInfo("Processing completed successfully.")
        return {
            self.WAYPOINTS_OUTPUT: waypoints_sink_id,
            self.ROUTE_OUTPUT: route_sink_id
        }

    # def get_sequence_data(self, start_coords, destinations, feedback):
    #     params = {
    #         "apikey": self.here_api_key,
    #         "mode": "fastest;pedestrian;traffic:disabled;",
    #         "start": start_coords,
    #     }
    #     for i, dest in enumerate(destinations):
    #         params[f"destination{i+1}"] = dest
    #     feedback.pushInfo(f"Url : {self.sequence_url, params}")
    #     response = requests.get(self.sequence_url, params=params)
    #     feedback.pushInfo(f"Réponse de l'url : {response.text}")

    #     if response.status_code != 200:
    #         raise QgsProcessingException(
    #             f"Failed to get sequence data: {response.status_code}"
    #         )
    #     return response.json()
    
    # def call_here_routing_api(self, start_point, end_point,feedback):
    #     params = {
    #         "apikey": self.here_api_key,
    #         "transportMode": "pedestrian",
    #         "origin": f"{start_point['lat']},{start_point['lng']}",
    #         "destination": f"{end_point['lat']},{end_point['lng']}",
    #         "return": "summary,polyline"
    #     }
    #     feedback.pushInfo(f"Url : {self.routing_url, params}")

    #     response = requests.get(self.routing_url, params=params)
    #     feedback.pushInfo(f"Réponse de l'url route : {response.text}")

    #     if response.status_code != 200:
    #         raise QgsProcessingException(
    #             f"Failed to get route data: {response.status_code}"
    #         )
    #     return response.json()
    def get_sequence_data(self, start_coords, destinations,mode, feedback):
        """
        Effectue une requête pour obtenir des données de séquence.
        """
        params = {
            "mode": f"fastest;{mode};traffic:disabled;",
            "start": start_coords
        }
        for i, dest in enumerate(destinations):
            params[f"destination{i+1}"] = dest

        feedback.pushInfo(f"Url : {self.sequence_url, params}")
        response = api_handler.make_request(self.sequence_url, params)
        feedback.pushInfo(f"Réponse de l'url : {response.text}")

        if response.status_code != 200:
            raise QgsProcessingException(
                f"Failed to get sequence data: {response.status_code}"
            )
        return response.json()

    def call_here_routing_api(self, start_point, end_point,mode, feedback):
        """
        Effectue une requête pour l'API de routage HERE.
        """
        params = {
            "transportMode": f"{mode}",
            "origin": f"{start_point['lat']},{start_point['lng']}",
            "destination": f"{end_point['lat']},{end_point['lng']}",
            "return": "summary,polyline"
        }
        feedback.pushInfo(f"Url : {self.routing_url, params}")

        response = api_handler.make_request(self.routing_url, params)
        feedback.pushInfo(f"Réponse de l'url route : {response.text}")

        if response.status_code != 200:
            raise QgsProcessingException(
                f"Failed to get route data: {response.status_code}"
            )
        return response.json()

    def decode_and_create_line_geometry(self, encoded_polyline):
        """
        Décoder une polyligne encodée et créer une géométrie de type ligne.
        
        Args:
            encoded_polyline (str): La polyligne encodée au format HERE.

        Returns:
            QgsGeometry: Géométrie de type ligne créée à partir de la polyligne.
        """
        try:
            # Décoder la polyligne avec flexpolyline
            data_decode = flexpolyline.decode(encoded_polyline)
            print("Géométries décodées : ", data_decode)

            # Inverser les coordonnées (x, y) pour obtenir (latitude, longitude)
            data_reversed = [(y, x) for x, y in data_decode]

            # Créer une géométrie de type ligne
            line_geometry = QgsGeometry.fromPolylineXY([QgsPointXY(x, y) for x, y in data_reversed])

            return line_geometry
        except Exception as e:
            raise QgsProcessingException(f"Erreur lors du décodage de la polyligne : {str(e)}")


    def name(self):
        return 'WaypointsSequences'

    def displayName(self):
        return self.tr('Waypoints Sequences')

    def group(self):
        return "Les plugins restreints du pôle DG d\'Inddigo" 

    def groupId(self):
        return "Les plugins restreints du pôle DG d\'Inddigo" 

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return WaypointSequences()
    def shortHelpString(self):
        """
        Retourne le texte d'aide pour l'outil.
        """
        return """
            <h3>Outil Inddigo : Waypoints Sequences</h3>
            <p>Cet outil permet de calculer la séquence optimale de waypoints pour un itinéraire, 
            en utilisant les services HERE API pour le séquencement et le routage.</p>
            <h4>Paramètres :</h4>
            <ul>
                <li><b>Couche d'entrée</b> : La couche vectorielle contenant les points de l'itinéraire.</li>
                <li><b>Champ contenant un identifiant unique</b> : Un champ qui identifie de manière unique chaque point.</li>
                <li><b>Un champ pour regrouper les points par tournée</b> : Permet de regrouper les points en fonction d'une clé de groupe. Il doit donc être identique pour chaque tournée</li>
                <li><b>Le champ contenant la séquence</b> : Il faut définir le point de début pour chaque tournée en remplissant un "1",</li>
                <li>et si vous voulez indiquer le point final de la tournée, remplissez "2".</li>
                <li><b>Modes de transport</b> : Sélectionnez le mode de transport à utiliser (Piéton, Voiture, Camion).</li>
            </ul>
            <h4>Sorties :</h4>
            <ul>
                <li><b>Waypoints Output</b> : Une couche contenant les waypoints optimisés avec leur séquence.</li>
                <li><b>Route Output</b> : Une couche contenant les itinéraires entre les waypoints.</li>
            </ul>
            
        """
    
