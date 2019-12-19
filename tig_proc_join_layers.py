# -*- coding: utf-8 -*-


__author__ = 'Alex Russkikh'
__date__ = '2018-12-03'
__copyright__ = '(C) 2018 by Alex Russkikh'

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
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterVectorLayer)

#===============================================================================
# 
#===============================================================================
class TigJoinLayersAlgorithm(QgsProcessingAlgorithm):
    """
    All Processing algorithms should extend the GeoAlgorithm class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LAYER_TO="LAYER_TO"
    FIELD_JOIN_TO="FIELD_A"
    
    LAYER_FROM="LAYER_FROM"
    FIELD_JOIN_FROM="FIELD_B"
    
    FIELDS_TO_JOIN="FIELDS_TO_JOIN"
    PREFIX="PREFIX"
    
    USE_CACHE="USE_CACHE"

    ##_joinfield__to=optional field Layer_to_update
    ##_joinfield__from=optional field Layer_from_update

    #===========================================================================
    # 
    #===========================================================================
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def name(self):
        return 'TigJoinLayersAlgorithm'

    def groupId(self):
        return 'PUMAtools'

    def group(self):
        return self.tr('Инструменты')

    def displayName(self):
        return self.tr(u'Создание связей')

    def createInstance(self):
        return TigJoinLayersAlgorithm()

    def initAlgorithm(self, config):

        #---------------LAYER A
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.LAYER_TO  #layer id
                , self.tr('Layer to update') #display text
                , [QgsProcessing.TypeVectorLine, QgsProcessing.TypeVectorPoint] #layer types
                , ''
                , False #[is Optional?]
                ))
        
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_JOIN_TO #id
                , self.tr('Field for join layers in A(default well_id)') #display text
                , 'well_id'
                , self.LAYER_TO #field layer
                , QgsProcessingParameterField.Any
                , optional=True #[is Optional?]
                ))

        #---------------LAYER B
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.LAYER_FROM  #layer id
                , self.tr('Layer from update') #display text
                , [QgsProcessing.TypeVectorLine, QgsProcessing.TypeVectorPoint] #layer types
                , ''
                , False #[is Optional?]
                ))
        
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_JOIN_FROM #id
                , self.tr('Field to for layers in B(default well_id)') #display text
                , 'well_id'
                , self.LAYER_FROM #field layer
                , QgsProcessingParameterField.Any
                , optional=True #[is Optional?]
                ))

        self.addParameter(
            QgsProcessingParameterField(
                self.FIELDS_TO_JOIN #id
                , self.tr('Fields to join') #display text
                , ''
                , self.LAYER_FROM #field layer
                , QgsProcessingParameterField.Any
                , True
                , False #[is Optional?]
                ))
        
        self.addParameter(
            QgsProcessingParameterString( #name='', description='', default=None, multiline=False,  optional=False, evaluateExpressions=False
                self.PREFIX    #name
                , u'Префикс' #desc
                , '_' #default
                , False # is big text?
                , False
                #, False #for 2.14
                ))   
        #---------------
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.USE_CACHE #id
                , self.tr('Save in cache?') #display text
                , True #default
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
        Layer_to_update     = self.parameterAsVectorLayer(parameters, self.LAYER_TO, context)
        Layer_from_update   = self.parameterAsVectorLayer(parameters, self.LAYER_FROM, context)
        
        _joinfield__to   = self.parameterAsString(parameters, self.FIELD_JOIN_TO, context)
        _joinfield__from = self.parameterAsString(parameters, self.FIELD_JOIN_FROM, context)
        
        _join_what_lst   = self.parameterAsFields(parameters, self.FIELDS_TO_JOIN, context)
        _prefix          = self.parameterAsString(parameters, self.PREFIX, context)
        
        _use_cache       = self.parameterAsBool(parameters, self.USE_CACHE, context)
        #--- create virtual field with geometry

        _joinfield__from='well_id' if _joinfield__from is None else _joinfield__from
        _joinfield__to=  'well_id' if _joinfield__to   is None else _joinfield__to
        progress.pushInfo('Fields: {},{}'.format(_joinfield__to, _joinfield__from))
        
        #Layer_from_update.startEditing()
        #cX = QgsField( '_x', QVariant.Double  )
        #cY = QgsField( '_y', QVariant.Double  )
        #cGeometry= QgsField( '_geometry', QVariant.String  )
        #--- VIRTUAL FIELD
        #Layer_from_update.addExpressionField( 'x(start_point($geometry))' , cX )
        #Layer_from_update.addExpressionField( 'y(start_point($geometry))' , cY )
        #Layer_from_update.addExpressionField( ' geom_to_wkt( $geometry )' , cGeometry )
        #Layer_from_update.commitChanges()
        
        #--- remove layers join
        progress.pushInfo('Try remove old join <b>{}</b> -> <b>{}</b>'.format(Layer_to_update.id(),Layer_from_update.id()))
        Layer_to_update.removeJoin( Layer_from_update.id() )
        #--- join layers. Join only virtual field  'upd_coord_geometry'
        progress.pushInfo('Join: \n\t{} \n\t-> \n\t{}'.format(Layer_to_update.id(),Layer_from_update.id()))
        joinObject = QgsVectorLayerJoinInfo()
        joinObject.setJoinLayer(Layer_from_update)
        joinObject.setJoinFieldName(_joinfield__from)
        joinObject.setTargetFieldName(_joinfield__to)
        joinObject.setUsingMemoryCache(_use_cache)
        joinObject.setPrefix(_prefix)
        joinObject.setJoinFieldNamesSubset(_join_what_lst)
        Layer_to_update.addJoin(joinObject)
        progress.pushInfo('<b>End</b>')

        return {}
                    
        