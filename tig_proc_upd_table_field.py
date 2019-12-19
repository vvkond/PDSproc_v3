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
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingParameterFileDestination)

#===============================================================================
# 
#===============================================================================
class TigUpdateTableFieldAlgorithm(QgsProcessingAlgorithm):
    """
    All Processing algorithms should extend the GeoAlgorithm class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LAYER_TO="LAYER_TO"
    FIELD_JOIN_TO="FIELD_A"
    FIELD_1_TO="FIELD_A_1"
    FIELD_2_TO="FIELD_A_2"
    
    LAYER_FROM="LAYER_FROM"
    FIELD_JOIN_FROM="FIELD_B"
    FIELD_1_FROM="FIELD_B_1"
    FIELD_2_FROM="FIELD_B_2"

    IS_SKEEP_NONE="IS_SKEEP_NONE"
    ##_joinfield__to=optional field Layer_to_update
    ##_joinfield__from=optional field Layer_from_update

    #===========================================================================
    # 
    #===========================================================================
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def name(self):
        return 'TigUpdateTableFieldAlgorithm'

    def groupId(self):
        return 'PUMAtools'

    def group(self):
        return self.tr('Инструменты')

    def displayName(self):
        return self.tr(u'Обновление значений таблицы')

    def createInstance(self):
        return TigUpdateTableFieldAlgorithm()

    def initAlgorithm(self, config):
        #---------------LAYER A
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.LAYER_TO  #layer id
                , self.tr('Layer to update') #display text
                , [QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVectorLine] #layer types
                , ''
                , False #[is Optional?]
                ))
        
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_JOIN_TO #id
                , self.tr('Field for join layers in A(default well_id)') #display text
                , ''
                , self.LAYER_TO #field layer
                , QgsProcessingParameterField.Any
                , optional=True #[is Optional?]
                ))
        #---------------LAYER B
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.LAYER_FROM  #layer id
                , self.tr('Layer from update') #display text
                , [QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVectorLine] #layer types
                , ''
                , False #[is Optional?]
                ))
        
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_JOIN_FROM #id
                , self.tr('Field for join layers in B(default well_id)') #display text
                , ''
                , self.LAYER_FROM #field layer
                , QgsProcessingParameterField.Any
                , optional=True #[is Optional?]
                ))

        #---------------
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_1_TO #id
                , self.tr('Field to update 1') #display text
                , ''
                , self.LAYER_TO #field layer
                , QgsProcessingParameterField.Any
                , optional=False #[is Optional?]
                ))
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_1_FROM #id
                , self.tr('Field from update 1') #display text
                , ''
                , self.LAYER_FROM #field layer
                , QgsProcessingParameterField.Any
                , optional=False #[is Optional?]
                ))


        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_2_TO #id
                , self.tr('Field to update 2') #display text
                , ''
                , self.LAYER_TO #field layer
                , QgsProcessingParameterField.Any
                , optional=True #[is Optional?]
                ))
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_2_FROM #id
                , self.tr('Field from update 2') #display text
                , ''
                , self.LAYER_FROM #field layer
                , QgsProcessingParameterField.Any
                , optional=True #[is Optional?]
                ))
        
        #---------------
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.IS_SKEEP_NONE #id
                , self.tr('Skeep None values?') #display text
                , ''
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
        
        _copyfield_1_to       = self.parameterAsString(parameters, self.FIELD_1_TO, context)
        _copyfield_2_to       = self.parameterAsString(parameters, self.FIELD_2_TO, context)
        
        _copyfield_1_from     = self.parameterAsString(parameters, self.FIELD_1_FROM, context)
        _copyfield_2_from     = self.parameterAsString(parameters, self.FIELD_2_FROM, context)
        
        _is_skeep_none       = self.parameterAsBool(parameters, self.IS_SKEEP_NONE, context)
        
        _joinfield__from='well_id' if _joinfield__from is None else _joinfield__from
        _joinfield__to=  'well_id' if _joinfield__to   is None else _joinfield__to
        
        field_to_upd=[[_copyfield_1_from ,_copyfield_1_to ] ]
        prefix='upd_fld_'
        if _copyfield_2_to is None or _copyfield_2_from is None:
            progress.pushInfo('Update only 1 field')
        else:
            field_to_upd.append([_copyfield_2_from ,_copyfield_2_to ] )
            progress.pushInfo('Update 2 fields')
            
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
        joinObject.setUsingMemoryCache(True)
        joinObject.setPrefix(prefix)
        joinObject.setJoinFieldNamesSubset([i[0] for i in field_to_upd])
        Layer_to_update.addJoin(joinObject)
        #---copy filter expression
        progress.pushInfo('Backup <b>{}</b> subsetString'.format(Layer_to_update.id()))
        filter_exp=Layer_to_update.subsetString()
        Layer_to_update.setSubsetString('')
        #--- update geometry from field 'upd_coord_geometry'
        prov=Layer_to_update.dataProvider()
        Layer_to_update.startEditing()
        #e = QgsExpression( 'if( geom_from_wkt(  "upd_coord_geometry" )  IS  None, $geometry ,geom_from_wkt(  "upd_coord_geometry" ))' )

        cntx = context.expressionContext()
        cntx.setFields(Layer_to_update.fields())
        
        for _copyfield_from,_copyfield_to in field_to_upd:
            progress.pushInfo('Copy values: \n\t{}.{} \n\t-> \n\t{}.{}'.format(Layer_from_update.id(), _copyfield_from, Layer_to_update.id() ,_copyfield_to))
            e=None
            if _is_skeep_none:
                e = QgsExpression( 'if( "{prefix}{upd_from}" IS  None, "{upd_to}" ,"{prefix}{upd_from}")'.format( prefix=prefix
                                                                                                                  , upd_from=_copyfield_from
                                                                                                                  , upd_to=_copyfield_to 
                                                                                                                  ) ) #https://qgis.org/api/2.18/classQgsExpression.html
            else:
                e = QgsExpression( '"{prefix}{upd_from}"'.format( prefix=prefix
                                                                  , upd_from=_copyfield_from
                                                                  ) ) #https://qgis.org/api/2.18/classQgsExpression.html

            progress.pushInfo('\tExpression is: <b>{}</b>'.format(e.expression()))
            e.prepare( cntx )
            fldIdx = prov.fieldNameIndex(_copyfield_to)
            to_upd={}
            for feature in Layer_to_update.getFeatures():  #https://qgis.org/api/classQgsFeature.html
                cntx.setFeature(feature)
                val = e.evaluate(cntx)
                to_upd[feature.id()]={ fldIdx : val }
            prov.changeAttributeValues(to_upd)
                #Layer_to_update.changeAttributeValue(feature.id(),fldIdx,e.evaluate( feature ))     
                #Layer_to_update.dataProvider().changeGeometryValues({feature.id(): e.evaluate( feature )})  #https://qgis.org/api/2.18/classQgsVectorLayer.html
        #Layer_to_update.beginEditCommand("edit")
        #Layer_to_update.endEditCommand()
        progress.pushInfo('Commit changes')
        Layer_to_update.commitChanges()
        #--- restore filter expression
        progress.pushInfo('Restore subsetString to "{}"'.format(filter_exp))
        Layer_to_update.setSubsetString(filter_exp)
        #--- remove layers join
        progress.pushInfo('Remove join {}->{}'.format(Layer_to_update.id(),Layer_from_update.id()))
        Layer_to_update.removeJoin( Layer_from_update.id() )
        progress.pushInfo('<b>End</b>')

        return {}
        
                    
        