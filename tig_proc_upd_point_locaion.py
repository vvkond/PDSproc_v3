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
                       QgsProcessingParameterFileDestination)


class TigUpdatePointLocationAlgorithm(QgsProcessingAlgorithm):
    LAYER_A="LAYER_A"
    FIELD_TO_JOIN_A="FIELD_A"
    LAYER_B="LAYER_B"
    FIELD_TO_JOIN_B="FIELD_B"

##Field_for_join_to=optional field Layer_to_update
##Field_for_join_from=optional field Layer_from_update

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def name(self):
        return 'TigUpdatePointLocationAlgorithm'

    def groupId(self):
        return 'PUMAtools'

    def group(self):
        return self.tr('Инструменты')

    def displayName(self):
        return self.tr(u'Обновление расположения скважин')

    def createInstance(self):
        return TigUpdatePointLocationAlgorithm()

    def initAlgorithm(self, config):
        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.LAYER_A  #layer id
                , self.tr('Layer to update') #display text
                , [QgsProcessing.TypeVectorPoint] #layer types
                , ''
                , False #[is Optional?]
                ))
        
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_TO_JOIN_A #id
                , self.tr('Field for join layers in A(default well_id)') #display text
                , 'well_id'
                , self.LAYER_A #field layer
                , QgsProcessingParameterField.Any
                , optional=True #[is Optional?]
                ))

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.LAYER_B  #layer id
                , self.tr('Layer from update') #display text
                , [QgsProcessing.TypeVectorPoint] #layer types
                , ''
                , False #[is Optional?]
                ))
        
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_TO_JOIN_B #id
                , self.tr('Field to for layers in B(default well_id)') #display text
                , 'well_id'
                , self.LAYER_B #field layer
                , QgsProcessingParameterField.Any
                , optional=True #[is Optional?]
                ))

    def processAlgorithm(self, parameters, context, feedback):
        """Here is where the processing itself takes place."""

        # The first thing to do is retrieve the values of the parameters
        # entered by the user
        Layer_to_update = self.parameterAsVectorLayer(parameters, self.LAYER_A, context)
        Layer_from_update = self.parameterAsVectorLayer(parameters, self.LAYER_B, context)
        Field_for_join_to = self.parameterAsString(parameters, self.FIELD_TO_JOIN_A, context)
        Field_for_join_from = self.parameterAsString(parameters, self.FIELD_TO_JOIN_B, context)

        Field_for_join_from='well_id' if Field_for_join_from is None else Field_for_join_from
        Field_for_join_to='well_id' if Field_for_join_to is None else Field_for_join_to
        #Layer_from_update.startEditing()
        #cX = QgsField( '_x', QVariant.Double  )
        #cY = QgsField( '_y', QVariant.Double  )
        cGeometry= QgsField( '_geometry', QVariant.String  )
        #--- VIRTUAL FIELD
        #Layer_from_update.addExpressionField( 'x(start_point($geometry))' , cX )
        #Layer_from_update.addExpressionField( 'y(start_point($geometry))' , cY )
        Layer_from_update.addExpressionField( ' geom_to_wkt( $geometry )' , cGeometry )
        #Layer_from_update.commitChanges()
        
        #--- remove layers join
        Layer_to_update.removeJoin( Layer_from_update.id() )
        #--- join layers. Join only virtual field  'upd_coord_geometry'
        joinObject = QgsVectorLayerJoinInfo()
        joinObject.setJoinLayer( Layer_from_update)
        joinObject.setJoinFieldName(Field_for_join_from)
        joinObject.setTargetFieldName(Field_for_join_to)
        joinObject.setUsingMemoryCache(True)
        joinObject.setPrefix('upd_coord')
        joinObject.setJoinFieldNamesSubset(['_geometry'])
        Layer_to_update.addJoin(joinObject)
        #---copy filter expression
        filter_exp=Layer_to_update.subsetString()
        Layer_to_update.setSubsetString('')
        #--- update geometry from field 'upd_coord_geometry'

        cntx = context.expressionContext()
        cntx.setFields( Layer_to_update.fields())

        Layer_to_update.startEditing()
        e = QgsExpression( 'if( geom_from_wkt(  "upd_coord_geometry" )  IS  None, $geometry ,geom_from_wkt(  "upd_coord_geometry" ))' )
        e.prepare(cntx)
        for feature in Layer_to_update.getFeatures():
            cntx.setFeature(feature)
            val = e.evaluate(cntx)
            Layer_to_update.dataProvider().changeGeometryValues({feature.id(): val})
        Layer_to_update.beginEditCommand("edit")
        Layer_to_update.endEditCommand()
        Layer_to_update.commitChanges()
        #--- restore filter expression
        Layer_to_update.setSubsetString(filter_exp)
        #--- remove layers join
        # Layer_to_update.removeJoin( Layer_from_update.id() )

        return {}
        
    @staticmethod
    def script():
        return """
##Layer_to_update=vector point
##Field_for_join_to=optional field Layer_to_update
##Layer_from_update=vector point
##Field_for_join_from=optional field Layer_from_update
##General Tools=group
##Move point =name

from qgis.core import *
from PyQt4.QtCore import QVariant

#--- create virtual field with geometry
Layer_from_update=processing.getObject(Layer_from_update)
Layer_to_update=processing.getObject(Layer_to_update)

Field_for_join_from='well_id' if Field_for_join_from is None else Field_for_join_from
Field_for_join_to='well_id' if Field_for_join_to is None else Field_for_join_to
#Layer_from_update.startEditing()
#cX = QgsField( '_x', QVariant.Double  )
#cY = QgsField( '_y', QVariant.Double  )
cGeometry= QgsField( '_geometry', QVariant.String  )
#--- VIRTUAL FIELD
#Layer_from_update.addExpressionField( 'x(start_point($geometry))' , cX )
#Layer_from_update.addExpressionField( 'y(start_point($geometry))' , cY )
Layer_from_update.addExpressionField( ' geom_to_wkt( $geometry )' , cGeometry )
#Layer_from_update.commitChanges()

#--- remove layers join
Layer_to_update.removeJoin( Layer_from_update.id() )
#--- join layers. Join only virtual field  'upd_coord_geometry'
joinObject = QgsVectorJoinInfo()
joinObject.joinLayerId = Layer_from_update.id()
joinObject.joinFieldName = Field_for_join_from
joinObject.targetFieldName = Field_for_join_to
joinObject.memoryCache = True
joinObject.prefix='upd_coord'
joinObject.setJoinFieldNamesSubset(['_geometry'])
Layer_to_update.addJoin(joinObject)
#---copy filter expression
filter_exp=Layer_to_update.subsetString()
Layer_to_update.setSubsetString('')
#--- update geometry from field 'upd_coord_geometry'
Layer_to_update.startEditing()
e = QgsExpression( 'if( geom_from_wkt(  "upd_coord_geometry" )  IS  None, $geometry ,geom_from_wkt(  "upd_coord_geometry" ))' )
e.prepare( Layer_to_update.fields() )
for feature in Layer_to_update.getFeatures():
    Layer_to_update.dataProvider().changeGeometryValues({feature.id(): e.evaluate( feature )})
Layer_to_update.beginEditCommand("edit")
Layer_to_update.endEditCommand()
Layer_to_update.commitChanges()
#--- restore filter expression
Layer_to_update.setSubsetString(filter_exp)
#--- remove layers join
Layer_to_update.removeJoin( Layer_from_update.id() )

"""
        