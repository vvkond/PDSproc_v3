# -*- coding: utf-8 -*-

__author__ = 'Viktor Kondrashov'
__date__ = '2017-05-08'
__copyright__ = '(C) 2017 by Viktor Kondrashov'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import tempfile
import os
import shutil

from qgis.PyQt.QtCore import QCoreApplication, QSettings, QProcess, QVariant
from qgis.utils import iface
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


class TigReservesByRasterAlgorithm(QgsProcessingAlgorithm):
    """This is an example algorithm that takes a vector layer and
    creates a new one just with just those features of the input
    layer that are selected.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the GeoAlgorithm class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT_LAYER = 'OUTPUT_LAYER'
    INPUT_LAYER = 'INPUT_LAYER1'
    INPUT_POLYGON = 'INPUT_POLYGON'
    INTERVAL = 'INTERVAL'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def name(self):
        return 'TigReservesByRasterAlgorithm'

    def groupId(self):
        return 'PUMAgrids'

    def group(self):
        return self.tr('Сетки')

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(u'Подсчет запасов')

    def shortDescription(self):
        self.tr("Подсчет запасов с использованием поверхности кровли и полигона ВНК")
        # self.tr(u" Calculate HC reserves using TopTVD raster and OWC\
        #                                     polygon imported from corporate database")

    def createInstance(self):
        return TigReservesByRasterAlgorithm()

    def initAlgorithm(self, config):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        self.addParameter(
            QgsProcessingParameterRasterLayer(self.INPUT_LAYER, self.tr('Поверхность'))
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(self.INPUT_POLYGON,
                                              self.tr('Полигон ВНК'),
                                              [QgsProcessing.TypeVectorPolygon, QgsProcessing.TypeVectorLine],
                                              '', False)
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_LAYER,
                self.tr('Таблица')
                ,'CSV файлы(*.csv *.CSV);;Все файлы (*.*)')
        )


    def processAlgorithm(self, parameters, context, feedback):
        self.mProgress = feedback

        in_tvd = self.parameterAsString(parameters, self.INPUT_LAYER, context)
        in_owc = self.parameterAsString(parameters, self.INPUT_POLYGON, context)
        out_Reserves = self.parameterAsFileOutput(parameters, self.OUTPUT_LAYER, context)

        # Initialise temporary variables
        # Polygons creared from lines
        rasterLayer = self.parameterAsRasterLayer(parameters, self.INPUT_LAYER, context)
        vectorLayer = self.parameterAsVectorLayer(parameters, self.INPUT_POLYGON, context)
        geometryType = vectorLayer.wkbType()
        owc_poly_tmp = in_owc
        if geometryType == QgsWkbTypes.LineString:
            owc_poly_tmp = getTempFilename('shp')
            processing.run("qgis:linestopolygons", {"INPUT": vectorLayer, "OUTPUT": owc_poly_tmp},
                           context=context, feedback=feedback)

        #Get raster info
        extent = rasterLayer.extent()
        provider = rasterLayer.dataProvider()
        rows = rasterLayer.rasterUnitsPerPixelY()
        cols = rasterLayer.rasterUnitsPerPixelX()
        block = provider.block(1, extent, rows, cols)
        noDataValue = block.noDataValue()
        cellSizeX = rasterLayer.rasterUnitsPerPixelX()
        cellSizeY = rasterLayer.rasterUnitsPerPixelY()
        cellArea = cellSizeX * cellSizeY

        # Clipped raster
#        tvd_clip_r = getTempFilename('tif')#scratch + "\\tvd_clip_r"
        points_v = getTempFilename('shp')#scratch + "\\out_r"
        # statistic = scratch + "\\statistic"

        #Raster to points
        self.mProgress.pushInfo('Convert raster to point node')
        self.mProgress.pushInfo(points_v)
        processing.run('saga:rastervaluestopoints', {"GRIDS": [in_tvd],
                                                   "POLYGONS": owc_poly_tmp,
                                                   "TYPE": 0,
                                                   "SHAPES":points_v},
                       context=context, feedback=feedback)
        pointsLayer = QgsVectorLayer(points_v, 'nodes', 'ogr')

        # Process: Extract by Mask
#        processing.runalg('gdalogr:cliprasterbymasklayer', {"INPUT":in_tvd,
#                                                            "MASK":owc_poly_tmp,
#                                                            "NO_DATA": noDataValue,
#                                                            "OUTPUT":tvd_clip_r} )
#        progress.setInfo("Clipped raster:{}".format(tvd_clip_r))

        try:
            fields = pointsLayer.fields()
            lastField = fields.count()-1
            lastFieldName = fields[lastField].name()
            tvdMAX = pointsLayer.maximumValue(lastField)
            tvdMIN = pointsLayer.minimumValue(lastField)
        except Exception as e:
            self.mProgress.setInfo(str(e))
            return

        NoIntervals = 5
        thick = int((float(tvdMAX) - float(tvdMIN)) / NoIntervals)

        # Write raster_area to a  file
        # workfile=scratch + "\\raster_area.txt"
        f = open(out_Reserves, 'w')
        f.write("DEPTH;CumArea@F90;F50;F10 \n")
        f.close()

        # simple list
        list1 = []
        # nested list
        outline = []
        self.curVolume = 0
        for i in range(NoIntervals + 1):
            slice = int(float(tvdMIN) / thick + i + 1) * thick

            expr = QgsExpression('\"{0}\">\'{1}\' AND \"{2}\"<=\'{3}\''.format(lastFieldName, slice-thick, lastFieldName, slice))
            searchRes = pointsLayer.getFeatures(QgsFeatureRequest(expr))
            num = 0
            for f in searchRes:
                num += 1
            list1.append(slice)
            list1.append(num * cellArea)
            outline.append(list1)
            list1 = []

        f = open(out_Reserves, 'a')
        for i in range(len(outline)):
            if (i == 0):
                p90 = float(outline[0][1]) * 0.8 / 1000000
            else:
                p90 = float(outline[i - 1][1]) / 1000000
            if (i == len(outline) - 1):
                p10 = float(outline[i][1]) * 1.2 / 1000000
            else:
                p10 = float(outline[i + 1][1]) / 1000000
            output = str(outline[i][0]) + ";" + str(p90) + ";" + str(float(outline[i][1]) / 1000000) + ";" + str(
                p10) + "\n"
            f.write(output)
        f.close()

        return {self.OUTPUT_LAYER: out_Reserves}

    def error(self, msg):
        print("Error", msg)

    def setCommand(self, cmd):
        return

    def addMessage(self, fmt, *a, **kw):
        print(fmt.format(*a, **kw))

    def setPercentage(self, val):
        return

    def setText(self, text):
        return

    def setInfo(self, text):
        self.mProgress.setInfo(text)

    def setConsoleInfo(self, text):
        if 'Grid Volume: Volume:' in text:
            ss = text.replace('Grid Volume: Volume:', '')
            self.curVolume = float(ss)


