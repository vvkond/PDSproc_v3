# -*- coding: utf-8 -*-


__author__ = 'Viktor Kondrashov'
__date__ = '2018-06-08'
__copyright__ = '(C) 2018 by Viktor Kondrashov'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import tempfile
import os

from qgis.PyQt.QtCore import QCoreApplication, QSettings, QProcess, QVariant
from qgis.analysis import QgsRasterCalculatorEntry, QgsRasterCalculator
from qgis.core import *
from processing.tools.system import getTempFilename
import processing
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

class TigSurfaceCorrectionAlgorithm(QgsProcessingAlgorithm):
    OUTPUT_LAYER = 'OUTPUT_LAYER'
    OUTPUT_QVECTOR = 'OUTPUT_QVECTOR'
    INPUT_LAYER = 'INPUT_LAYER'
    INPUT_FAULT = 'INPUT_FAULT'
    INPUT_FIELD = 'INPUT_FIELD'
    INPUT_RASTER = 'INPUT_RASTER'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def name(self):
        return 'TigSurfaceCorrectionAlgorithm'

    def groupId(self):
        return 'PUMAgrids'

    def group(self):
        return self.tr('Сетки')

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(u'Корректировка поверхности')

    def createInstance(self):
        return TigSurfaceCorrectionAlgorithm()

    def initAlgorithm(self, config):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_RASTER,
                                          self.tr(u'Поверхность для корректировки')))

        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_LAYER,
                                                            self.tr(u'Точки для корректировки поверхности'),
                                                            [QgsProcessing.TypeVectorPoint], '', False))
        self.addParameter(QgsProcessingParameterField(self.INPUT_FIELD, self.tr(u'Поле'), '',
                                              self.INPUT_LAYER, QgsProcessingParameterField.Numeric))

        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_FAULT,
                                          self.tr(u'Разломы'), [QgsProcessing.TypeVectorLine], '', True))

        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_LAYER, u'Откорректированная поверхность'))
        self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT_QVECTOR, u'Контроль качества корректировки'))

    def processAlgorithm(self, parameters, context, progress):
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT_LAYER, context)
        outputVector = self.parameterAsOutputLayer(parameters, self.OUTPUT_QVECTOR, context)
        inputFaultFilename = self.parameterAsString(parameters, self.INPUT_FAULT, context)
        inputField = self.parameterAsString(parameters, self.INPUT_FIELD, context)

        rasterLayer = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
        self.extent = rasterLayer.extent()

        pointsLayer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        pointsProvider = pointsLayer.dataProvider()

        tempResidualName = getTempFilename('shp')
        progress.pushInfo(tempResidualName)
        tempDeltasName = getTempFilename('tif')
        progress.pushInfo(tempDeltasName)

        fields = pointsProvider.fields()
        settings = QSettings()
        systemEncoding = settings.value('/UI/encoding', 'System')
        fields.append(QgsField('Delta1', QVariant.Double))
        writer = QgsVectorFileWriter(tempResidualName, systemEncoding,
                              fields,
                              QgsWkbTypes.Point, pointsProvider.crs(), 'ESRI Shapefile')

        #1. Extract surface points and write deltas
        progress.pushInfo('Step 1: Extraxt surface points and write deltas')
        features = pointsProvider.getFeatures()
        for f in features:
            pointGeom = f.geometry()
            if pointGeom.wkbType() == QgsWkbTypes.MultiPoint:
                pointPoint = pointGeom.asMultiPoint()[0]
            else:
                pointPoint = pointGeom.asPoint()

            attrs = f.attributes()
            inputAttr = float(f.attribute(inputField))

            outFeat = QgsFeature()
            outFeat.setGeometry(pointGeom)

            rastSample = rasterLayer.dataProvider().identify(pointPoint, QgsRaster.IdentifyFormatValue).results()
            if rastSample and len(rastSample):
                keys = list(rastSample.keys())
                attrs.append(inputAttr - float(rastSample[keys[0]]))
            else:
                attrs.append(None)

            outFeat.initAttributes(1)
            outFeat.setAttributes(attrs)
            writer.addFeature(outFeat)
        del writer
        writer = None
        progress.setProgress(25)


        #2.Make delta`s surface
        progress.pushInfo('Step 2: Make delta`s surface')
        strExtent = '{0},{1},{2},{3}'.format(self.extent.xMinimum(), self.extent.xMaximum(),
                                             self.extent.yMinimum(), self.extent.yMaximum())
        processing.run('PUMAplus:creategridwithfaults',
                       {"INPUT_LAYER": tempResidualName,
                        "INPUT_FIELD": 'Delta1',
                        "INPUT_FAULT" : inputFaultFilename,
                        "INPUT_EXTENT": strExtent,
                        "EXPAND_PERCENT_X" : '0',
                        "EXPAND_PERCENT_Y": '0',
                        "STEP_X": rasterLayer.rasterUnitsPerPixelX(),
                        "STEP_Y": rasterLayer.rasterUnitsPerPixelY(),
                        "OUTPUT_LAYER" : tempDeltasName},
                       feedback=progress)
        progress.setProgress(50)


        #3. Add input surface and delta`s surface
        progress.pushInfo('Step 3: Add input surface and delta`s surface')
        tempDeltasRaster = QgsRasterLayer(tempDeltasName, 'TempDeltasLayer')
        entries = []
        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@1'
        ras.raster = rasterLayer
        ras.bandNumber = 1
        entries.append(ras)
        ras1 = QgsRasterCalculatorEntry()
        ras1.ref = 'ras1@1'
        ras1.raster = tempDeltasRaster
        ras1.bandNumber = 1
        entries.append(ras1)
        calc = QgsRasterCalculator('ras@1 + ras1@1', output, 'GTiff', rasterLayer.extent(),
                                   rasterLayer.width(), rasterLayer.height(), entries)
        calc.processCalculation()
        progress.setProgress(75)

        # 4. Extract points from corrected surface
        progress.pushInfo('Step 5: Extract points from corrected surface')
        sumRaster = QgsRasterLayer(output, 'sumSurface')
        deltasLayer = QgsVectorLayer(tempResidualName, "testlayer_shp", "ogr")
        fields = deltasLayer.dataProvider().fields()
        fields.append(QgsField('Delta2', QVariant.Double))
        writer = QgsVectorFileWriter(outputVector, systemEncoding,
                              fields,
                              QgsWkbTypes.Point, pointsProvider.crs(), 'ESRI Shapefile')
        for f in deltasLayer.dataProvider().getFeatures():
            pointGeom = f.geometry()
            pointPoint = pointGeom.asPoint()

            attrs = f.attributes()
            inputAttr = float(f.attribute(inputField))

            outFeat = QgsFeature()
            outFeat.setGeometry(pointGeom)

            rastSample = sumRaster.dataProvider().identify(pointPoint, QgsRaster.IdentifyFormatValue).results()
            if rastSample and len(rastSample):
                keys = list(rastSample.keys())
                attrs.append(inputAttr - float(rastSample[keys[0]]))
            else:
                attrs.append(None)

            outFeat.initAttributes(1)
            outFeat.setAttributes(attrs)
            writer.addFeature(outFeat)
        del writer
        writer = None
        del sumRaster
        sumRaster = None

        progress.setProgress(100)
        return {self.OUTPUT_LAYER: output, self.OUTPUT_QVECTOR: outputVector}



