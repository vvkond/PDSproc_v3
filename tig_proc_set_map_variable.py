# -*- coding: utf-8 -*-


__author__ = 'Alex Russkikh'
__date__ = '2018-12-03'
__copyright__ = '(C) 2018 by Alex Russkikh'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import tempfile
import os

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.utils import iface
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
                       QgsProcessingParameterString,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingParameterFileDestination,
                       QgsExpressionContextUtils)

#===============================================================================
# 
#===============================================================================
class TigSetMapVariable(QgsProcessingAlgorithm):
    """

    @var var:
        00    str: PROP_1    
        01    str: __doc__    
        02    str: __init__    
        03    str: __module__    
        04    str: __str__    
        05    str: _checkParameterValuesBeforeExecuting    
        06    str: _formatHelp    
        07    str: _icon    
        08    str: addOutput    
        09    str: addParameter    
        10    str: allowOnlyOpenedLayers    
        11    str: canRunInBatchMode    
        12    str: checkBeforeOpeningParametersDialog    
        13    str: checkInputCRS    
        14    str: checkOutputFileExtensions    
        15    str: checkParameterValuesBeforeExecuting    
        16    str: commandLineName    
        17    str: convertUnsupportedFormats    
        18    str: crs    
        19    str: defineCharacteristics    
        20    str: displayName    
        21    str: displayNames    
        22    str: execute    
        23    str: getAsCommand    
        24    str: getCopy    
        25    str: getCustomModelerParametersDialog    
        26    str: getCustomParametersDialog    
        27    str: getDefaultIcon    
        28    str: getFormatShortNameFromFilename    
        29    str: getHTMLOutputsCount    
        30    str: getIcon    
        31    str: getOutputFromName    
        32    str: getOutputValue    
        33    str: getOutputValuesAsDictionary    
        34    str: getParameterDescriptions    
        35    str: getParameterFromName    
        36    str: getParameterValue    
        37    str: getVisibleOutputsCount    
        38    str: getVisibleParametersCount    
        39    str: group    
        40    str: help    
        41    str: i18n_group    
        42    str: i18n_name    
        43    str: model    
        44    str: name    
        45    str: outputs    
        46    str: parameters    
        47    str: processAlgorithm    
        48    str: provider    
        49    str: removeOutputFromName    
        50    str: resolveDataObjects    
        51    str: resolveTemporaryOutputs    
        52    str: runHookScript    
        53    str: runPostExecutionScript    
        54    str: runPreExecutionScript    
        55    str: setOutputCRS    
        56    str: setOutputValue    
        57    str: setParameterValue    
        58    str: shortHelp    
        59    str: showInModeler    
        60    str: showInToolbox    
        61    str: tr    
        62    str: trAlgorithm    
    
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    PROPS=[
        ["company_name",u'Имя компании',    u'', 'String']
        ,["project"    ,u'Имя проекта',     u'', 'String']
        ,["map_date"   ,u'Дата для штампа', u'', 'String']
        ,["emblem"     ,u'Файл с эмблемой', u'', 'File']
        ]

    #QgsExpressionContextUtils.projectScope().variable(PROP_1)
    #QgsExpressionContextUtils.setProjectVariable(PROP_1,self.getParameterValue(self.PROP_1)) 
    #===========================================================================
    # 
    #===========================================================================
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def name(self):
        return 'TigSetMapVariable'

    def groupId(self):
        return 'PUMAtools'

    def group(self):
        return self.tr('Инструменты')

    def displayName(self):
        return self.tr(u'Задание переменных карты')

    def createInstance(self):
        return TigSetMapVariable()

    def initAlgorithm(self, config):
        for [name,desc,default,paramtype] in self.PROPS:
            try:
                defaultValue = QgsExpressionContextUtils.projectScope(QgsProject.instance()).variable(name)
            except:
                defaultValue = default
            if paramtype=='String':

                self.addParameter(
                    QgsProcessingParameterString( #name='', description='', default=None, multiline=False,  optional=False, evaluateExpressions=False
                        name
                        , desc
                        , defaultValue
                        , False # is big text?
                        , False
                        #, False #for 2.14
                        ))
            elif paramtype=='File':
                self.addParameter(
                    QgsProcessingParameterFile(
                        name=name
                        , description=desc
                        , defaultValue=defaultValue
                        , optional=True
                        ))
            else:
                raise Exception('Unknown type parameter')


    #===========================================================================
    # 
    #===========================================================================
    def processAlgorithm(self, parameters, context, feedback):
        """Here is where the processing itself takes place."""
        for [name,desc,default,paramtype] in self.PROPS:
            QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), name,
                                                         self.parameterAsString(parameters, name, context))
        return {}
  
        
  
        