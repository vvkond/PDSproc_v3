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
                       QgsProcessingParameterString,
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingParameterFileDestination)


#===============================================================================
# 
#===============================================================================
class TigSetCustomProp(QgsProcessingAlgorithm):
    LAYER_A="LAYER_A"
    PROP_NAME="PROPERTY"
    PROP_VALUE="VALUE"

    #self.layer.setCustomProperty("qgis_pds_type", "pds_fond")
    #layer.customProperty("qgis_pds_type") 
    #===========================================================================
    # 
    #===========================================================================
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def name(self):
        return 'TigSetCustomProp'

    def groupId(self):
        return 'PUMAtools'

    def group(self):
        return self.tr('Инструменты')

    def displayName(self):
        return self.tr(u'Задание свойств слоя')

    def createInstance(self):
        return TigSetCustomProp()

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.LAYER_A  #layer id
                , self.tr('Layer to update') #display text
                , [QgsProcessing.TypeVectorPoint] #layer types
                , ''
                , False #[is Optional?]
                ))

        self.addParameter(
            QgsProcessingParameterString(
                self.PROP_NAME    #name
                , self.tr('Имя свойства') #desc
                , 'qgis_pds_type/pds_prod_SelectedReservoirs/pds_prod_PhaseFilter/..' #default
                , False # multiLine?
                , False
                #, False #for 2.14
                ))    
        self.addParameter(
            QgsProcessingParameterString(
                self.PROP_VALUE
                , self.tr('Значение свойства')
                , 'pds_cumulative_production'
                , False 
                , False
                ))

    #===========================================================================
    # 
    #===========================================================================
    def processAlgorithm(self, parameters, context, feedback):
        """Here is where the processing itself takes place."""
        Layer_to_update = self.parameterAsVectorLayer(parameters, self.LAYER_A, context)
        Layer_to_update.setCustomProperty(self.parameterAsString(parameters, self.PROP_NAME, context),
                                          self.parameterAsString(parameters, self.PROP_VALUE, context))

        return {}
  
        
  
        