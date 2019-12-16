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
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingParameterFileDestination)

#===============================================================================
# 
#===============================================================================
class TigSetPdsCustomProp(QgsProcessingAlgorithm):
    PROPS=[
         ["qgis_pds_type"]
        ,["pds_prod_SelectedReservoirs"]
        ,["pds_prod_PhaseFilter"]
        ]
    
    #self.layer.setCustomProperty("qgis_pds_type", "pds_fond")
    #layer.customProperty("qgis_pds_type") 
    #===========================================================================
    # 
    #===========================================================================
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def name(self):
        return 'TigSetPdsCustomProp'

    def groupId(self):
        return 'PUMAtools'

    def group(self):
        return self.tr('Инструменты')

    def displayName(self):
        return self.tr(u'Задание свойств pds у выбранных слоев')

    def createInstance(self):
        return TigSetPdsCustomProp()

    def initAlgorithm(self, config):
        self.parameters = []
        self.param_info = {}

        layers = iface.layerTreeView().selectedLayers()
        for layer in layers:
            for [prop_name] in self.PROPS:
                self.addParameter(
                    QgsProcessingParameterString(
                        layer.id() + u"/" + prop_name  # name
                        , layer.name() + u" / " + prop_name  # desc
                        , layer.customProperty(prop_name)  # def
                        , False  # mline
                        , True  # opt
                        # , False #for 2.14
                    ))
                self.param_info[layer.id() + u"/" + prop_name] = [layer, prop_name]

    #===================================================================
    # 
    #===================================================================
    def checkBeforeOpeningParametersDialog1(self):
        # self.parameters[0]
        # ESCAPED_NEWLINE', 'NEWLINE', '__doc__', '__init__', '__module__', '__str__', 'default', 'description'
        #'evaluateExpressions', 'getAsScriptCode', 'getValueAsCommandLineParameter', 'hidden', 'isAdvanced', 'multiline', 'name', 'optional', 'setDefaultValue', 'setValue', 'todict', 'tr', 'typeName', 'value'
        #param.setValue(QgsExpressionContextUtils.projectScope().variable(self.PROP_1))
        self.parameters=[]
        self.param_info={}
        layers= iface.legendInterface().selectedLayers()
        for layer in layers:
            for [prop_name] in self.PROPS:
                self.addParameter(
                    ParameterString(  #name='', description='', default=None, multiline=False,  optional=False, evaluateExpressions=False
                        layer.id()+u"/"+prop_name #name 
                        , layer.name()+u" / "+prop_name #desc
                        , layer.customProperty(prop_name) #def
                        , False #mline
                        , True  #opt
                        #, False #for 2.14
                        ))
                self.param_info[layer.id()+u"/"+prop_name]=[layer,prop_name]
    #===========================================================================
    # 
    #===========================================================================
    def processAlgorithm(self, parameters, context, feedback):
        """Here is where the processing itself takes place."""
        for param_id,[Layer_to_update,prop_name] in self.param_info.items():
            Layer_to_update.setCustomProperty(prop_name, self.parameterAsString(parameters, param_id, context))

        return {}
  
        
  
        