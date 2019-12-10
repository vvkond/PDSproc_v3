# -*- coding: utf-8 -*-


__author__ = 'Viktor Kondrashov'
__date__ = '2017-05-08'
__copyright__ = '(C) 2017 by Viktor Kondrashov'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import tempfile
import os

from qgis.PyQt.QtCore import QCoreApplication, QSettings, QProcess, QVariant
from qgis.utils import iface
from qgis.core import *
from processing.tools.system import getTempFilename
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterField,
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterNumber)

class TigSurfitAlgorithm(QgsProcessingAlgorithm):
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
    INPUT_LAYER = 'INPUT_LAYER'
    INPUT_FIELD = 'INPUT_FIELD'
    INPUT_LAYER1 = 'INPUT_LAYER1'
    INPUT_FIELD1 = 'INPUT_FIELD1'
    INPUT_LAYER2 = 'INPUT_LAYER2'
    INPUT_FIELD2 = 'INPUT_FIELD2'
    INPUT_LAYER3 = 'INPUT_LAYER3'
    INPUT_FIELD3 = 'INPUT_FIELD3'
    INPUT_FAULT = 'INPUT_FAULT'
    STEP_X_VALUE = 'STEP_X'
    STEP_Y_VALUE = 'STEP_Y'
    EXPAND_PERCENT_X = 'EXPAND_PERCENT_X'
    EXPAND_PERCENT_Y = 'EXPAND_PERCENT_Y'
    INPUT_EXTENT = 'INPUT_EXTENT'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def name(self):
        return 'TigSurfitAlgorithm'

    def groupId(self):
        return 'PUMAgrids'

    def group(self):
        return self.tr('Сетки')

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Создать сетку с разломами')

    def createInstance(self):
        return TigSurfitAlgorithm()

    def initAlgorithm(self, config):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(QgsProcessingParameterFeatureSource(
                                        self.INPUT_LAYER,
                                        self.tr('Исходные данные 1'),
                                        [QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVectorLine], optional=False))

        self.addParameter(QgsProcessingParameterField(self.INPUT_FIELD, self.tr('Поле 1'), '',
            self.INPUT_LAYER, QgsProcessingParameterField.Numeric))

        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_LAYER1,
                                          2*' ' + self.tr('Исходные данные 2'),
                                          [QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVectorLine],
                                          '', optional=True))

        self.addParameter(QgsProcessingParameterField(self.INPUT_FIELD1, 2*' ' + self.tr('Поле 2'), '',
                                              self.INPUT_LAYER1, QgsProcessingParameterField.Numeric, optional=True))

        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_LAYER2,
                                          4*' ' + self.tr('Исходные данные 3'),
                                          [QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVectorLine], '', optional=True))

        self.addParameter(QgsProcessingParameterField(self.INPUT_FIELD2, 4*' ' + self.tr('Поле 3'), '',
                                              self.INPUT_LAYER2, QgsProcessingParameterField.Numeric, optional=True))

        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_LAYER3,
                                          6*' ' + self.tr('Исходные данные 4'),
                                          [QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVectorLine], '', optional=True))

        self.addParameter(QgsProcessingParameterField(self.INPUT_FIELD3, 6*' ' + self.tr('Поле 4'), '',
                                              self.INPUT_LAYER3, QgsProcessingParameterField.Numeric, optional=True))

        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_FAULT,
            u'Разломы ', [QgsProcessing.TypeVectorLine], '', optional=True))

        self.addParameter(QgsProcessingParameterExtent(self.INPUT_EXTENT, u'Границы ', optional=True))

        self.addParameter(QgsProcessingParameterNumber(self.STEP_X_VALUE, u'Шаг по X ',
                                                       type= QgsProcessingParameterNumber.Double,
                                                       defaultValue=0, optional=True))
        self.addParameter(QgsProcessingParameterNumber(self.STEP_Y_VALUE, u'Шаг по Y ',
                                                       type= QgsProcessingParameterNumber.Double,
                                                       defaultValue=0, optional=True))

        self.addParameter(QgsProcessingParameterNumber(self.EXPAND_PERCENT_X, u'Расширение по X (%)',
                                                       type=QgsProcessingParameterNumber.Double,
                                                       defaultValue=10, optional=True))
        self.addParameter(QgsProcessingParameterNumber(self.EXPAND_PERCENT_Y, u'Расширение по Y (%)',
                                                       type=QgsProcessingParameterNumber.Double,
                                                       defaultValue=10, optional=True))

        # We add a raster layer as output
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_LAYER, u'Поверхность'))

    def processAlgorithm(self, parameters, context, feedback):
        """Here is where the processing itself takes place."""

        # The first thing to do is retrieve the values of the parameters
        # entered by the user
        # inputFilename = self.getParameterValue(self.INPUT_LAYER)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT_LAYER, context)

        self.plugin_dir = os.path.dirname(__file__)
        self.tempPointsFilename = getTempFilename('txt').replace("\\","/")
        self.tclFilename = getTempFilename('tcl')
        self.faultFilename = None

        outputFilename, ext = os.path.splitext(output)
        self.grdFilename = getTempFilename('grd').replace("\\","/")

        # if inputFilename is None:
        #     return

        vectorLayer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        self.extent = vectorLayer.extent()
        provider = vectorLayer.dataProvider()

        ext = self.parameterAsExtent(parameters, self.INPUT_EXTENT, context)
        if not ext.isEmpty():
            self.extent = QgsRectangle(ext)


        self.stepX = self.parameterAsDouble(parameters, self.STEP_X_VALUE, context)
        self.stepY = self.parameterAsDouble(parameters, self.STEP_Y_VALUE, context)
        if self.stepX < 1:
            self.stepX = self.extent.width() / 100
        if self.stepY < 1:
            self.stepY = self.extent.height() / 100

        if not self.prepareInputData(parameters, context, feedback):
            return

        self.prepareJob(parameters, context)
        self.runSurfit(feedback)

        runStr = 'gdal_translate -a_nodata -999 -a_srs "{0}" "{1}" "{2}"'.format(provider.crs().toProj4(), self.grdFilename, output )
        self.runProcess(runStr, feedback)
        return {self.OUTPUT_LAYER: output}


    def prepareInputData(self, parameters, context, feedback):
        inputFaultFilename = self.parameterAsString(parameters, self.INPUT_FAULT, context)

        inputDatas = []
        #Data #1
        inputDataItem = {}
        inputDataItem['fileName'] = self.INPUT_LAYER
        inputDataItem['field'] = self.parameterAsString(parameters, self.INPUT_FIELD, context)
        inputDatas.append(inputDataItem)

        #Data #2
        inputFilename = self.parameterAsString(parameters, self.INPUT_LAYER1, context)
        input_field = self.parameterAsString(parameters, self.INPUT_FIELD1, context)
        if inputFilename and input_field:
            inputDataItem = {}
            inputDataItem['fileName'] = self.INPUT_LAYER1
            inputDataItem['field'] = input_field
            inputDatas.append(inputDataItem)

        # Data #3
        inputFilename = self.parameterAsString(parameters, self.INPUT_LAYER2, context)
        input_field = self.parameterAsString(parameters, self.INPUT_FIELD2, context)
        if inputFilename and input_field:
            inputDataItem = {}
            inputDataItem['fileName'] = self.INPUT_LAYER2
            inputDataItem['field'] = input_field
            inputDatas.append(inputDataItem)

        # Data #4
        inputFilename = self.parameterAsString(parameters, self.INPUT_LAYER3, context)
        input_field = self.parameterAsString(parameters, self.INPUT_FIELD3, context)
        if inputFilename and input_field:
            inputDataItem = {}
            inputDataItem['fileName'] = self.INPUT_LAYER3
            inputDataItem['field'] = input_field
            inputDatas.append(inputDataItem)

        with open(self.tempPointsFilename, "w") as text_file:
            for item in inputDatas:
                inputFilename = item['fileName']
                input_field = item['field']
                vectorLayer = self.parameterAsVectorLayer(parameters, inputFilename, context)
                features = vectorLayer.getFeatures()
                for f in features:
                    geom = f.geometry()
                    if geom:
                        if geom.wkbType() == QgsWkbTypes.Point:
                            pt = geom.asPoint()
                            val = f.attribute(input_field)
                            text_file.write("{0} {1} {2}\n".format(pt.x(), pt.y(), val))
                        elif geom.wkbType() == QgsWkbTypes.MultiPoint:
                            points = geom.asMultiPoint()
                            for pt in points:
                                val = f.attribute(input_field)
                                text_file.write("{0} {1} {2}\n".format(pt.x(), pt.y(), val))
                        elif geom.wkbType() == QgsWkbTypes.LineString:
                            points = geom.asPolyline()
                            for pt in points:
                                val = f.attribute(input_field)
                                text_file.write("{0} {1} {2}\n".format(pt.x(), pt.y(), val))

        vectorLayer = self.parameterAsVectorLayer(parameters, self.INPUT_FAULT, context)
        if not vectorLayer:
            return True

        #Create fault lines SHP
        provider = vectorLayer.dataProvider()

        self.faultFilename = getTempFilename('shp').replace("\\", "/")
        #self.temp_path.replace("\\", "/") + '/tempfaults.shp'
        settings = QSettings()
        systemEncoding = settings.value('/UI/encoding', 'System')
        fields = QgsFields()
        fields.append(QgsField('NAME', QVariant.String))
        writer = QgsVectorFileWriter(self.faultFilename, systemEncoding,
                              fields,
                              provider.wkbType(), provider.crs(), 'ESRI Shapefile')

        features = provider.getFeatures(QgsFeatureRequest(self.extent))
        num = 1
        for f in features:
            l = f.geometry()
            feat = QgsFeature()
            feat.setGeometry(l)
            feat.setAttributes(['fault{0}'.format(num)])
            num = num + 1
            writer.addFeature(feat)
        del writer

        return True


    def prepareJob(self, parameters, context):
        with open(self.tclFilename, "w") as text_file:
            # load plugins
            text_file.write("load libsurfit[info sharedlibextension]\n")
            text_file.write("load libsurfit_io[info sharedlibextension]\n")
            # remove all previous data and gridding rules
            text_file.write("clear_data\n")
            # set name of surface
            text_file.write('set map_name "map_faults"\n')
            # set solver
            text_file.write('set_solver "cg"\n')
            # set tolerance for solver
            text_file.write('set tol 1e-005\n')
            ##
            ## load initial data
            ##
            # load points from text file
            text_file.write('pnts_read "{0}" "points1"\n'.format(self.tempPointsFilename))

            if self.faultFilename:
                # load faults from Surfer BLN file
                text_file.write('curv_load_shp "{0}"\n'.format(self.faultFilename))

            ##
            ## construct grid
            ##

            expX = self.parameterAsDouble(parameters, self.EXPAND_PERCENT_X, context)
            expY = self.parameterAsDouble(parameters, self.EXPAND_PERCENT_Y, context)
            deltaX = self.extent.width() / 100.0 * expX
            deltaY = self.extent.height() / 100.0 * expY
            offX = self.stepX / 2.0
            offY = self.stepY / 2.0
            text_file.write("grid_get {0} {1} {2} {3} {4} {5}\n".format(self.extent.xMinimum()-deltaX/2 + offX,
                                                                self.extent.xMaximum()+deltaX/2 - offX,
                                                                self.stepX,
                                                                self.extent.yMinimum()-deltaY/2 + offY,
                                                                self.extent.yMaximum()+deltaY/2 - offY,
                                                                self.stepY))
            # text_file.write("grid 50 50\n")
            ##
            ## create gridding rules
            ##
            # resulting surface at points = points values
            text_file.write('points "points1"\n')

            if self.faultFilename:
                text_file.write('fault "fault*"\n')

            # resulting surface should tend to be constant or plane
            text_file.write("completer 1 5 \n")
            ##
            ## run gridding algorithm
            ##
            text_file.write("surfit \n")
            ##
            ## save results
            ##
            # save surface to Surfer-ASCII grid file
            text_file.write('surf_save_grd "{0}" $map_name \n'.format(self.grdFilename))


    def runSurfit(self, progress):
        runStr = os.path.join(self.plugin_dir, "bin/surfit ") + os.path.realpath(self.tclFilename)
        self.runProcess(runStr, progress)

    def runProcess(self, runStr, progress):
        process = QProcess(iface)
        process.start(runStr)
        process.waitForFinished()
        returnedstring = str(process.readAllStandardOutput())
        # print returnedstring
        progress.pushInfo(returnedstring)
        process.kill()

