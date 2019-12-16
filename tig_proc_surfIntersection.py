# -*- coding: utf-8 -*-


__author__ = 'Viktor Kondrashov'
__date__ = '2018-06-08'
__copyright__ = '(C) 2018 by Viktor Kondrashov'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import tempfile
import os

from qgis.PyQt.QtCore import QCoreApplication
from qgis.analysis import QgsRasterCalculatorEntry, QgsRasterCalculator
from qgis.core import *
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterField,
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingParameterFileDestination)

class TigSurfaceIntersectCorrectAlgorithm(QgsProcessingAlgorithm):
    OUTPUT_SURFACE = 'OUTPUT_RASTER'
    TOP_SURFACE = 'TOP_SURFACE'
    BOTTOM_SURFACE = 'BOTTOM_SURFACE'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def name(self):
        return 'TigSurfaceIntersectCorrectAlgorithm'

    def groupId(self):
        return 'PUMAgrids'

    def group(self):
        return self.tr('Сетки')

    def displayName(self):
        return self.tr(u'Пересечение поверхности')

    def createInstance(self):
        return TigSurfaceIntersectCorrectAlgorithm()

    def initAlgorithm(self, config):
        self.addParameter(QgsProcessingParameterRasterLayer(self.TOP_SURFACE,
                                          self.tr('Верхняя поверхность')))
        self.addParameter(QgsProcessingParameterRasterLayer(self.BOTTOM_SURFACE,
                                          self.tr('Нижняя поверхность')))

        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_SURFACE, self.tr('Результат')))


    def processAlgorithm(self, parameters, context, progress):
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT_SURFACE, context)

        bottomRaster = self.parameterAsRasterLayer(parameters, self.BOTTOM_SURFACE, context)
        topRaster = self.parameterAsRasterLayer(parameters, self.TOP_SURFACE, context)

        entries = []
        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@1'
        ras.raster = topRaster
        ras.bandNumber = 1
        entries.append(ras)
        ras1 = QgsRasterCalculatorEntry()
        ras1.ref = 'ras1@1'
        ras1.raster = bottomRaster
        ras1.bandNumber = 1
        entries.append(ras1)
        calc = QgsRasterCalculator('ras@1 + (ras1@1 - ras@1) * ((ras1@1 - ras@1) >= 0)', output, 'GTiff', bottomRaster.extent(),
                                   bottomRaster.width(), bottomRaster.height(), entries)
        calc.processCalculation()

        return {self.OUTPUT_SURFACE: output}

