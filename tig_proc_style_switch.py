# -*- coding: utf-8 -*-


__author__ = 'Alex Russkikh'
__date__ = '2018-12-03'
__copyright__ = '(C) 2018 by Alex Russkikh'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import tempfile
import os

from qgis.PyQt.QtCore import QCoreApplication, QVariant
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
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterString)

#===============================================================================
# 
#===============================================================================
class TigSwitchLayerStyleAlgorithm(QgsProcessingAlgorithm):
    """
    All Processing algorithms should extend the GeoAlgorithm class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LAYER_TO="LAYER_TO"
    STYLE="PREFIX"
    
    ##_joinfield__to=optional field Layer_to_update
    ##_joinfield__from=optional field Layer_from_update

    #===========================================================================
    # 
    #===========================================================================
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def name(self):
        return 'TigSwitchLayerStyleAlgorithm'

    def groupId(self):
        return 'PUMAtools'

    def group(self):
        return self.tr('Инструменты')

    def displayName(self):
        return self.tr(u'Переключение стиля слоя')

    def createInstance(self):
        return TigSwitchLayerStyleAlgorithm()

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.LAYER_TO  #layer id
                , self.tr('Layer to update') #display text
                ))

        self.addParameter(
            QgsProcessingParameterString( #name='', description='', default=None, multiline=False,  optional=False, evaluateExpressions=False
                self.STYLE    #name
                , u'Стиль' #desc
                , 'default' #default
                , False # is big text?
                , True
                #, False #for 2.14
                ))   
         
        
    #===========================================================================
    # 
    #===========================================================================
    def processAlgorithm(self, parameters, context, progress):
        """Here is where the processing itself takes place."""
        progress.pushInfo('<b>Start</b>')
        
        
        progress.pushInfo('Read settings')
        # The first thing to do is retrieve the values of the parameters
        # entered by the user
        Layer_to_update      = self.parameterAsVectorLayer(parameters, self.LAYER_TO, context)
        _style               = self.parameterAsString(parameters, self.STYLE, context)
        #--- create virtual field with geometry
        progress.pushInfo('Try change style <b>{}</b> -> <b>{}</b>'.format(Layer_to_update,_style))
        LayerStyles=Layer_to_update.styleManager()
        LayerStyles.setCurrentStyle(_style)
        progress.pushInfo('<b>End</b>')

        return {}
            
                    
        