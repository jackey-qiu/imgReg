# -*- coding: utf-8 -*-
import os


import math
import numpy as np
from pyqtgraph.Point import Point
from pyqtgraph.graphicsItems.ItemGroup import ItemGroup
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
from pyqtgraph.graphicsItems.ViewBox.ViewBoxMenu import ViewBoxMenu
import weakref

import field_area_tool

__all__ = ['ViewBox']


class WeakList(object):

    def __init__(self):
        self._items = []

    def append(self, obj):
        #Add backwards to iterate backwards (to make iterating more efficient on removal).
        self._items.insert(0, weakref.ref(obj))

    def __iter__(self):
        i = len(self._items)-1
        while i >= 0:
            ref = self._items[i]
            d = ref()
            if d is None:
                del self._items[i]
            else:
                yield d
            i -= 1

class ChildGroup(ItemGroup):

    def __init__(self, parent):
        ItemGroup.__init__(self, parent)

        # Used as callback to inform ViewBox when items are added/removed from
        # the group.
        # Note 1: We would prefer to override itemChange directly on the
        #         ViewBox, but this causes crashes on PySide.
        # Note 2: We might also like to use a signal rather than this callback
        #         mechanism, but this causes a different PySide crash.
        self.itemsChangedListeners = WeakList()

        # exempt from telling view when transform changes
        self._GraphicsObject__inform_view_on_change = False

    def itemChange(self, change, value):
        ret = ItemGroup.itemChange(self, change, value)
        if change in [
            self.GraphicsItemChange.ItemChildAddedChange,
            self.GraphicsItemChange.ItemChildRemovedChange,
        ]:
            try:
                itemsChangedListeners = self.itemsChangedListeners
            except AttributeError:
                # It's possible that the attribute was already collected when the itemChange happened
                # (if it was triggered during the gc of the object).
                pass
            else:
                for listener in itemsChangedListeners:
                    listener.itemsChanged()
        return ret



