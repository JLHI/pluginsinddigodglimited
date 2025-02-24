# -*- coding: utf-8 -*-

"""
/***************************************************************************
 PluginsInddigoDGLimited
                                 A QGIS plugin
 Les plugins non restreint du pôle DG d'Inddigo
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-11-22
        copyright            : (C) 2024 by JLHI
        email                : jl.humbert@inddigo.com
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

__author__ = 'JLHI'
__date__ = '2024-11-22'
__copyright__ = '(C) 2024 by JLHI'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.core import QgsProcessingProvider, QgsExpressionContextUtils
from qgis.PyQt.QtWidgets import QMessageBox
from .waypointssequences.waypointsequences import WaypointSequences
from .multimode.Multimode_GIS_processing_algorithm import Multimode_GIS_processingAlgorithm
from .isochrones.isochrones_algorithm import isochroneAlgorithm

class PluginsInddigoDGLimitedProvider(QgsProcessingProvider):

    def __init__(self):
        """
        Default constructor.
        """
        QgsProcessingProvider.__init__(self)

    def unload(self):
        """
        Unloads the provider. Any tear-down steps required by the provider
        should be implemented here.
        """
        pass

    def test_API(self):
        """
        Récupère la clé API Here à partir d'une variable globale QGIS.
        Si la clé est absente, affiche un avertissement.
        """
        Herekey = None
        # Replace 'variable_name' with the name of your global variable
        variable_name = 'hereapikey'

        # Get the global variable value 
        Herekey = QgsExpressionContextUtils.globalScope().variable(variable_name)
        if Herekey is None : 
            QMessageBox.warning(
                None,
                (
                    "Clé manquante", 
                    "Attention : La clé Here n'est pas configurée. Vous devez ajouter une variable globale 'hereapikey' et saisir votre api Here, puis recharger le plugin"
                )
            )
        return Herekey        

    def loadAlgorithms(self):
        """
        Loads all algorithms belonging to this provider.
        """
        #self.addAlgorithm(PluginsInddigoDGAlgorithm())

        self.addAlgorithm(WaypointSequences())
        self.addAlgorithm(Multimode_GIS_processingAlgorithm())
        self.addAlgorithm(isochroneAlgorithm())

        # add additional algorithms here
        # self.addAlgorithm(MyOtherAlgorithm())

    def id(self):
        """
        Returns the unique provider id, used for identifying the provider. This
        string should be a unique, short, character only string, eg "qgis" or
        "gdal". This string should not be localised.
        """
        return 'PluginsInddigoDGLimited'

    def name(self):
        """
        Returns the provider name, which is used to describe the provider
        within the GUI.

        This string should be short (e.g. "Lastools") and localised.
        """
        return self.tr('PluginsInddigoDGLimited')

    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QgsProcessingProvider.icon(self)

    def longName(self):
        """
        Returns the a longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Lastools LIDAR tools
        (version 2.2.1)". This string should be localised. The default
        implementation returns the same string as name().
        """
        return self.name()
