# -*- coding: utf-8 -*-

"""
/***************************************************************************
Isochrone_GIS_processing
                                 A QGIS plugin
 Outil de calcul de temps de trajets multimodaux
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-10-11
        copyright            : (C) 2024 by C.Garcia - JL.Humbert from Inddigo
        email                : c.garcia@inddigo.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'C.Garcia - JL.Humbert from Inddigo'
__date__ = '2024-10-11'
__copyright__ = '(C) 2024 by C.Garcia - JL.Humbert from Inddigo'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'
from qgis.PyQt.QtWidgets import QMessageBox

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsProcessingParameterField,
                       QgsProcessingParameterDateTime,
                       QgsProcessingParameterString,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterNumber,
                       QgsFeature,
                       QgsWkbTypes,
                       QgsField, 
                       QgsFeature,
                       QgsProcessingException,
                       QgsFields,
                       QgsExpressionContextUtils
                       )
from PyQt5.QtCore import QVariant
from .modules.get_iso import iso


from .utils.utils import clean_intermediate_values, saveInDbIso

class isochroneAlgorithm(QgsProcessingAlgorithm):
    
    def __init__(self):
        super().__init__()
        
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    OUTPUT = 'OUTPUT'
    INPUT1 = 'INPUT1'
    ID_FIELD1_JOIN = 'ID_FIELD1_JOIN'
    DATE_FIELD = 'DATE_FIELD'
    CKB_DEPART_OU_ARRIVEE = 'CKB_DEPART_OU_ARRIVEE'
    CHECKBOXES_MODES = 'CHECKBOXES_MODES'
    CHECKBOXES_RANGE = 'CHECKBOXES_RANGE'
    DIST_MAX_MARCHE = 'DIST_MAX_MARCHE'
    VALEURS = 'VALEURS'
    BUFFER = "BUFFER"


    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT1,
                self.tr('Couche de point '),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Resultat isochrone')
            )
        )


                # Ajout d'un paramètre de calendrier
        self.addParameter(
            QgsProcessingParameterDateTime(
                self.DATE_FIELD,
                self.tr('Selectionner une date'),
                defaultValue=None,  # Vous pouvez définir une valeur par défaut
                optional=False  # Permet de rendre le paramètre facultatif
            )
        )

        # Paramètre pour une liste de valeurs texte séparées
        self.addParameter(
            QgsProcessingParameterEnum(
                self.CKB_DEPART_OU_ARRIVEE,
                self.tr("Selectionnez si l'heure indiquée est celle de départ ou d'arrivée"),
                options=["Heure de départ", "Heure d'arrivée"],
                allowMultiple=False,  # Ne permet de cocher qu'une seule réponse
                defaultValue= 1    
            )
        )

        # Boutons à cocher simulés avec un Enum à sélection multiple
        self.addParameter(
            QgsProcessingParameterEnum(
                self.CHECKBOXES_MODES,
                self.tr("Selectionnez les modes que vous voulez requêter"),
                options=["Piéton", "Vélo", "VAE","Voiture"],
                allowMultiple=True,  # Permet de cocher plusieurs options
                defaultValue=[0]  # Option 1 et 2 cochées par défaut
            )
        )

        # Boutons à cocher simulés avec un Enum à sélection multiple
        self.addParameter(
            QgsProcessingParameterEnum(
                self.CHECKBOXES_RANGE,
                self.tr("Selectionnez la valeur que vous voulez requêter"),
                options=["Distance", "Temps"],
                allowMultiple=False,  # Permet de cocher plusieurs options
                defaultValue=1  # Option 1 et 2 cochées par défaut
            )
        )

        # Paramètre valeur max
        self.addParameter(
            QgsProcessingParameterString(
                self.VALEURS,
                self.tr("Entrez la(les) valeur(s) nécessaire(s) à la construction des isochrones séparées par des virgules (En mètre ou en seconde)")
            )
        )

        # Paramètre buffer
        self.addParameter(
            QgsProcessingParameterNumber(
                self.BUFFER,
                self.tr("Taille du buffer (en mètres)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0,
                optional=True
            )
        )



    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        # Obligé de faire l'import ici et pas eu début car sinon erreur de type 'import ciruclaire' (connaissait pas...)
        from ..PluginsInddigoDGLimited_provider import PluginsInddigoDGLimitedProvider

        # Appel du provider
        provider = PluginsInddigoDGLimitedProvider()
        # Récupérer la clé d'API
        Herekey = provider.test_API()

        
        if Herekey is None:
            feedback.pushInfo("La clé API Here est manquante.")
            return {}

        # Si la clé API existe, continuez le traitement
        feedback.pushInfo(f"Clé API Here récupérée : {Herekey}")
        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source1 = self.parameterAsSource(parameters, self.INPUT1, context)
        selected_date = self.parameterAsDateTime(parameters, self.DATE_FIELD, context)
        checkboxes_modes = self.parameterAsEnums(parameters, self.CHECKBOXES_MODES, context)
        range_checkboxes = self.parameterAsEnums(parameters, self.CHECKBOXES_RANGE, context)
        valeurs = self.parameterAsString(parameters,self.VALEURS, context)
        buffer_size = self.parameterAsDouble(parameters, self.BUFFER, context)

        if not source1:
            raise QgsProcessingException("Impossible de charger les couches d'entrée.")
        
        # Vérification du CRS de la couche
        crs_wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
        source_crs = source1.sourceCrs()
        transform_to_wgs84 = None

        if source_crs != crs_wgs84:
            feedback.pushInfo("La couche n'est pas en WGS84. Transformation en cours...")
            transform_to_wgs84 = QgsCoordinateTransform(source_crs, crs_wgs84, context.transformContext())
        else:
            transform_to_wgs84 = None
            feedback.pushInfo("La couche est déjà en WGS84.")
        
        # Récupération des champs existants + combinés ces derniers
        fields = QgsFields()  # Initialise un objet QgsFields vide
        for field in source1.fields():  # Appelez la méthode fields() pour obtenir la liste des champs
            fields.append(field)

        # Ajout des nouveaux champs
        new_fields = [
            QgsField("Mode", QVariant.String),
            QgsField("Date", QVariant.String),
            QgsField("Option", QVariant.String),
            QgsField("Valeur", QVariant.Int),
            QgsField("Buffer_m", QVariant.Int)
        ]

        for new_field in new_fields:
            fields.append(new_field)

        # Création du sink avec les champs combinés
        sink, errorMsg = self.parameterAsSink(parameters,self.OUTPUT, context, fields, QgsWkbTypes.Polygon, crs_wgs84)
        if not sink:
            raise QgsProcessingException(f"Erreur lors de la création de la couche de sortie : {errorMsg}.")
        
        selected_index = self.parameterAsEnum(parameters, self.CKB_DEPART_OU_ARRIVEE, context)
        # Transformation des indices de CHECKBOXES_MODES en noms d'options
        options = ["Heure de départ", "Heure d'arrivée"]
        selected_heure = options[selected_index]

        # Transformation des indices de CHECKBOXES_RANGE en noms d'options
        selected_range_value = "distance" if range_checkboxes == 0 else "time"

        print("Range sélectionné :", selected_range_value)

        # Transformation des indices de CHECKBOXES_MODES en noms d'options
        options_modes = ["Piéton", "Vélo", "VAE","Voiture"]
        selected_mode_values = [
            'pedestrian' if options_modes[i] == 'Piéton' else
            'bicycle' if options_modes[i] == 'Vélo' else
            'car' if options_modes[i] == 'Voiture' else
            'vae' if options_modes[i] == 'VAE' else

            options_modes[i] for i in checkboxes_modes
        ]
        print("Modes sélectionnés :", selected_mode_values)

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source1.featureCount() if source1.featureCount() else 0
        features1 = list(source1.getFeatures())

        # Conversion de QDateTime en datetime standard de Python
        python_datetime = selected_date.toPyDateTime()

        # Formatage de la date selon le format désiré
        formatted_datetime = python_datetime.strftime("%Y-%m-%dT%H:%M:%S")        

        # Type d'heure à requêter + changement du type de lieu (origine ou destination) en conséquence
        if "Heure de départ" in selected_heure:
            type_heure = 'departureTime='
            type_lieu = f'origin='
        else:
            type_heure = 'arrivalTime='
            type_lieu = f'destination='
        
     

        # Appel de la fonction pour formatter les valeurs intermédiaires (supprimant les espaces inutiles et séparer les valeurs par des virgules)
        try :
            value = clean_intermediate_values(valeurs)
        except TypeError as e :
            print(f"Erreur : {e}")

        # Parcours des feature
        for current, feature1 in enumerate(features1):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break


            # Récupère la géométrie
            geometry1 = feature1.geometry()
            # Transformer la géométrie en WGS84 si nécessaire
            if transform_to_wgs84:
                geometry1.transform(transform_to_wgs84)
            combined_attributes = feature1.attributes()


            # Vérifie si la géométrie est un point et extrait les coordonnées
            if geometry1 and geometry1.type() == QgsWkbTypes.PointGeometry:
                point1 = geometry1.asPoint()
                s_olng, s_olat = point1.x(), point1.y()
            else:
                feedback.pushInfo(f"Feature {feature1.id()} n'a pas de géométrie valide. Ignoré.")
                continue

            # Calcul des isochrones pour chaque mode sélectionné
            for mode in selected_mode_values:
                feedback.pushInfo(f"Calcul de l'isochrone pour le mode {mode}")
                
                try :
                    # Appel à la fonction iso
                    results = iso(
                        s_olat, s_olng, mode, selected_range_value, type_heure,
                        type_lieu, formatted_datetime, value, Herekey
                    )
                    saveInDbIso(mode)

                    print(results)
                    
                    for polygon_iso, valeur in results:
                        enriched_attributes = combined_attributes + [
                            mode, formatted_datetime, selected_range_value, valeur, buffer_size
                        ]

                        # Vérifier si un buffer doit être appliqué
                        if buffer_size > 0:
                            # Transformer en CRS métrique (par exemple EPSG:2154 pour Lambert 93)
                            crs_projected = QgsCoordinateReferenceSystem("EPSG:2154")
                            transform_to_projected = QgsCoordinateTransform(crs_wgs84, crs_projected, context.transformContext())
                            transform_to_wgs84_back = QgsCoordinateTransform(crs_projected, crs_wgs84, context.transformContext())

                            # Appliquer la transformation pour buffer
                            polygon_iso.transform(transform_to_projected)
                            polygon_iso = polygon_iso.buffer(buffer_size, segments=360)

                            # Revenir au CRS WGS84
                            polygon_iso.transform(transform_to_wgs84_back)

                        # Crée une nouvelle entité avec les attributs enrichis
                        new_feature = QgsFeature(fields)
                        new_feature.setGeometry(polygon_iso)
                        new_feature.setAttributes(
                            enriched_attributes
                        )

                        # Ajoute l'entité au `sink`
                        sink.addFeature(new_feature, QgsFeatureSink.FastInsert)
                        print(f"Feature ajoutée avec géométrie : {new_feature.geometry().asWkt()}")
                except Exception as e:
                    feedback.pushInfo(f"Erreur lors du traitement du mode {mode} : {e}")

            # Mise à jour de la barre de progression
            feedback.setProgress(int(current * total))

        feedback.pushInfo("Traitement terminé avec succès.")
        return {self.OUTPUT: sink}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Isochrone'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return 'Isochrone'

    def group(self):
        return "Les plugins restreints du pôle DG d\'Inddigo" 

    def groupId(self):
        return 'Les plugins restreints du pôle DG d\'Inddigo'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return isochroneAlgorithm()

    def shortHelpString(self):
        """
        Retourne le texte d'aide pour l'outil.
        """
        return """
            <h3>Outil Inddigo : Isochrone_processing</h3>
            <p>Ce plugin permet de :</p>
            <ul>
                <li>Calculer les isochrones/isodistances pour différents modes de transport :</li>
                <ul>
                    <li><b>Piéton :</b> Calcul des isochrones/isodistances de trajet à pied.</li>
                    <li><b>Vélo :</b> Calcul des isochrones/isodistances pour les vélos traditionnels et VAE.</li>
                    <li><b>Voiture :</b> Calcul des isochrones/isodistances en voiture, avec ou sans trafic.</li>
                </ul>
            </ul>
            <h4>Paramètres</h4>
            <ul>
                <li><b>Couche d'entrée :</b> La couche contenant les points d'origine.</li>
                <li><b>Date et heure :</b> Paramètre permettant de spécifier la date et l'heure pour le calcul des isochrones.</li>
                <li><b>Type d'heure :</b> Spécifie si l'heure fournie correspond à une heure de départ ou d'arrivée.</li>
                <li><b>Modes de transport :</b> Sélectionnez les modes de transport à inclure dans les calculs.</li>
                <li><b>Mode distance ou temps :</b> Sélectionner si vous voulez calculer des isochrones (facteur temps) ou des isodistances (facteur distance).</li>
                <li><b>Valeur(s) à requêter :</b> Sélectionne la ou les valeurs nécessaires à la construction du ou des différentes zones de chalandises. Chaque valeur doit être séparée par des virgules avec ou sans espaces.</li>
            </ul>
            <p>Le résultat est une couche géographique ayant pour géométrie les isochrones/isodistances ainsi calculés pour chaque mode de transport et récapitulant les options choisies pour construire cette nouvelle couche.</p>
            <h4>Sorties</h4>
            <ul>
                <li><b>Couche résultat :</b> La couche résultante contenant les isochrones calculés pour chaque mode sélectionné.</li>
            </ul>
        """