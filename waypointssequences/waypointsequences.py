from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterString,
    QgsProcessingParameterFeatureSink,
    QgsFeature,
    QgsProcessing,
    QgsFeatureSink,QgsGeometry,
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
    GROUP_FIELD = 'GROUP_FIELD'
    SEQUENCE_FIELD = 'SEQUENCE_FIELD'
    WAYPOINTS_OUTPUT = 'WAYPOINTS_OUTPUT'
    INTERCONNECTIONS_OUTPUT = 'INTERCONNECTIONS_OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT,
            self.tr('Input point layer'),
            [QgsProcessing.TypeVectorPoint]
        ))
        
        self.addParameter(QgsProcessingParameterField(
            self.GROUP_FIELD,
            self.tr('Field for tour grouping'),
            parentLayerParameterName=self.INPUT
        ))
        
        self.addParameter(QgsProcessingParameterField(
            self.SEQUENCE_FIELD,
            self.tr('Field for point sequence'),
            parentLayerParameterName=self.INPUT
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.WAYPOINTS_OUTPUT,
            self.tr('Output waypoints'),
            QgsProcessing.TypeVectorPoint
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.INTERCONNECTIONS_OUTPUT,
            self.tr('Output interconnections'),
            QgsProcessing.TypeVectorLine
        ))

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsSource(parameters, self.INPUT, context)
        group_field = self.parameterAsString(parameters, self.GROUP_FIELD, context)
        sequence_field = self.parameterAsString(parameters, self.SEQUENCE_FIELD, context)

        (waypoints_sink, waypoints_sink_id) = self.parameterAsSink(
            parameters, self.WAYPOINTS_OUTPUT, context,
            layer.fields(), QgsProcessing.TypeVectorPoint, layer.sourceCrs()
        )
        
        (interconnections_sink, interconnections_sink_id) = self.parameterAsSink(
            parameters, self.INTERCONNECTIONS_OUTPUT, context,
            layer.fields(), QgsProcessing.TypeVectorLine, layer.sourceCrs()
        )

        if not waypoints_sink or not interconnections_sink:
            raise QgsProcessingException(self.tr("Sink not available."))

        # Collecter les points par tournée
        tours = {}
        for feature in layer.getFeatures():
            group = feature[group_field]
            sequence = feature[sequence_field]
            x, y = feature.geometry().asPoint()
            if group not in tours:
                tours[group] = []
            tours[group].append({
                'sequence': sequence,
                'x': x,
                'y': y,
                'id': feature.id(),
                'end': feature[sequence_field] == 2  # Point de fin
            })

        # Traitement des tournées
        for group, points in tours.items():
            feedback.pushInfo(f"Processing tour: {group}")
            points = sorted(points, key=lambda p: p['sequence'])
            start = f"{points[0]['y']},{points[0]['x']}"
            end = next((p for p in points if p['end']), None)

            destinations = ""
            for idx, point in enumerate(points[1:], start=1):
                destinations += f"destination{idx}={point['id']};{point['y']},{point['x']}&"
            
            # Construire l'URL
            url = (
                f"https://wps.hereapi.com/v8/findsequence2?mode=fastest;pedestrian;traffic:disabled;"
                f"&start={start}"
            )
            if end:
                url += f"&end={end['y']},{end['x']}"
            url += f"&{destinations}improveFor=TIME&apikey={api_key}"

            response = requests.get(url)
            if response.status_code == 200:
                json_data = response.text.split('processResults(')[1].split(')')[0]
                response_json = json.loads(json_data)
                # Process waypoints
                waypoints = response_json.get('results', [])[0].get('waypoints', [])
                for wp in waypoints:
                    f = QgsFeature()
                    f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(wp['lng'], wp['lat'])))
                    f.setAttributes([group, wp['id']])
                    waypoints_sink.addFeature(f, QgsFeatureSink.FastInsert)
                # Process interconnections
                interconnections = response_json.get('results', [])[0].get('interconnections', [])
                for ic in interconnections:
                    line_coords = [
                        (wp['lng'], wp['lat']) for wp in waypoints 
                        if wp['id'] in [ic['fromWaypoint'], ic['toWaypoint']]
                    ]
                    if len(line_coords) == 2:
                        f = QgsFeature()
                        f.setGeometry(QgsGeometry.fromPolylineXY([
                            QgsPointXY(*line_coords[0]), QgsPointXY(*line_coords[1])
                        ]))
                        f.setAttributes([group])
                        interconnections_sink.addFeature(f, QgsFeatureSink.FastInsert)
            else:
                feedback.reportError(f"Error for tour {group}: {response.status_code}")

        return {self.WAYPOINTS_OUTPUT: waypoints_sink_id, self.INTERCONNECTIONS_OUTPUT: interconnections_sink_id}

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
    
