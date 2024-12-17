from qgis.PyQt.QtCore import QCoreApplication,QVariant
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterString,
    QgsProcessingParameterFeatureSink,
    QgsFeature,
    QgsProcessing,QgsWkbTypes,
    QgsFeatureSink,QgsGeometry,QgsFields,QgsField,
    QgsMessageLog,QgsPointXY,QgsProcessingException,QgsExpressionContextUtils
)
import requests
import json


api_key = None
# Replace 'variable_name' with the name of your global variable
variable_name = 'hereapikey'

# Get the global variable value
try : 
    api_key = QgsExpressionContextUtils.globalScope().variable(variable_name)
except Exception as e: 
    print(e)

class WaypointSequences(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    WAYPOINTS_OUTPUT = 'WAYPOINTS_OUTPUT'
    GROUP_FIELD = 'GROUP_FIELD'
    SEQUENCE_FIELD = 'SEQUENCE_FIELD'
    ROUTE_OUTPUT = 'ROUTE_OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT, self.tr('Input Layer'), [QgsProcessing.TypeVectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.GROUP_FIELD, self.tr('Group Field'), defaultValue=''
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.SEQUENCE_FIELD, self.tr('Sequence Field'), defaultValue=''
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.WAYPOINTS_OUTPUT, self.tr('Waypoints Output')
            )
        )



    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsSource(parameters, self.INPUT, context)
        group_field = self.parameterAsString(parameters, self.GROUP_FIELD, context)
        sequence_field = self.parameterAsString(parameters, self.SEQUENCE_FIELD, context)

        # HERE API Key and URLs
        here_api_key = "YOUR_HERE_API_KEY"  # Replace with your actual HERE API key
        sequence_url = "https://wps.hereapi.com/v8/findsequence2"
        routing_url = "https://router.hereapi.com/v8/routes"

        # Define output fields for waypoints
        fields = QgsFields()
        fields.append(QgsField("fid", QVariant.Int))
        fields.append(QgsField("waypointID", QVariant.String))
        fields.append(QgsField("sequence", QVariant.Int))
        fields.append(QgsField("latitude", QVariant.Double))
        fields.append(QgsField("longitude", QVariant.Double))

        # Create output sink
        (waypoints_sink, waypoints_sink_id) = self.parameterAsSink(
            parameters, self.WAYPOINTS_OUTPUT, context,
            fields, QgsWkbTypes.Point, layer.sourceCrs()
        )

        # Helper function: Call the HERE Sequence API
        def get_sequence_data(start_coords, destinations):
            params = {
                "apikey": here_api_key,
                "mode": "fastest;pedestrian;traffic:disabled;",
                "start": start_coords,
            }
            for i, dest in enumerate(destinations):
                params[f"destination{i+1}"] = dest
            response = requests.get(sequence_url, params=params)
            if response.status_code != 200:
                raise QgsProcessingException(
                    f"Failed to get sequence data: {response.status_code}"
                )
            return response.json()

        # Helper function: Call the HERE Routing API for a pair of points
        def call_here_routing_api(start, end):
            params = {
                "origin": f"{start['lat']},{start['lng']}",
                "destination": f"{end['lat']},{end['lng']}",
                "transportMode": "pedestrian",
                "return": "polyline,summary",
                "apikey": here_api_key
            }
            response = requests.get(routing_url, params=params)
            return response.json()

        # Extract waypoints from the input layer
        start_coords = None
        destinations = []
        for feature in layer.getFeatures():
            group = feature[group_field]
            sequence = feature[sequence_field]
            geom = feature.geometry()
            if geom and geom.isPoint():
                point = geom.asPoint()
                lat, lng = point.y(), point.x()
                if sequence == 0:
                    start_coords = f"{lat},{lng}"
                else:
                    destinations.append(f"{group};{lat},{lng}")

        if not start_coords or not destinations:
            raise QgsProcessingException("No valid start or destination points found.")

        # Query HERE API to get ordered waypoints
        feedback.pushInfo("Querying HERE Sequence API...")
        sequence_data = get_sequence_data(start_coords, destinations)
        waypoints = sequence_data.get('results', [])[0].get('waypoints', [])
        waypoints_sorted = sorted(waypoints, key=lambda x: x['sequence'])

        # Write waypoints to the output layer
        feedback.pushInfo("Writing waypoints to output layer...")
        fid_counter = 0
        for i, waypoint in enumerate(waypoints_sorted):
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

            # Call HERE Routing API for consecutive waypoints
            if i < len(waypoints_sorted) - 1:
                start_point = waypoint
                end_point = waypoints_sorted[i + 1]
                route_response = call_here_routing_api(start_point, end_point)
                route_summary = route_response.get('routes', [])[0].get('sections', [])[0].get('summary', {})
                feedback.pushInfo(
                    f"Route {i} → {i+1}: Distance {route_summary.get('length')}m, "
                    f"Time {route_summary.get('duration')}s"
                )

        feedback.pushInfo("Processing completed successfully.")
        return {self.WAYPOINTS_OUTPUT: waypoints_sink_id}


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
    
