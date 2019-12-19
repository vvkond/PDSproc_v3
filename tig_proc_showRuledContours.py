# -*- coding: utf-8 -*-


__author__ = 'Alex Russkikh'
__date__ = '2019-02-12'
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
                       QgsExpressionContextUtils,
                       QgsProcessingParameterRange)


#===============================================================================
# 
#===============================================================================
class TigShowRuleLabelContours(QgsProcessingAlgorithm):
    """
    All Processing algorithms should extend the GeoAlgorithm class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LAYER_TO="LAYER_TO"
    VALUE_FIELD="VALUE_FIELD"
    LIMITS="LIMITS"
    STEP="STEP"
    SKEEP_EACH="SKEEP_EACH"
    
    PARAMS=[
        [STEP ,"Step for show contours"           ,True ,25    ]
        ,[SKEEP_EACH ,"Skeep each 'n' contours"   ,True  ,0    ]
        ]
    #===========================================================================
    # 
    #===========================================================================
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def name(self):
        return 'TigShowRuleLabelContours'

    def groupId(self):
        return 'PUMAtools'

    def group(self):
        return self.tr('Инструменты')

    def displayName(self):
        return self.tr(u'Отображение контуров с указанным шагом')

    def createInstance(self):
        return TigShowRuleLabelContours()

    def initAlgorithm(self, config):

        #---------------LAYER A
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.LAYER_TO  #layer id
                , self.tr('Layer with contours') #display text
                , [QgsProcessing.TypeVectorLine] #layer types
                , ''
                , False #[is Optional?]
                ))

        self.addParameter(
            QgsProcessingParameterField(
                self.VALUE_FIELD
                , self.tr('Field {} with contour value ').format(self.VALUE_FIELD) #display text
                , ''
                , self.LAYER_TO #field layer
                , QgsProcessingParameterField.Numeric
                , optional=False #[is Optional?]
                ))
        self.addParameter(
            QgsProcessingParameterRange(
                name=self.LIMITS
                , description=self.tr('Interval limits') #display text
                , defaultValue='-20000,20000'
                , optional=True
                )
            )
        
        for [param_id,desc,is_optional,param_default] in self.PARAMS:
            self.addParameter(
                QgsProcessingParameterNumber(
                    name=param_id 
                    , description= desc
                    , defaultValue=param_default
                    , optional=is_optional
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
        editLayer     = self.parameterAsVectorLayer(parameters, self.LAYER_TO, context)
        _value_field_= self.parameterAsDouble(parameters, self.VALUE_FIELD, context)
        _range_field_= self.parameterAsRange(parameters, self.LIMITS, context)
        _step_field_= self.parameterAsDouble(parameters, self.STEP, context)
        _skeep_field_= self.parameterAsDouble(parameters, self.SKEEP_EACH, context)

        #--- create virtual field with geometry
        # editLayer=dataobjects.getObject(Layer_to_update)      #processing.getObjectFromUri()
        layerCurrentStyleRendere=editLayer.renderer()
        if not type(layerCurrentStyleRendere)==QgsRuleBasedRenderer:
            editLayerStyles=editLayer.styleManager()
            editLayerStyles.addStyle( u'контуры', editLayerStyles.style(editLayerStyles.currentStyle() ))
            editLayerStyles.setCurrentStyle(u'контуры')

            progress.pushInfo('Change style rendered to rule based')
            renderer = QgsRuleBasedRenderer(QgsRuleBasedRenderer.Rule(None))
            superRootRule = renderer.rootRule() #super Root Rule
            editLayer.setRenderer(renderer)
        else:
            superRootRule=layerCurrentStyleRendere.rootRule() 
        #---------
        progress.pushInfo('Create rule')
        symbol = QgsLineSymbol.createSimple({
                                                    'name' :'0'
                                                 ,  'type': 'line'
                                                 #,  'class':'SimpleLine'
                                                 ,  'alpha':"1"
                                                 ,  'clip_to_extent':"1"
                                                })
        """
           <symbol alpha="1" clip_to_extent="1" type="line" name="0">
            <layer pass="0" class="SimpleLine" locked="0">
             <prop k="capstyle" v="square"/>
             <prop k="customdash" v="5;2"/>
             <prop k="customdash_map_unit_scale" v="0,0,0,0,0,0"/>
             <prop k="customdash_unit" v="MM"/>
             <prop k="draw_inside_polygon" v="0"/>
             <prop k="joinstyle" v="bevel"/>
             <prop k="line_color" v="34,139,34,255"/>
             <prop k="line_style" v="solid"/>
             <prop k="line_width" v="0.25"/>
             <prop k="line_width_unit" v="MM"/>
             <prop k="offset" v="0"/>
             <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
             <prop k="offset_unit" v="MM"/>
             <prop k="use_custom_dash" v="0"/>
             <prop k="width_map_unit_scale" v="0,0,0,0,0,0"/>
            </layer>
           </symbol>
        """        
        sub_rule = QgsRuleBasedRenderer.Rule(symbol)
        progress.pushInfo('Set rule label')
        sub_rule.setLabel(u'Контуры от {} до {} с шагом {} {}'.format(_range_field_[0]
                                                                                      ,_range_field_[1]
                                                                                      ,_step_field_
                                                                                      ,u'исключая каждый {}'.format(_skeep_field_) if _skeep_field_>0  else ''
                                                                                      ))
        progress.pushInfo('Set rule filter')
        sub_rule.setFilterExpression(u'isValueInIntervalWithSkeep({value}, {limit_min}, {limit_max}, {step}, {skeep_each})'.format(
            value=_value_field_
            ,limit_min=_range_field_[0]
            ,limit_max=_range_field_[1]
            ,step=_step_field_
            ,skeep_each=_skeep_field_
            )) 
        superRootRule.appendChild(sub_rule)
        progress.pushInfo('End')

        return {}
        
                    
                    
                    
                    
        