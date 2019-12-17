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
class TigUpdateLabelLocationAlgorithm(QgsProcessingAlgorithm):
    """
    All Processing algorithms should extend the GeoAlgorithm class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LAYER_TO="LAYER_TO"
    FIELD_JOIN_TO="FIELD_A"
    FIELD_LBLX_TO="FIELD_A_X"
    FIELD_LBLY_TO="FIELD_A_Y"
    FIELD_LBLXOFF_TO="FIELD_A_XOFF"
    FIELD_LBLYOFF_TO="FIELD_A_YOFF"
    FIELD_LBLOFF_TO="FIELD_A_OFF"
    
    LAYER_FROM="LAYER_FROM"
    FIELD_JOIN_FROM="FIELD_B"
    FIELD_LBLX_FROM="FIELD_B_X"
    FIELD_LBLY_FROM="FIELD_B_Y"
    FIELD_LBLXOFF_FROM="FIELD_B_XOFF"
    FIELD_LBLYOFF_FROM="FIELD_B_YOFF"
    FIELD_LBLOFF_FROM="FIELD_B_OFF"
    
    IS_REMOVE_JOIN="IS_REMOVE_JOIN"

    ##_joinfield__to=optional field Layer_to_update
    ##_joinfield__from=optional field Layer_from_update

    #===========================================================================
    # 
    #===========================================================================
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def name(self):
        return 'TigUpdateLabelLocationAlgorithm'

    def groupId(self):
        return 'PUMAtools'

    def group(self):
        return self.tr('Инструменты')

    def displayName(self):
        return self.tr(u'Обновление расположения подписей')

    def createInstance(self):
        return TigUpdateLabelLocationAlgorithm()

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
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_LBLX_TO #id
                , self.tr('Field with label x position(default lablx)') #display text
                , ''
                , self.LAYER_TO #field layer
                , QgsProcessingParameterField.Any
                , optional=True #[is Optional?]
                ))
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_LBLY_TO #id
                , self.tr('Field with label y position(default lably)') #display text
                , ''
                , self.LAYER_TO #field layer
                , QgsProcessingParameterField.Any
                , optional=True #[is Optional?]
                ))
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_LBLXOFF_TO #id
                , self.tr('Field with label x offset position(default labloffx)') #display text
                , ''
                , self.LAYER_TO #field layer
                , QgsProcessingParameterField.Any
                , optional=True #[is Optional?]
                ))
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_LBLYOFF_TO #id
                , self.tr('Field with label y offset position(default labloffy)') #display text
                , ''
                , self.LAYER_TO #field layer
                , QgsProcessingParameterField.Any
                , optional=True #[is Optional?]
                ))
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_LBLOFF_TO #id
                , self.tr('Field with enable/disable offset offset position(default labloffset)') #display text
                , ''
                , self.LAYER_TO #field layer
                , QgsProcessingParameterField.Any
                , optional=True #[is Optional?]
                ))

        #---------------
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.IS_REMOVE_JOIN #id
                , self.tr('Remove join after algorithm?') #display text
                , ''
                , True #default
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
                , self.tr('Field to for layers in B(default well_id)') #display text
                , ''
                , self.LAYER_FROM #field layer
                , QgsProcessingParameterField.Any
                , optional=True #[is Optional?]
                ))

        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_LBLX_FROM #id
                , self.tr('Field with label x position(default lablx)') #display text
                , ''
                , self.LAYER_FROM #field layer
                , QgsProcessingParameterField.Any
                , optional=True #[is Optional?]
                ))
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_LBLY_FROM #id
                , self.tr('Field with label y position(default lably)') #display text
                , ''
                , self.LAYER_FROM #field layer
                , QgsProcessingParameterField.Any
                , optional=True #[is Optional?]
                ))
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_LBLXOFF_FROM #id
                , self.tr('Field with label x offset position(default labloffx)') #display text
                , ''
                , self.LAYER_FROM #field layer
                , QgsProcessingParameterField.Any
                , optional=True #[is Optional?]
                ))
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_LBLYOFF_FROM #id
                , self.tr('Field with label y offset position(default labloffy)') #display text
                , ''
                , self.LAYER_FROM #field layer
                , QgsProcessingParameterField.Any
                , optional=True #[is Optional?]
                ))
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_LBLOFF_FROM #id
                , self.tr('Field with enable/disable offset offset position(default labloffset)') #display text
                , ''
                , self.LAYER_FROM #field layer
                , QgsProcessingParameterField.Any
                , optional=True #[is Optional?]
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
        
        _copyfield_lblx_to       = self.parameterAsString(parameters, self.FIELD_LBLX_TO, context)
        _copyfield_lbly_to       = self.parameterAsString(parameters, self.FIELD_LBLY_TO, context)
        _copyfield_lblxoff_to    = self.parameterAsString(parameters, self.FIELD_LBLXOFF_TO, context)
        _copyfield_lblyoff_to    = self.parameterAsString(parameters, self.FIELD_LBLYOFF_TO, context)
        _copyfield_lbloff_to     = self.parameterAsString(parameters, self.FIELD_LBLOFF_TO, context)
        
        _copyfield_lblx_from     = self.parameterAsString(parameters, self.FIELD_LBLX_FROM, context)
        _copyfield_lbly_from     = self.parameterAsString(parameters, self.FIELD_LBLY_FROM, context)
        _copyfield_lblxoff_from  = self.parameterAsString(parameters, self.FIELD_LBLXOFF_FROM, context)
        _copyfield_lblyoff_from  = self.parameterAsString(parameters, self.FIELD_LBLYOFF_FROM, context)
        _copyfield_lbloff_from   = self.parameterAsString(parameters, self.FIELD_LBLOFF_FROM, context)
        
        _is_remove_join          = self.parameterAsBool(parameters, self.IS_REMOVE_JOIN, context)

        _joinfield__from='well_id' if _joinfield__from is None else _joinfield__from
        _joinfield__to=  'well_id' if _joinfield__to   is None else _joinfield__to
        
        _copyfield_lblx_to       ='lablx'      if _copyfield_lblx_to      is None else _copyfield_lblx_to     
        _copyfield_lbly_to       ='lably'      if _copyfield_lbly_to      is None else _copyfield_lbly_to     
        _copyfield_lblxoff_to    ='labloffx'   if _copyfield_lblxoff_to   is None else _copyfield_lblxoff_to  
        _copyfield_lblyoff_to    ='labloffy'   if _copyfield_lblyoff_to   is None else _copyfield_lblyoff_to
        _copyfield_lbloff_to     ='labloffset' if _copyfield_lbloff_to    is None else _copyfield_lbloff_to
          
        _copyfield_lblx_from     ='lablx'      if _copyfield_lblx_from    is None else _copyfield_lblx_from   
        _copyfield_lbly_from     ='lably'      if _copyfield_lbly_from    is None else _copyfield_lbly_from   
        _copyfield_lblxoff_from  ='labloffx'   if _copyfield_lblxoff_from is None else _copyfield_lblxoff_from
        _copyfield_lblyoff_from  ='labloffy'   if _copyfield_lblyoff_from is None else _copyfield_lblyoff_from
        _copyfield_lbloff_from   ='labloffset' if _copyfield_lbloff_from  is None else _copyfield_lbloff_from
                  
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
        joinObject.joinLayerId = Layer_from_update.id()
        joinObject.joinFieldName = _joinfield__from
        joinObject.targetFieldName = _joinfield__to
        joinObject.memoryCache = True
        joinObject.prefix='upd_lbl_'
        joinObject.setJoinFieldNamesSubset([
                                            _copyfield_lblx_from
                                            ,_copyfield_lbly_from
                                            ,_copyfield_lblxoff_from
                                            ,_copyfield_lblyoff_from
                                            ,_copyfield_lbloff_from
                                            ])
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
        
        for _copyfield_from,_copyfield_to in [
                                    [_copyfield_lblx_from,    _copyfield_lblx_to]
                                    ,[_copyfield_lbly_from,   _copyfield_lbly_to]
                                    ,[_copyfield_lblxoff_from,_copyfield_lblxoff_to]
                                    ,[_copyfield_lblyoff_from,_copyfield_lblyoff_to]
                                    ,[_copyfield_lbloff_from ,_copyfield_lbloff_to ]
                                    ]:
            progress.pushInfo('Copy not None values: \n\t{}.{} \n\t-> \n\t{}.{}'.format(Layer_from_update.id(), _copyfield_from, Layer_to_update.id() ,_copyfield_to))
            
            e = QgsExpression( 'if( "upd_lbl_{upd_from}" IS  None, "{upd_to}" ,"upd_lbl_{upd_from}")'.format( upd_from=_copyfield_from, upd_to=_copyfield_to ) ) #https://qgis.org/api/2.18/classQgsExpression.html
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
        #--- remove layers join
        if _is_remove_join:
            progress.pushInfo('Remove join {}->{}'.format(Layer_to_update.id(),Layer_from_update.id()))
            Layer_to_update.removeJoin( Layer_from_update.id() )
        #--- restore filter expression
        progress.pushInfo('Restore subsetString to "{}"'.format(filter_exp))
        Layer_to_update.setSubsetString(filter_exp)
        
        progress.pushInfo('<b>End</b>')

        return {}
                    
        