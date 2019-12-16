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

class TigVolumeMethodAlgorithm(QgsProcessingAlgorithm):
    OUTPUT_SURFACE = 'OUTPUT_RASTER'
    TOP_SURFACE = 'TOP_SURFACE'
    BOTTOM_SURFACE = 'BOTTOM_SURFACE'
    PORO_SURFACE = 'POROSITY_SURFACE'
    NTG_SURFACE = 'NTG_SURFACE'
    VNK_VALUE = 'VNK'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def name(self):
        return 'TigVolumeMethodAlgorithm'

    def groupId(self):
        return 'PUMAgrids'

    def group(self):
        return self.tr('Сетки')

    def displayName(self):
        return self.tr(u'Подсчет запасов объемным методом')

    def createInstance(self):
        return TigVolumeMethodAlgorithm()

    def initAlgorithm(self, config):
        self.addParameter(QgsProcessingParameterRasterLayer(self.TOP_SURFACE,
                                          self.tr('Поверхность кровли')))
        self.addParameter(QgsProcessingParameterRasterLayer(self.BOTTOM_SURFACE,
                                          self.tr('Поверхность подошвы')))
        self.addParameter(QgsProcessingParameterRasterLayer(self.NTG_SURFACE,
                                          self.tr('Поверхность песчанистости'), '', True))
        self.addParameter(QgsProcessingParameterRasterLayer(self.PORO_SURFACE,
                                          self.tr('Поверхность пористости'), '', True))
        self.addParameter(QgsProcessingParameterNumber(self.VNK_VALUE, self.tr('Уровень ВНК ')
                                                       , type= QgsProcessingParameterNumber.Double
                                                       , defaultValue=2500
                                                       , optional=False))

        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_SURFACE, self.tr('Output surface')))


    def processAlgorithm(self, parameters, context, progress):
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT_SURFACE, context)
        topRaster = self.parameterAsRasterLayer(parameters, self.TOP_SURFACE, context)
        bottomRaster = self.parameterAsRasterLayer(parameters, self.BOTTOM_SURFACE, context)
        ntgRaster = self.parameterAsRasterLayer(parameters, self.NTG_SURFACE, context)
        poroRaster = self.parameterAsRasterLayer(parameters, self.PORO_SURFACE, context)
        vnkValue = self.parameterAsDouble(parameters, self.VNK_VALUE, context)

        formula = '( base@1 - top@1 ) * ( base@1 <= {0} ) + ( {0} - top@1 ) * ( base@1 > {0} ) * ' \
                  '( (  base@1 - top@1 ) * ( base@1 <= {0}) + ( {0} - top@1 ) * ( base@1 > {0} ) > 0)'.format(vnkValue)

        entries = []
        ras = QgsRasterCalculatorEntry()
        ras.ref = 'top@1'
        ras.raster = topRaster
        ras.bandNumber = 1
        entries.append(ras)
        ras1 = QgsRasterCalculatorEntry()
        ras1.ref = 'base@1'
        ras1.raster = bottomRaster
        ras1.bandNumber = 1
        entries.append(ras1)
        calc = QgsRasterCalculator(formula, output, 'GTiff', bottomRaster.extent(),
                                   bottomRaster.width(), bottomRaster.height(), entries)
        calc.processCalculation(progress)

        return {self.OUTPUT_SURFACE: output}