class FieldViewBox(pg.ViewBox):
    """
    **Bases:** :class:`GraphicsWidget <pyqtgraph.GraphicsWidget>`
    Box that allows internal scaling/panning of children by mouse drag. 
    This class is usually created automatically as part of a :class:`PlotItem <pyqtgraph.PlotItem>` or
     :class:`Canvas <pyqtgraph.canvas.Canvas>` or with :func:`GraphicsLayout.addViewBox()
      <pyqtgraph.GraphicsLayout.addViewBox>`.
    Features:
    
    * Scaling contents by mouse or auto-scale when contents change
    * View linking--multiple views display the same data ranges
    * Configurable by context menu
    * Item coordinate mapping methods
    
    """
    
    sigYRangeChanged = QtCore.Signal(object, object)
    sigXRangeChanged = QtCore.Signal(object, object)
    sigRangeChangedManually = QtCore.Signal(object)
    sigRangeChanged = QtCore.Signal(object, object)
    #sigActionPositionChanged = QtCore.Signal(object)
    sigStateChanged = QtCore.Signal(object)
    sigTransformChanged = QtCore.Signal(object)
    sigResized = QtCore.Signal(object)
    pathExtractionClicked = QtCore.Signal(object, object)
    distanceMeasuredMoved_sig = QtCore.Signal(float,float,float)
    distanceMeasuredClicked_sig = QtCore.Signal(float,float,float)
    rectangleSelected_sig = QtCore.Signal(float,float,float,float)
    fiducialMarkerAdded_sig = QtCore.Signal(object)
    ## mouse modes
    PanMode = 3
    RectMode = 1
    
    ## axes
    XAxis = 0
    YAxis = 1
    XYAxes = 2

    ## for linking views together
    NamedViews = weakref.WeakValueDictionary()   # name: ViewBox
    AllViews = weakref.WeakKeyDictionary()       # ViewBox: None

    stagePositionTarget_sig = QtCore.Signal(float,float)
    stageMoveUpdate_sig = QtCore.Signal(float, float)
    def __init__(self, parent=None, border=None, lockAspect=False, enableMouse=True,
      invertY=False, enableMenu=True, name=None, invertX=False, defaultPadding=0.02,
      defaultSpotValue=[10,10],defaultSpotInterspacingValue=[10,10],_parent=None):
        """
        ==============  =============================================================
        **Arguments:**
        *parent*        (QGraphicsWidget) Optional parent widget
        *border*        (QPen) Do draw a border around the view, give any
                        single argument accepted by :func:`mkPen <pyqtgraph.mkPen>`
        *lockAspect*    (False or float) The aspect ratio to lock the view
                        coorinates to. (or False to allow the ratio to change)
        *enableMouse*   (bool) Whether mouse can be used to scale/pan the view
        *invertY*       (bool) See :func:`invertY <pyqtgraph.ViewBox.invertY>`
        *invertX*       (bool) See :func:`invertX <pyqtgraph.ViewBox.invertX>`
        *enableMenu*    (bool) Whether to display a context menu when 
                        right-clicking on the ViewBox background.
        *name*          (str) Used to register this ViewBox so that it appears
                        in the "Link axis" dropdown inside other ViewBox
                        context menus. This allows the user to manually link
                        the axes of any other view to this one. 
        ==============  =============================================================
        """
        pg.GraphicsWidget.__init__(self, parent)
        self.name = None
        self._parent = _parent
        self.linksBlocked = False
        self.addedItems = []
        #self.gView = view
        #self.showGrid = showGrid
        self._matrixNeedsUpdate = True  ## indicates that range has changed, but matrix update was deferred
        self._autoRangeNeedsUpdate = True ## indicates auto-range needs to be recomputed.

        self._lastScene = None  ## stores reference to the last known scene this view was a part of.
        
        self.state = {

            ## separating targetRange and viewRange allows the view to be resized
            ## while keeping all previously viewed contents visible
            'targetRange': [[0,1], [0,1]],   ## child coord. range visible [[xmin, xmax], [ymin, ymax]]
            'viewRange': [[0,1], [0,1]],     ## actual range viewed

            'yInverted': invertY,
            'xInverted': invertX,
            'aspectLocked': False,    ## False if aspect is unlocked, otherwise float specifies the locked ratio.
            'autoRange': [True, True],  ## False if auto range is disabled,
                                        ## otherwise float gives the fraction of data that is visible
            'autoPan': [False, False],         ## whether to only pan (do not change scaling) when auto-range is enabled
            'autoVisibleOnly': [False, False], ## whether to auto-range only to the visible portion of a plot
            'linkedViews': [None, None],  ## may be None, "viewName", or weakref.ref(view)
                                          ## a name string indicates that the view *should* link to another, but no view with that name exists yet.
            'defaultPadding': defaultPadding,

            'mouseEnabled': [enableMouse, enableMouse],
            'mouseMode': pg.ViewBox.PanMode if pg.getConfigOption('leftButtonPan') else pg.ViewBox.RectMode,
            'enableMenu': enableMenu,
            'wheelScaleFactor': -1.0 / 8.0,

            'background': None,

            # Limits
            'limits': {
                'xLimits': [None, None],   # Maximum and minimum visible X values
                'yLimits': [None, None],   # Maximum and minimum visible Y values
                'xRange': [None, None],   # Maximum and minimum X range
                'yRange': [None, None],   # Maximum and minimum Y range
                }

        }
        self._updatingRange = False  ## Used to break recursive loops. See updateAutoRange.
        self._itemBoundsCache = weakref.WeakKeyDictionary()
        
        self.locateGroup = None  ## items displayed when using ViewBox.locate(item)
        
        self.setFlag(self.GraphicsItemFlag.ItemClipsChildrenToShape)
        self.setFlag(self.GraphicsItemFlag.ItemIsFocusable, True)  ## so we can receive key presses
        
        ## childGroup is required so that ViewBox has local coordinates similar to device coordinates.
        ## this is a workaround for a Qt + OpenGL bug that causes improper clipping
        ## https://bugreports.qt.nokia.com/browse/QTBUG-23723
        self.childGroup = ChildGroup(self)
        self.childGroup.itemsChangedListeners.append(self)
        
        self.background = QtGui.QGraphicsRectItem(self.rect())
        self.background.setParentItem(self)
        self.background.setZValue(-1e6)
        self.background.setPen(pg.functions.mkPen(None))
        self.updateBackground()
        
        self.border = pg.functions.mkPen(border)

        self.borderRect = QtGui.QGraphicsRectItem(self.rect())
        self.borderRect.setParentItem(self)
        self.borderRect.setZValue(1e3)
        self.borderRect.setPen(self.border)

        ## Make scale box that is shown when dragging on the view
        self.rbScaleBox = QtGui.QGraphicsRectItem(0, 0, 1, 1)
        self.rbScaleBox.setPen(pg.functions.mkPen((255,255,100), width=1))
        self.rbScaleBox.setBrush(pg.functions.mkBrush(255,255,0,100))
        self.rbScaleBox.setZValue(1e9)
        self.rbScaleBox.hide()
        self.addItem(self.rbScaleBox, ignoreBounds=True)

        ## show target rect for debugging
        self.target = QtGui.QGraphicsRectItem(0, 0, 1, 1)
        self.target.setPen(pg.functions.mkPen('r'))
        self.target.setParentItem(self)
        self.target.hide()

        self.axHistory = [] # maintain a history of zoom locations
        self.axHistoryPointer = -1 # pointer into the history. Allows forward/backward movement, not just "undo"

        self.setZValue(-100)
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Policy.Expanding, QtGui.QSizePolicy.Policy.Expanding))

        self.setAspectLocked(lockAspect)

        if enableMenu:
            self.menu = ViewBoxMenu(self)
        else:
            self.menu = None

        self.register(name)
        if name is None:
            self.updateViewLists()


        # // initialize the viewbox in navigate mode
        self.mode = "select"
        self.tracking = True
        self.activeScanTool = 0
        self.fiducial_active = 0
        self.defaultSpotValue = defaultSpotValue
        self.defaultSpotInterspacingValue = defaultSpotInterspacingValue


        self.rbGridBox = QtGui.QGraphicsRectItem(0, 0, 1, 1)
        self.rbGridBox.setPen(pg.functions.mkPen('#99FF33', width=1, dash=[2, 2]))
        self.rbGridBox.setBrush(pg.functions.mkBrush(0,0,0,0))
        self.rbGridBox.setZValue(1e4)
        self.rbGridBox.hide()
        self.addItem(self.rbGridBox, ignoreBounds=True)
        

        self.borderRect = QtGui.QGraphicsRectItem(self.rect())
        self.borderRect.setParentItem(self)
        self.borderRect.setZValue(1e3)
        self.borderRect.setPen(self.border)

        self.setAspectLocked(lockAspect)

        if enableMenu:
            self.menu = ViewBoxMenu(self)
        else:
            self.menu = None

        self.register(name)
        if name is None:
            self.updateViewLists()
        # try:
        #     self._parent._parent.dock_lasing_pattern_editor.SpotSizeChange.connect(self.update_spotSize_slot)
        #     self._parent._parent.dock_lasing_pattern_editor.SpotInterspacingChange.connect(self.update_spotInterspacing_slot)
        # except:
        #     QtCore.qDebug("Failed to connect to parent 464df5846")

    @QtCore.Slot(object)
    def remove_item(self, item):
        self.removeItem(item)

    @QtCore.Slot(str)
    def set_mode(self, mode):
        assert isinstance(mode, str)
        if len(mode) == 0:
            # // get the mode from the parent widget
            mode = self.mode
        self.mode = mode

    def raiseContextMenu(self, ev):
        menu = self.getMenu(ev)
        menu.popup(ev.screenPos().toPoint())

    def measure_handle_tool_clicked(self, evt):
        pos = self.mapSceneToView(evt.scenePos())
        #% check for handles
        if len(self.measure_tool.handles)==0:
            self.distanceMeasuredMoved_sig.emit(0, 0, 0)
            return None
        dX = math.fabs(self.measure_tool.handles[0]['pos'].x()-pos.x())/1000
        dY = math.fabs(self.measure_tool.handles[0]['pos'].y()-pos.y())/1000
        dis = math.sqrt(dX**2+dY**2)
        self.distanceMeasuredClicked_sig.emit(dis, dX, dY)

    def mouseMoved_custom(self,evt):
        if self.mode=='distance_measure':
            if self.sceneBoundingRect().contains(evt):
                mousePoint = self.mapSceneToView(evt)
                # // check for handles
                if len(self.measure_tool.handles)==0:
                    self._parent._parent.statusUpdate('Length= 0.0000 mm , dX/dY= (0.0000 mm,0.0000 mm)')
                    self.distanceMeasuredMoved_sig.emit(0, 0, 0)
                    return None

                dX = math.fabs(self.measure_tool.handles[0]['pos'].x()-mousePoint.x())/1000
                dY = math.fabs(self.measure_tool.handles[0]['pos'].y()-mousePoint.y())/1000
                dis = math.sqrt(dX**2+dY**2)
                self._parent._parent.statusUpdate('Length= '+ '{:.4f}'.format(dis) + 'mm , dX/dY= ({:.4f} mm,{:.4f} mm)'.format(dX,dY))
                self.distanceMeasuredMoved_sig.emit(dis, dX, dY)
                self.measure_tool.setPoints([self.measure_tool.handles[0]['pos'], [mousePoint.x(),mousePoint.y()]])
        elif self.mode=='fiducial_marker':
            if self.sceneBoundingRect().contains(evt) and self.fiducial_active:
                mousePoint = self.mapSceneToView(evt)
                self.activeScanTool.setPoints([[x['pos'].x(),x['pos'].y()] for x in self.activeScanTool.handles[:-1]]+[[mousePoint.x(),mousePoint.y()]])
        elif self.mode=='select':
            self._parent.lineEdit_coords.setText(str(self.mapSceneToView(evt)))

    def mouseDragFinishedEvent(self, ev):
        print(ev, self.mode)

    def mouseDragEvent(self, ev):

        if self.mode == 'fiducial_marker':
            if ev.button() == QtCore.Qt.LeftButton:
                ev.ignore()
            else:
                pg.ViewBox.mouseDragEvent(self, ev)
            ev.accept()


    def clear_selection(self):
        """

        :return:
        """
        # // remove all borders
        self._parent._clear_borders()
        # // clear selection from the render table
        self._parent.tbl_render_order.clearSelection()
        # // clear the currently selected image
        self._parent.update_field_current = None

    @QtCore.Slot(object)
    def mouseClickEvent(self, ev):
        """
        Slot for a mouse click event
        :param ev:
        :return:
        """
        if ev.button() == QtCore.Qt.LeftButton:
            if self.mode == "fiducial_marker":
                print('mouse click event: fiducial_marker')
                # // check the number of handles
                mousePoint = self.mapSceneToView(ev.pos())
                if not self.fiducial_active:
                    # // create the line segment
                    self.activeScanTool = field_area_tool.fiducial_marker_tool(positions=[[mousePoint.x(), mousePoint.y()], [mousePoint.x(), mousePoint.y()]], closed=False, movable=False)
                    # self.activeScanTool.mouseClickEvent.
                    self.activeScanTool.setZValue(1e4)
                    self.addItem(self.activeScanTool)
                    self.fiducial_active = 1


        elif ev.button() == QtCore.Qt.RightButton and self.menuEnabled():
            ev.accept()
            self.raiseContextMenu(ev)

        elif ev.button() == QtCore.Qt.MiddleButton:
            pos = ev.scenePos()
            view = ev.currentItem
            view_point = view.mapToView(pos)
            if view_point:
                self.stageMoveUpdate_sig.emit(view_point.x(), view_point.y())


    def create_pattern(self):
        import numpy as np
        trajectory_nodes = np.zeros((2,0,3))
        zheight = 0

        if self.mode == "fiducial_marker":
            # // generate a pattern of the current scanTool and close it
            print('add one fiducial marker')
            self.fiducialMarkerAdded_sig.emit(self.activeScanTool)
            self.activeScanTool = 0
            self.fiducial_active = 0
            # // this pattern is not added to the scan list
            return


        else:
            scans=[]
