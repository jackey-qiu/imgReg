# -*- coding: utf-8 -*-
import os


"""
ROI.py -  Interactive graphics items for GraphicsView (ROI widgets)
Copyright 2010  Luke Campagnola
Distributed under MIT/X11 license. See license.txt for more infomation.

Implements a series of graphics items which display movable/scalable/rotatable shapes
for use as region-of-interest markers. ROI class automatically handles extraction 
of array data from ImageItems.

The ROI class is meant to serve as the base for more specific types; see several examples
of how to build an ROI at the bottom of the file.
"""
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
#from numpy.linalg import norm
from pyqtgraph.Point import *
from pyqtgraph.SRTTransform import SRTTransform
from math import cos, sin
from pyqtgraph import functions as fn
from pyqtgraph.graphicsItems.GraphicsObject import GraphicsObject
from pyqtgraph.graphicsItems.UIGraphicsItem import UIGraphicsItem
from pyqtgraph import getConfigOption

__all__ = [
    'ROI', 'LineSegmentROI', 'PolyLineROI',
]

def rectStr(r):
    return "[%f, %f] + [%f, %f]" % (r.x(), r.y(), r.width(), r.height())

class ROI(GraphicsObject):
    """
    Generic region-of-interest widget.
    
    Can be used for implementing many types of selection box with 
    rotate/translate/scale handles.
    ROIs can be customized to have a variety of shapes (by subclassing or using
    any of the built-in subclasses) and any combination of draggable handles
    that allow the user to manipulate the ROI.
    
    ================ ===========================================================
    **Arguments**
    pos              (length-2 sequence) Indicates the position of the ROI's 
                     origin. For most ROIs, this is the lower-left corner of
                     its bounding rectangle.
    size             (length-2 sequence) Indicates the width and height of the 
                     ROI.
    angle            (float) The rotation of the ROI in degrees. Default is 0.
    invertible       (bool) If True, the user may resize the ROI to have 
                     negative width or height (assuming the ROI has scale
                     handles). Default is False.
    maxBounds        (QRect, QRectF, or None) Specifies boundaries that the ROI 
                     cannot be dragged outside of by the user. Default is None.
    snapSize         (float) The spacing of snap positions used when *scaleSnap*
                     or *translateSnap* are enabled. Default is 1.0.
    scaleSnap        (bool) If True, the width and height of the ROI are forced
                     to be integer multiples of *snapSize* when being resized
                     by the user. Default is False.
    translateSnap    (bool) If True, the x and y positions of the ROI are forced
                     to be integer multiples of *snapSize* when being resized
                     by the user. Default is False.
    rotateSnap       (bool) If True, the ROI angle is forced to a multiple of 
                     15 degrees when rotated by the user. Default is False.
    parent           (QGraphicsItem) The graphics item parent of this ROI. It
                     is generally not necessary to specify the parent.
    pen              (QPen or argument to pg.mkPen) The pen to use when drawing
                     the shape of the ROI.
    movable          (bool) If True, the ROI can be moved by dragging anywhere 
                     inside the ROI. Default is True.
    removable        (bool) If True, the ROI will be given a context menu with
                     an option to remove the ROI. The ROI emits
                     sigRemoveRequested when this menu action is selected.
                     Default is False.
    ================ ===========================================================
    
    
    
    ======================= ====================================================
    **Signals**
    sigRegionChangeFinished Emitted when the user stops dragging the ROI (or
                            one of its handles) or if the ROI is changed
                            programatically.
    sigRegionChangeStarted  Emitted when the user starts dragging the ROI (or
                            one of its handles).
    sigRegionChanged        Emitted any time the position of the ROI changes,
                            including while it is being dragged by the user.
    sigHoverEvent           Emitted when the mouse hovers over the ROI.
    sigClicked              Emitted when the user clicks on the ROI.
                            Note that clicking is disabled by default to prevent
                            stealing clicks from objects behind the ROI. To 
                            enable clicking, call 
                            roi.setAcceptedMouseButtons(QtCore.Qt.LeftButton). 
                            See QtWidgets.QGraphicsItem documentation for more 
                            details.
    sigRemoveRequested      Emitted when the user selects 'remove' from the 
                            ROI's context menu (if available).
    ======================= ====================================================
    """
    
    sigRegionChangeFinished = QtCore.Signal(object)
    sigRegionChangeStarted = QtCore.Signal(object)
    sigRegionChanged = QtCore.Signal(object)
    sigHoverEvent = QtCore.Signal(object)
    sigClicked = QtCore.Signal(object, object)
    sigRemoveRequested = QtCore.Signal(object)
    
    def __init__(self, pos, size=Point(1, 1), angle=0.0, invertible=False, maxBounds=None, snapSize=1.0, scaleSnap=False, translateSnap=False, rotateSnap=False, parent=None, pen=None, movable=True, removable=False):
        #QObjectWorkaround.__init__(self)
        GraphicsObject.__init__(self, parent)
        self.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        pos = Point(pos)
        size = Point(size)
        self.aspectLocked = False
        self.translatable = movable
        self.rotateAllowed = True
        self.removable = removable
        self.menu = None
        
        self.freeHandleMoved = False ## keep track of whether free handles have moved since last change signal was emitted.
        self.mouseHovering = False
        if pen is None:
            pen = (255, 255, 255)
        self.setPen(pen)
        
        self.handlePen = QtGui.QPen(QtGui.QColor(150, 255, 255))
        self.handles = []
        self.state = {'pos': Point(0,0), 'size': Point(1,1), 'angle': 0}  ## angle is in degrees for ease of Qt integration
        self.lastState = None
        self.setPos(pos)
        self.setAngle(angle)
        self.setSize(size)
        self.setZValue(10)
        self.isMoving = False
        
        self.handleSize = 5
        self.invertible = invertible
        self.maxBounds = maxBounds
        
        self.snapSize = snapSize
        self.translateSnap = translateSnap
        self.rotateSnap = rotateSnap
        self.scaleSnap = scaleSnap
        #self.setFlag(self.ItemIsSelectable, True)
    
    def getState(self):
        return self.stateCopy()

    def stateCopy(self):
        sc = {}
        sc['pos'] = Point(self.state['pos'])
        sc['size'] = Point(self.state['size'])
        sc['angle'] = self.state['angle']
        return sc
        
    def saveState(self):
        """Return the state of the widget in a format suitable for storing to 
        disk. (Points are converted to tuple)
        
        Combined with setState(), this allows ROIs to be easily saved and 
        restored."""
        state = {}
        state['pos'] = tuple(self.state['pos'])
        state['size'] = tuple(self.state['size'])
        state['angle'] = self.state['angle']
        return state
    
    def setState(self, state, update=True):
        """
        Set the state of the ROI from a structure generated by saveState() or
        getState().
        """
        self.setPos(state['pos'], update=False)
        self.setSize(state['size'], update=False)
        self.setAngle(state['angle'], update=update)
    
    def setZValue(self, z):
        QtWidgets.QGraphicsItem.setZValue(self, z)
        for h in self.handles:
            h['item'].setZValue(z+1)
        
    def parentBounds(self):
        """
        Return the bounding rectangle of this ROI in the coordinate system
        of its parent.        
        """
        return self.mapToParent(self.boundingRect()).boundingRect()

    def setPen(self, *args, **kwargs):
        """
        Set the pen to use when drawing the ROI shape.
        For arguments, see :func:`mkPen <pyqtgraph.mkPen>`.
        """
        self.pen = fn.mkPen(*args, **kwargs)
        self.currentPen = self.pen
        self.update()
        
    def size(self):
        """Return the size (w,h) of the ROI."""
        return self.getState()['size']
        
    def pos(self):
        """Return the position (x,y) of the ROI's origin. 
        For most ROIs, this will be the lower-left corner."""
        return self.getState()['pos']
        
    def angle(self):
        """Return the angle of the ROI in degrees."""
        return self.getState()['angle']
        
    def setPos(self, pos, y=None, update=True, finish=True):
        """Set the position of the ROI (in the parent's coordinate system).
        
        Accepts either separate (x, y) arguments or a single :class:`Point` or
        ``QPointF`` argument. 
        
        By default, this method causes both ``sigRegionChanged`` and
        ``sigRegionChangeFinished`` to be emitted. If *finish* is False, then
        ``sigRegionChangeFinished`` will not be emitted. You can then use 
        stateChangeFinished() to cause the signal to be emitted after a series
        of state changes.
        
        If *update* is False, the state change will be remembered but not processed and no signals 
        will be emitted. You can then use stateChanged() to complete the state change. This allows
        multiple change functions to be called sequentially while minimizing processing overhead
        and repeated signals. Setting ``update=False`` also forces ``finish=False``.
        """
        if y is None:
            pos = Point(pos)
        else:
            # avoid ambiguity where update is provided as a positional argument
            if isinstance(y, bool):
                raise TypeError("Positional arguments to setPos() must be numerical.")
            pos = Point(pos, y)
        self.state['pos'] = pos
        QtWidgets.QGraphicsItem.setPos(self, pos)
        if update:
            self.stateChanged(finish=finish)
        
    def setSize(self, size, update=True, finish=True):
        """Set the size of the ROI. May be specified as a QPoint, Point, or list of two values.
        See setPos() for an explanation of the update and finish arguments.
        """
        size = Point(size)
        self.prepareGeometryChange()
        self.state['size'] = size
        if update:
            self.stateChanged(finish=finish)
        
    def setAngle(self, angle, update=True, finish=True):
        """Set the angle of rotation (in degrees) for this ROI.
        See setPos() for an explanation of the update and finish arguments.
        """
        self.state['angle'] = angle
        tr = QtGui.QTransform()
        #tr.rotate(-angle * 180 / np.pi)
        tr.rotate(angle)
        self.setTransform(tr)
        if update:
            self.stateChanged(finish=finish)
        
    def scale(self, s, center=[0,0], update=True, finish=True):
        """
        Resize the ROI by scaling relative to *center*.
        See setPos() for an explanation of the *update* and *finish* arguments.
        """
        c = self.mapToParent(Point(center) * self.state['size'])
        self.prepareGeometryChange()
        newSize = self.state['size'] * s
        c1 = self.mapToParent(Point(center) * newSize)
        newPos = self.state['pos'] + c - c1
        
        self.setSize(newSize, update=False)
        self.setPos(newPos, update=update, finish=finish)
        
   
    def translate(self, *args, **kargs):
        """
        Move the ROI to a new position.
        Accepts either (x, y, snap) or ([x,y], snap) as arguments
        If the ROI is bounded and the move would exceed boundaries, then the ROI
        is moved to the nearest acceptable position instead.
        
        *snap* can be:
        
        =============== ==========================================================================
        None (default)  use self.translateSnap and self.snapSize to determine whether/how to snap
        False           do not snap
        Point(w,h)      snap to rectangular grid with spacing (w,h)
        True            snap using self.snapSize (and ignoring self.translateSnap)
        =============== ==========================================================================
           
        Also accepts *update* and *finish* arguments (see setPos() for a description of these).
        """

        if len(args) == 1:
            pt = args[0]
        else:
            pt = args
            
        newState = self.stateCopy()
        newState['pos'] = newState['pos'] + pt
        
        ## snap position
        #snap = kargs.get('snap', None)
        #if (snap is not False)   and   not (snap is None and self.translateSnap is False):
        
        snap = kargs.get('snap', None)
        if snap is None:
            snap = self.translateSnap
        if snap is not False:
            newState['pos'] = self.getSnapPosition(newState['pos'], snap=snap)
        
        #d = ev.scenePos() - self.mapToScene(self.pressPos)
        if self.maxBounds is not None:
            r = self.stateRect(newState)
            #r0 = self.sceneTransform().mapRect(self.boundingRect())
            d = Point(0,0)
            if self.maxBounds.left() > r.left():
                d[0] = self.maxBounds.left() - r.left()
            elif self.maxBounds.right() < r.right():
                d[0] = self.maxBounds.right() - r.right()
            if self.maxBounds.top() > r.top():
                d[1] = self.maxBounds.top() - r.top()
            elif self.maxBounds.bottom() < r.bottom():
                d[1] = self.maxBounds.bottom() - r.bottom()
            newState['pos'] += d
        
        #self.state['pos'] = newState['pos']
        update = kargs.get('update', True)
        finish = kargs.get('finish', True)
        self.setPos(newState['pos'], update=update, finish=finish)
        #if 'update' not in kargs or kargs['update'] is True:
        #self.stateChanged()

    def rotate(self, angle, update=True, finish=True):
        """
        Rotate the ROI by *angle* degrees. 
        
        Also accepts *update* and *finish* arguments (see setPos() for a 
        description of these).
        """
        self.setAngle(self.angle()+angle, update=update, finish=finish)

    def handleMoveStarted(self):
        self.preMoveState = self.getState()
    
    def addTranslateHandle(self, pos, axes=None, item=None, name=None, index=None):
        """
        Add a new translation handle to the ROI. Dragging the handle will move 
        the entire ROI without changing its angle or shape. 
        
        Note that, by default, ROIs may be moved by dragging anywhere inside the
        ROI. However, for larger ROIs it may be desirable to disable this and
        instead provide one or more translation handles.
        
        =================== ====================================================
        **Arguments**
        pos                 (length-2 sequence) The position of the handle 
                            relative to the shape of the ROI. A value of (0,0)
                            indicates the origin, whereas (1, 1) indicates the
                            upper-right corner, regardless of the ROI's size.
        item                The Handle instance to add. If None, a new handle
                            will be created.
        name                The name of this handle (optional). Handles are 
                            identified by name when calling 
                            getLocalHandlePositions and getSceneHandlePositions.
        =================== ====================================================
        """
        pos = Point(pos)
        return self.addHandle({'name': name, 'type': 't', 'pos': pos, 'item': item}, index=index)
    
    def addFreeHandle(self, pos=None, axes=None, item=None, name=None, index=None):
        """
        Add a new free handle to the ROI. Dragging free handles has no effect
        on the position or shape of the ROI. 
        
        =================== ====================================================
        **Arguments**
        pos                 (length-2 sequence) The position of the handle 
                            relative to the shape of the ROI. A value of (0,0)
                            indicates the origin, whereas (1, 1) indicates the
                            upper-right corner, regardless of the ROI's size.
        item                The Handle instance to add. If None, a new handle
                            will be created.
        name                The name of this handle (optional). Handles are 
                            identified by name when calling 
                            getLocalHandlePositions and getSceneHandlePositions.
        =================== ====================================================
        """
        if pos is not None:
            pos = Point(pos)
        return self.addHandle({'name': name, 'type': 'f', 'pos': pos, 'item': item}, index=index)
        
    def addHandle(self, info, index=None):
        ## If a Handle was not supplied, create it now
        if 'item' not in info or info['item'] is None:
            h = Handle(self.handleSize, typ=info['type'], pen=self.handlePen, parent=self)
            h.setPos(info['pos'] * self.state['size'])
            info['item'] = h
        else:
            h = info['item']
            if info['pos'] is None:
                info['pos'] = h.pos()
            
        ## connect the handle to this ROI
        #iid = len(self.handles)
        h.connectROI(self)
        if index is None:
            self.handles.append(info)
        else:
            self.handles.insert(index, info)
        
        h.setZValue(self.zValue()+1)
        self.stateChanged()
        return h
    
    def addHandle_scan(self, info, index=None):
        ## If a Handle was not supplied, create it now
        if 'item' not in info or info['item'] is None:
            h = Handle_scan(self.handleSize, typ=info['type'], pen=self.handlePen, parent=self)
            h.setPos(info['pos'] * self.state['size'])
            info['item'] = h
        else:
            h = info['item']
            if info['pos'] is None:
                info['pos'] = h.pos()
            
        ## connect the handle to this ROI
        #iid = len(self.handles)
        h.connectROI(self)
        if index is None:
            self.handles.append(info)
        else:
            self.handles.insert(index, info)
        
        h.setZValue(self.zValue()+1)
        self.stateChanged()
        return h


    def indexOfHandle(self, handle):
        """
        Return the index of *handle* in the list of this ROI's handles.
        """
        if isinstance(handle, Handle):
            index = [i for i, info in enumerate(self.handles) if info['item'] is handle]    
            if len(index) == 0:
                raise Exception("Cannot return handle index; not attached to this ROI")
            return index[0]
        else:
            return handle
        
    def removeHandle(self, handle):
        """Remove a handle from this ROI. Argument may be either a Handle 
        instance or the integer index of the handle."""
        index = self.indexOfHandle(handle)
            
        handle = self.handles[index]['item']
        self.handles.pop(index)
        handle.disconnectROI(self)
        if len(handle.rois) == 0:
            self.scene().removeItem(handle)
        self.stateChanged()
    
    def replaceHandle(self, oldHandle, newHandle):
        """Replace one handle in the ROI for another. This is useful when 
        connecting multiple ROIs together.
        
        *oldHandle* may be a Handle instance or the index of a handle to be
        replaced."""
        index = self.indexOfHandle(oldHandle)
        info = self.handles[index]
        self.removeHandle(index)
        info['item'] = newHandle
        info['pos'] = newHandle.pos()
        self.addHandle(info, index=index)
        
    def checkRemoveHandle(self, handle):
        ## This is used when displaying a Handle's context menu to determine
        ## whether removing is allowed. 
        ## Subclasses may wish to override this to disable the menu entry.
        ## Note: by default, handles are not user-removable even if this method returns True.
        return True
        
        
    def getLocalHandlePositions(self, index=None):
        """Returns the position of handles in the ROI's coordinate system.
        
        The format returned is a list of (name, pos) tuples.
        """
        if index == None:
            positions = []
            for h in self.handles:
                positions.append((h['name'], h['pos']))
            return positions
        else:
            return (self.handles[index]['name'], self.handles[index]['pos'])
            
    def getSceneHandlePositions(self, index=None):
        """Returns the position of handles in the scene coordinate system.
        
        The format returned is a list of (name, pos) tuples.
        """
        if index == None:
            positions = []
            for h in self.handles:
                positions.append((h['name'], h['item'].scenePos()))
            return positions
        else:
            return (self.handles[index]['name'], self.handles[index]['item'].scenePos())
        
    def getHandles(self):
        """
        Return a list of this ROI's Handles.
        """
        return [h['item'] for h in self.handles]
    
    def mapSceneToParent(self, pt):
        return self.mapToParent(self.mapFromScene(pt))

    def setSelected(self, s):
        QtWidgets.QGraphicsItem.setSelected(self, s)
        #print "select", self, s
        if s:
            for h in self.handles:
                h['item'].show()
        else:
            for h in self.handles:
                h['item'].hide()


    def hoverEvent(self, ev):
        hover = False
        if not ev.isExit():
            if self.translatable and ev.acceptDrags(QtCore.Qt.LeftButton):
                hover=True
                
            for btn in [QtCore.Qt.LeftButton, QtCore.Qt.RightButton, QtCore.Qt.MiddleButton]:
                if int(self.acceptedMouseButtons() & btn) > 0 and ev.acceptClicks(btn):
                    hover=True
            if self.contextMenuEnabled():
                ev.acceptClicks(QtCore.Qt.RightButton)
                
        if hover:
            self.setMouseHover(True)
            self.sigHoverEvent.emit(self)
            ev.acceptClicks(QtCore.Qt.LeftButton)  ## If the ROI is hilighted, we should accept all clicks to avoid confusion.
            ev.acceptClicks(QtCore.Qt.RightButton)
            ev.acceptClicks(QtCore.Qt.MiddleButton)
        else:
            self.setMouseHover(False)

    def setMouseHover(self, hover):
        ## Inform the ROI that the mouse is(not) hovering over it
        if self.mouseHovering == hover:
            return
        self.mouseHovering = hover
        self._updateHoverColor()
        
    def _updateHoverColor(self):
        pen = self._makePen()
        if self.currentPen != pen:
            self.currentPen = pen
            self.update()
        
    def _makePen(self):
        # Generate the pen color for this ROI based on its current state.
        if self.mouseHovering:
            return fn.mkPen(255, 255, 0)
        else:
            return self.pen

    def contextMenuEnabled(self):
        return self.removable
    
    def raiseContextMenu(self, ev):
        if not self.contextMenuEnabled():
            return
        menu = self.getMenu()
        menu = self.scene().addParentContextMenus(self, menu, ev)
        pos = ev.screenPos()
        menu.popup(QtCore.QPoint(pos.x(), pos.y()))

    def getMenu(self):
        if self.menu is None:
            self.menu = QtWidgets.QMenu()
            self.menu.setTitle("ROI")
            remAct = QtGui.QAction("Remove ROI", self.menu)
            remAct.triggered.connect(self.removeClicked)
            self.menu.addAction(remAct)
            self.menu.remAct = remAct
        return self.menu

    def removeClicked(self):
        ## Send remove event only after we have exited the menu event handler
        QtCore.QTimer.singleShot(0, lambda: self.sigRemoveRequested.emit(self))
        
    def mouseDragEvent(self, ev):
        if ev.isStart():
            #p = ev.pos()
            #if not self.isMoving and not self.shape().contains(p):
                #ev.ignore()
                #return        
            if ev.button() == QtCore.Qt.LeftButton:
                self.setSelected(True)
                if self.translatable:
                    self.isMoving = True
                    self.preMoveState = self.getState()
                    self.cursorOffset = self.pos() - self.mapToParent(ev.buttonDownPos())
                    self.sigRegionChangeStarted.emit(self)
                    ev.accept()
                else:
                    ev.ignore()

        elif ev.isFinish():
            if self.translatable:
                if self.isMoving:
                    self.stateChangeFinished()
                self.isMoving = False
            return

        if self.translatable and self.isMoving and ev.buttons() == QtCore.Qt.LeftButton:
            snap = True if (ev.modifiers() & QtCore.Qt.ControlModifier) else None
            newPos = self.mapToParent(ev.pos()) + self.cursorOffset
            self.translate(newPos - self.pos(), snap=snap, finish=False)
        
    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton and self.isMoving:
            ev.accept()
            self.cancelMove()
        if ev.button() == QtCore.Qt.RightButton and self.contextMenuEnabled():
            self.sigClicked.emit(self, ev)

        elif int(ev.button() & self.acceptedMouseButtons()) > 0:
            ev.accept()
            self.sigClicked.emit(self, ev)
        else:
            ev.ignore()

    def cancelMove(self):
        self.isMoving = False
        self.setState(self.preMoveState)

    def checkPointMove(self, handle, pos, modifiers):
        """When handles move, they must ask the ROI if the move is acceptable.
        By default, this always returns True. Subclasses may wish override.
        """
        return True

    def movePoint(self, handle, pos, modifiers=QtCore.Qt.KeyboardModifier(), finish=True, coords='parent'):
        ## called by Handles when they are moved. 
        ## pos is the new position of the handle in scene coords, as requested by the handle.
        
        newState = self.stateCopy()
        index = self.indexOfHandle(handle)
        h = self.handles[index]
        p0 = self.mapToParent(h['pos'] * self.state['size'])
        p1 = Point(pos)
        
        if coords == 'parent':
            pass
        elif coords == 'scene':
            p1 = self.mapSceneToParent(p1)
        else:
            raise Exception("New point location must be given in either 'parent' or 'scene' coordinates.")

        
        ## transform p0 and p1 into parent's coordinates (same as scene coords if there is no parent). I forget why.
        #p0 = self.mapSceneToParent(p0)
        #p1 = self.mapSceneToParent(p1)

        ## Handles with a 'center' need to know their local position relative to the center point (lp0, lp1)
        if 'center' in h:
            c = h['center']
            cs = c * self.state['size']
            lp0 = self.mapFromParent(p0) - cs
            lp1 = self.mapFromParent(p1) - cs
        
        if h['type'] == 't':
            snap = True if (modifiers & QtCore.Qt.ControlModifier) else None
            #if self.translateSnap or ():
                #snap = Point(self.snapSize, self.snapSize)
            self.translate(p1-p0, snap=snap, update=False)
        
        elif h['type'] == 'f':
            newPos = self.mapFromParent(p1)
            h['item'].setPos(newPos)
            h['pos'] = newPos
            self.freeHandleMoved = True
            #self.sigRegionChanged.emit(self)  ## should be taken care of by call to stateChanged()
            
        elif h['type'] == 's':
            ## If a handle and its center have the same x or y value, we can't scale across that axis.
            if h['center'][0] == h['pos'][0]:
                lp1[0] = 0
            if h['center'][1] == h['pos'][1]:
                lp1[1] = 0
            
            ## snap 
            if self.scaleSnap or (modifiers & QtCore.Qt.ControlModifier):
                lp1[0] = round(lp1[0] / self.snapSize) * self.snapSize
                lp1[1] = round(lp1[1] / self.snapSize) * self.snapSize
                
            ## preserve aspect ratio (this can override snapping)
            if h['lockAspect'] or (modifiers & QtCore.Qt.AltModifier):
                #arv = Point(self.preMoveState['size']) - 
                lp1 = lp1.proj(lp0)
            
            ## determine scale factors and new size of ROI
            hs = h['pos'] - c
            if hs[0] == 0:
                hs[0] = 1
            if hs[1] == 0:
                hs[1] = 1
            newSize = lp1 / hs
            
            ## Perform some corrections and limit checks
            if newSize[0] == 0:
                newSize[0] = newState['size'][0]
            if newSize[1] == 0:
                newSize[1] = newState['size'][1]
            if not self.invertible:
                if newSize[0] < 0:
                    newSize[0] = newState['size'][0]
                if newSize[1] < 0:
                    newSize[1] = newState['size'][1]
            if self.aspectLocked:
                newSize[0] = newSize[1]
            
            ## Move ROI so the center point occupies the same scene location after the scale
            s0 = c * self.state['size']
            s1 = c * newSize
            cc = self.mapToParent(s0 - s1) - self.mapToParent(Point(0, 0))
            
            ## update state, do more boundary checks
            newState['size'] = newSize
            newState['pos'] = newState['pos'] + cc
            if self.maxBounds is not None:
                r = self.stateRect(newState)
                if not self.maxBounds.contains(r):
                    return
            
            self.setPos(newState['pos'], update=False)
            self.setSize(newState['size'], update=False)
        
        elif h['type'] in ['r', 'rf']:
            if h['type'] == 'rf':
                self.freeHandleMoved = True
            
            if not self.rotateAllowed:
                return
            ## If the handle is directly over its center point, we can't compute an angle.
            try:
                if lp1.length() == 0 or lp0.length() == 0:
                    return
            except OverflowError:
                return
            
            ## determine new rotation angle, constrained if necessary
            ang = newState['angle'] - lp0.angle(lp1)
            if ang is None:  ## this should never happen..
                return
            if self.rotateSnap or (modifiers & QtCore.Qt.ControlModifier):
                ang = round(ang / 15.) * 15.  ## 180/12 = 15
            
            ## create rotation transform
            tr = QtGui.QTransform()
            tr.rotate(ang)
            
            ## move ROI so that center point remains stationary after rotate
            cc = self.mapToParent(cs) - (tr.map(cs) + self.state['pos'])
            newState['angle'] = ang
            newState['pos'] = newState['pos'] + cc
            
            ## check boundaries, update
            if self.maxBounds is not None:
                r = self.stateRect(newState)
                if not self.maxBounds.contains(r):
                    return
            #self.setTransform(tr)
            self.setPos(newState['pos'], update=False)
            self.setAngle(ang, update=False)
            #self.state = newState
            
            ## If this is a free-rotate handle, its distance from the center may change.
            
            if h['type'] == 'rf':
                h['item'].setPos(self.mapFromScene(p1))  ## changes ROI coordinates of handle
                
        elif h['type'] == 'sr':
            if h['center'][0] == h['pos'][0]:
                scaleAxis = 1
                nonScaleAxis=0
            else:
                scaleAxis = 0
                nonScaleAxis=1
            
            try:
                if lp1.length() == 0 or lp0.length() == 0:
                    return
            except OverflowError:
                return
            
            ang = newState['angle'] - lp0.angle(lp1)
            if ang is None:
                return
            if self.rotateSnap or (modifiers & QtCore.Qt.ControlModifier):
                #ang = round(ang / (np.pi/12.)) * (np.pi/12.)
                ang = round(ang / 15.) * 15.
            
            hs = abs(h['pos'][scaleAxis] - c[scaleAxis])
            newState['size'][scaleAxis] = lp1.length() / hs
            #if self.scaleSnap or (modifiers & QtCore.Qt.ControlModifier):
            if self.scaleSnap:  ## use CTRL only for angular snap here.
                newState['size'][scaleAxis] = round(newState['size'][scaleAxis] / self.snapSize) * self.snapSize
            if newState['size'][scaleAxis] == 0:
                newState['size'][scaleAxis] = 1
            if self.aspectLocked:
                newState['size'][nonScaleAxis] = newState['size'][scaleAxis]
                
            c1 = c * newState['size']
            tr = QtGui.QTransform()
            tr.rotate(ang)
            
            cc = self.mapToParent(cs) - (tr.map(c1) + self.state['pos'])
            newState['angle'] = ang
            newState['pos'] = newState['pos'] + cc
            if self.maxBounds is not None:
                r = self.stateRect(newState)
                if not self.maxBounds.contains(r):
                    return
            #self.setTransform(tr)
            #self.setPos(newState['pos'], update=False)
            #self.prepareGeometryChange()
            #self.state = newState
            self.setState(newState, update=False)
        
        self.stateChanged(finish=finish)
    
    def stateChanged(self, finish=True):
        """Process changes to the state of the ROI.
        If there are any changes, then the positions of handles are updated accordingly
        and sigRegionChanged is emitted. If finish is True, then 
        sigRegionChangeFinished will also be emitted."""
        
        changed = False
        if self.lastState is None:
            changed = True
        else:
            state = self.getState()
            for k in list(state.keys()):
                if state[k] != self.lastState[k]:
                    changed = True
        
        self.prepareGeometryChange()
        if changed:
            ## Move all handles to match the current configuration of the ROI
            for h in self.handles:
                if h['item'] in self.childItems():
                    p = h['pos']
                    h['item'].setPos(h['pos'] * self.state['size'])
                #else:
                #    trans = self.state['pos']-self.lastState['pos']
                #    h['item'].setPos(h['pos'] + h['item'].parentItem().mapFromParent(trans))
                    
            self.update()
            self.sigRegionChanged.emit(self)
        elif self.freeHandleMoved:
            self.sigRegionChanged.emit(self)
            
        self.freeHandleMoved = False
        self.lastState = self.getState()
            
        if finish:
            self.stateChangeFinished()
            self.informViewBoundsChanged()
    
    def stateChangeFinished(self):
        self.sigRegionChangeFinished.emit(self)
    
    def stateRect(self, state):
        r = QtCore.QRectF(0, 0, state['size'][0], state['size'][1])
        tr = QtGui.QTransform()
        #tr.rotate(-state['angle'] * 180 / np.pi)
        tr.rotate(-state['angle'])
        r = tr.mapRect(r)
        return r.adjusted(state['pos'][0], state['pos'][1], state['pos'][0], state['pos'][1])
    
    
    def getSnapPosition(self, pos, snap=None):
        ## Given that pos has been requested, return the nearest snap-to position
        ## optionally, snap may be passed in to specify a rectangular snap grid.
        ## override this function for more interesting snap functionality..
        
        if snap is None or snap is True:
            if self.snapSize is None:
                return pos
            snap = Point(self.snapSize, self.snapSize)
        
        return Point(
            round(pos[0] / snap[0]) * snap[0],
            round(pos[1] / snap[1]) * snap[1]
        )
    
    def boundingRect(self):
        return QtCore.QRectF(0, 0, self.state['size'][0], self.state['size'][1]).normalized()

    def paint(self, p, opt, widget):
        # p.save()
        # Note: don't use self.boundingRect here, because subclasses may need to redefine it.
        r = QtCore.QRectF(0, 0, self.state['size'][0], self.state['size'][1]).normalized()
        
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(self.currentPen)
        p.translate(r.left(), r.top())
        p.scale(r.width(), r.height())
        p.drawRect(0, 0, 1, 1)
        # p.restore()

    def getGlobalTransform(self, relativeTo=None):
        """Return global transformation (rotation angle+translation) required to move 
        from relative state to current state. If relative state isn't specified,
        then we use the state of the ROI when mouse is pressed."""
        if relativeTo == None:
            relativeTo = self.preMoveState
        st = self.getState()
        
        ## this is only allowed because we will be comparing the two 
        relativeTo['scale'] = relativeTo['size']
        st['scale'] = st['size']
        
        t1 = SRTTransform(relativeTo)
        t2 = SRTTransform(st)
        return t2/t1
        
        
        #st = self.getState()
        
        ### rotation
        #ang = (st['angle']-relativeTo['angle']) * 180. / 3.14159265358
        #rot = QtGui.QTransform()
        #rot.rotate(-ang)

        ### We need to come up with a universal transformation--one that can be applied to other objects
        ### such that all maintain alignment.
        ### More specifically, we need to turn the ROI's position and angle into
        ### a rotation _around the origin_ and a translation.
        
        #p0 = Point(relativeTo['pos'])

        ### base position, rotated
        #p1 = rot.map(p0)
        
        #trans = Point(st['pos']) - p1
        #return trans, ang

    def applyGlobalTransform(self, tr):
        st = self.getState()
        
        st['scale'] = st['size']
        st = SRTTransform(st)
        st = (st * tr).saveState()
        st['size'] = st['scale']
        self.setState(st)


class Handle(UIGraphicsItem):
    """
    Handle represents a single user-interactable point attached to an ROI. They
    are usually created by a call to one of the ROI.add___Handle() methods.
    
    Handles are represented as a square, diamond, or circle, and are drawn with 
    fixed pixel size regardless of the scaling of the view they are displayed in.
    
    Handles may be dragged to change the position, size, orientation, or other
    properties of the ROI they are attached to.
    
    
    """
    types = {   ## defines number of sides, start angle for each handle type
        't': (4, np.pi/4),
        'f': (4, np.pi/4), 
        's': (4, 0),
        'r': (12, 0),
        'sr': (12, 0),
        'rf': (12, 0),
    }

    sigClicked = QtCore.Signal(object, object)   # self, event
    sigRemoveRequested = QtCore.Signal(object)   # self
    
    def __init__(self, radius, typ=None, pen=(200, 200, 220), parent=None, deletable=False):
        #print "   create item with parent", parent
        #self.bounds = QtCore.QRectF(-1e-10, -1e-10, 2e-10, 2e-10)
        #self.setFlags(self.ItemIgnoresTransformations | self.ItemSendsScenePositionChanges)
        self.parent =  parent
        self.rois = []
        self.radius = radius
        self.typ = typ
        self.pen = fn.mkPen(pen)
        self.currentPen = self.pen
        self.pen.setWidth(0)
        self.pen.setCosmetic(True)
        self.isMoving = False
        self.sides, self.startAng = self.types[typ]
        self.buildPath()
        self._shape = None
        self.menu = self.buildMenu()
        
        UIGraphicsItem.__init__(self, parent=parent)
        self.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        self.deletable = deletable
        if deletable:
            self.setAcceptedMouseButtons(QtCore.Qt.RightButton)        
        #self.updateShape()
        self.setZValue(11)
            
    def connectROI(self, roi):
        ### roi is the "parent" roi, i is the index of the handle in roi.handles
        self.rois.append(roi)
        
    def disconnectROI(self, roi):
        self.rois.remove(roi)
        #for i, r in enumerate(self.roi):
            #if r[0] == roi:
                #self.roi.pop(i)
                
    #def close(self):
        #for r in self.roi:
            #r.removeHandle(self)
            
    def setDeletable(self, b):
        self.deletable = b
        if b:
            self.setAcceptedMouseButtons(self.acceptedMouseButtons() | QtCore.Qt.RightButton)
        else:
            self.setAcceptedMouseButtons(self.acceptedMouseButtons() & ~QtCore.Qt.RightButton)
            
    def removeClicked(self):
        self.sigRemoveRequested.emit(self)

    def hoverEvent(self, ev):
        hover = False
        if not ev.isExit():
            if ev.acceptDrags(QtCore.Qt.LeftButton):
                hover=True
            for btn in [QtCore.Qt.LeftButton, QtCore.Qt.RightButton, QtCore.Qt.MiddleButton]:
                if int(self.acceptedMouseButtons() & btn) > 0 and ev.acceptClicks(btn):
                    hover=True
                    
        if hover:
            self.currentPen = fn.mkPen(255, 255,0)
        else:
            self.currentPen = self.pen
        self.update()
        #if (not ev.isExit()) and ev.acceptDrags(QtCore.Qt.LeftButton):
            #self.currentPen = fn.mkPen(255, 255,0)
        #else:
            #self.currentPen = self.pen
        #self.update()

    def mouseClickEvent(self, ev):
        # // left-click sends signal to the parent
        if ev.button() == QtCore.Qt.LeftButton:
            self.parentItem().mouseClickEvent(ev)
        ## right-click cancels drag
        if ev.button() == QtCore.Qt.RightButton and self.isMoving:
            self.isMoving = False  ## prevents any further motion
            self.movePoint(self.startPos, finish=True)
            #for r in self.roi:
                #r[0].cancelMove()
            ev.accept()
        elif int(ev.button() & self.acceptedMouseButtons()) > 0:
            ev.accept()
            if ev.button() == QtCore.Qt.RightButton and self.deletable:
                # // end the line scan pattern
                self.parent.finishPattern()
                # self.raiseContextMenu(ev)
            self.sigClicked.emit(self, ev)
        else:
            ev.ignore()        
            
            #elif self.deletable:
                #ev.accept()
                #self.raiseContextMenu(ev)
            #else:
                #ev.ignore()
                
    def buildMenu(self):
        menu = QtWidgets.QMenu()
        menu.setTitle("Handle")
        self.removeAction = menu.addAction("Remove handle", self.removeClicked) 
        return menu
        
    def getMenu(self):
        return self.menu

        

    def raiseContextMenu(self, ev):
        menu = self.scene().addParentContextMenus(self, self.getMenu(), ev)
        
        ## Make sure it is still ok to remove this handle
        removeAllowed = all([r.checkRemoveHandle(self) for r in self.rois])
        self.removeAction.setEnabled(removeAllowed)
        pos = ev.screenPos()
        menu.popup(QtCore.QPoint(pos.x(), pos.y()))    

    def mouseDragEvent(self, ev):
        if ev.button() != QtCore.Qt.LeftButton:
            return
        ev.accept()
        
        ## Inform ROIs that a drag is happening 
        ##  note: the ROI is informed that the handle has moved using ROI.movePoint
        ##  this is for other (more nefarious) purposes.
        #for r in self.roi:
            #r[0].pointDragEvent(r[1], ev)
            
        if ev.isFinish():
            if self.isMoving:
                for r in self.rois:
                    r.stateChangeFinished()
            self.isMoving = False
        elif ev.isStart():
            for r in self.rois:
                r.handleMoveStarted()
            self.isMoving = True
            self.startPos = self.scenePos()
            self.cursorOffset = self.scenePos() - ev.buttonDownScenePos()
            
        if self.isMoving:  ## note: isMoving may become False in mid-drag due to right-click.
            pos = ev.scenePos() + self.cursorOffset
            self.movePoint(pos, ev.modifiers(), finish=False)

    def movePoint(self, pos, modifiers=QtCore.Qt.KeyboardModifier(), finish=True):
        for r in self.rois:
            if not r.checkPointMove(self, pos, modifiers):
                return
        #print "point moved; inform %d ROIs" % len(self.roi)
        # A handle can be used by multiple ROIs; tell each to update its handle position
        for r in self.rois:
            r.movePoint(self, pos, modifiers, finish=finish, coords='scene')
        
    def buildPath(self):
        size = self.radius
        self.path = QtGui.QPainterPath()
        ang = self.startAng
        dt = 2*np.pi / self.sides
        for i in range(0, self.sides+1):
            x = size * cos(ang)
            y = size * sin(ang)
            ang += dt
            if i == 0:
                self.path.moveTo(x, y)
            else:
                self.path.lineTo(x, y)            
            
    def paint(self, p, opt, widget):
        ### determine rotation of transform
        #m = self.sceneTransform()
        ##mi = m.inverted()[0]
        #v = m.map(QtCore.QPointF(1, 0)) - m.map(QtCore.QPointF(0, 0))
        #va = np.arctan2(v.y(), v.x())
        
        ### Determine length of unit vector in painter's coords
        ##size = mi.map(Point(self.radius, self.radius)) - mi.map(Point(0, 0))
        ##size = (size.x()*size.x() + size.y() * size.y()) ** 0.5
        #size = self.radius
        
        #bounds = QtCore.QRectF(-size, -size, size*2, size*2)
        #if bounds != self.bounds:
            #self.bounds = bounds
            #self.prepareGeometryChange()
        p.setRenderHints(p.Antialiasing, True)
        p.setPen(self.currentPen)
        
        #p.rotate(va * 180. / 3.1415926)
        #p.drawPath(self.path)        
        p.drawPath(self.shape())
        #ang = self.startAng + va
        #dt = 2*np.pi / self.sides
        #for i in range(0, self.sides):
            #x1 = size * cos(ang)
            #y1 = size * sin(ang)
            #x2 = size * cos(ang+dt)
            #y2 = size * sin(ang+dt)
            #ang += dt
            #p.drawLine(Point(x1, y1), Point(x2, y2))
            
    def shape(self):
        if self._shape is None:
            s = self.generateShape()
            if s is None:
                return self.path
            self._shape = s
            self.prepareGeometryChange()  ## beware--this can cause the view to adjust, which would immediately invalidate the shape.
        return self._shape
    
    def boundingRect(self):
        #print 'roi:', self.roi
        s1 = self.shape()
        #print "   s1:", s1
        #s2 = self.shape()
        #print "   s2:", s2
        
        return self.shape().boundingRect()
            
    def generateShape(self):
        ## determine rotation of transform
        #m = self.sceneTransform()  ## Qt bug: do not access sceneTransform() until we know this object has a scene.
        #mi = m.inverted()[0]
        dt = self.deviceTransform()
        
        if dt is None:
            self._shape = self.path
            return None
        
        v = dt.map(QtCore.QPointF(1, 0)) - dt.map(QtCore.QPointF(0, 0))
        va = np.arctan2(v.y(), v.x())
        
        dti = fn.invertQTransform(dt)
        devPos = dt.map(QtCore.QPointF(0,0))
        tr = QtGui.QTransform()
        tr.translate(devPos.x(), devPos.y())
        tr.rotate(va * 180. / 3.1415926)
        
        return dti.map(tr.map(self.path))
        
        
    def viewTransformChanged(self):
        GraphicsObject.viewTransformChanged(self)
        self._shape = None  ## invalidate shape, recompute later if requested.
        self.update()
        
    #def itemChange(self, change, value):
        #if change == self.ItemScenePositionHasChanged:
            #self.updateShape()

class Handle_scan(Handle):
    def __init__(self, radius, typ=None, pen=(200, 200, 220), parent=None, deletable=False):
        Handle.__init__(self, radius, typ=typ, pen=pen, parent=parent, deletable=deletable)
    # ROI.__init__(self, pos, size, **args)
    def buildPath(self):
        size = self.radius
        self.path = QtGui.QPainterPath()
        ang = self.startAng
        dt = 2*np.pi / self.sides
        for i in range(0, self.sides+1):
            x = size * cos(ang)
            y = size * sin(ang)
            ang += dt
            if i == 0:
                self.path.moveTo(x, y)
            else:
                self.path.lineTo(x, y)   
        # self.path.moveTo(-size, 0)
        # self.path.lineTo(size, 0)
        # self.path.moveTo(0,-size)
        # self.path.lineTo(0, size) 
        # self.path.closeSubpath()
        # c=[
        #     (-0.5, -0.05), (-0.5, 0.05), (-0.05, 0.05), (-0.05, 0.5),
        #     (0.05, 0.5), (0.05, 0.05), (0.5, 0.05), (0.5, -0.05),
        #     (0.05, -0.05), (0.05, -0.5), (-0.05, -0.5), (-0.05, -0.05)
        # ]
        # self.path.moveTo(*c[0])
        # for x,y in c[1:]:
        #     self.path.lineTo(x, y)
        # self.path.closeSubpath()

            
    def paint(self, p, opt, widget):
        ### determine rotation of transform
        #m = self.sceneTransform()
        ##mi = m.inverted()[0]
        #v = m.map(QtCore.QPointF(1, 0)) - m.map(QtCore.QPointF(0, 0))
        #va = np.arctan2(v.y(), v.x())
        
        ### Determine length of unit vector in painter's coords
        ##size = mi.map(Point(self.radius, self.radius)) - mi.map(Point(0, 0))
        ##size = (size.x()*size.x() + size.y() * size.y()) ** 0.5
        #size = self.radius
        
        #bounds = QtCore.QRectF(-size, -size, size*2, size*2)
        #if bounds != self.bounds:
            #self.bounds = bounds
            #self.prepareGeometryChange()
        p.setRenderHints(p.Antialiasing, True)
        p.setPen(pg.functions.mkPen('#99FF33', width=1))
        
        #p.rotate(va * 180. / 3.1415926)
        #p.drawPath(self.path)        
        p.drawPath(self.shape())
        #ang = self.startAng + va
        #dt = 2*np.pi / self.sides
        #for i in range(0, self.sides):
            #x1 = size * cos(ang)
            #y1 = size * sin(ang)
            #x2 = size * cos(ang+dt)
            #y2 = size * sin(ang+dt)
            #ang += dt
            #p.drawLine(Point(x1, y1), Point(x2, y2))

class PolyLineROI(ROI):
    """
    Container class for multiple connected LineSegmentROIs.
    
    This class allows the user to draw paths of multiple line segments.
    
    ============== =============================================================
    **Arguments**
    positions      (list of length-2 sequences) The list of points in the path.
                   Note that, unlike the handle positions specified in other
                   ROIs, these positions must be expressed in the normal
                   coordinate system of the ROI, rather than (0 to 1) relative
                   to the size of the ROI.
    closed         (bool) if True, an extra LineSegmentROI is added connecting 
                   the beginning and end points.
    \**args        All extra keyword arguments are passed to ROI()
    ============== =============================================================
    
    """
    def __init__(self, positions, closed=False, pos=None, **args):
        
        if pos is None:
            pos = [0,0]
            
        self.closed = closed
        self.segments = []
        ROI.__init__(self, pos, size=[1,1], **args)
        
        self.setPoints(positions)

    def setPoints(self, points, closed=None):
        """
        Set the complete sequence of points displayed by this ROI.
        
        ============= =========================================================
        **Arguments**
        points        List of (x,y) tuples specifying handle locations to set.
        closed        If bool, then this will set whether the ROI is closed 
                      (the last point is connected to the first point). If
                      None, then the closed mode is left unchanged.
        ============= =========================================================
        
        """
        if closed is not None:
            self.closed = closed
        
        self.clearPoints()
        
        for p in points:
            self.addFreeHandle(p)
        
        start = -1 if self.closed else 0
        for i in range(start, len(self.handles)-1):
            self.addSegment(self.handles[i]['item'], self.handles[i+1]['item'])
        
    def clearPoints(self):
        """
        Remove all handles and segments.
        """
        while len(self.handles) > 0:
            self.removeHandle(self.handles[0]['item'])
    
    def getState(self):
        state = ROI.getState(self)
        state['closed'] = self.closed
        state['points'] = [Point(h.pos()) for h in self.getHandles()]
        return state

    def saveState(self):
        state = ROI.saveState(self)
        state['closed'] = self.closed
        state['points'] = [tuple(h.pos()) for h in self.getHandles()]
        return state

    def setState(self, state):
        ROI.setState(self, state)
        self.setPoints(state['points'], closed=state['closed'])
        
    def addSegment(self, h1, h2, index=None):
        seg = _PolyLineSegment(handles=(h1, h2), pen=self.pen, parent=self, movable=False)
        if index is None:
            self.segments.append(seg)
        else:
            self.segments.insert(index, seg)
        seg.sigClicked.connect(self.segmentClicked)
        seg.setAcceptedMouseButtons(QtCore.Qt.LeftButton)
        seg.setZValue(self.zValue()+1)
        for h in seg.handles:
            h['item'].setDeletable(True)
            h['item'].setAcceptedMouseButtons(h['item'].acceptedMouseButtons() | QtCore.Qt.LeftButton) ## have these handles take left clicks too, so that handles cannot be added on top of other handles
        
    def setMouseHover(self, hover):
        ## Inform all the ROI's segments that the mouse is(not) hovering over it
        ROI.setMouseHover(self, hover)
        for s in self.segments:
            s.setParentHover(hover)
          
    def addHandle(self, info, index=None):
        h = ROI.addHandle(self, info, index=index)
        h.sigRemoveRequested.connect(self.removeHandle)
        self.stateChanged(finish=True)
        return h
        
    def segmentClicked(self, segment, ev=None, pos=None): ## pos should be in this item's coordinate system
        if ev != None:
            pos = segment.mapToParent(ev.pos())
        elif pos != None:
            pos = pos
        else:
            raise Exception("Either an event or a position must be given.")
        h1 = segment.handles[0]['item']
        h2 = segment.handles[1]['item']
        
        i = self.segments.index(segment)
        h3 = self.addFreeHandle(pos, index=self.indexOfHandle(h2))
        self.addSegment(h3, h2, index=i+1)
        segment.replaceHandle(h2, h3)
        
    def removeHandle(self, handle, updateSegments=True):
        ROI.removeHandle(self, handle)
        handle.sigRemoveRequested.disconnect(self.removeHandle)
        
        if not updateSegments:
            return
        segments = handle.rois[:]
        
        if len(segments) == 1:
            self.removeSegment(segments[0])
        elif len(segments) > 1:
            handles = [h['item'] for h in segments[1].handles]
            handles.remove(handle)
            segments[0].replaceHandle(handle, handles[0])
            self.removeSegment(segments[1])
        self.stateChanged(finish=True)
        
    def removeSegment(self, seg):
        for handle in seg.handles[:]:
            seg.removeHandle(handle['item'])
        self.segments.remove(seg)
        seg.sigClicked.disconnect(self.segmentClicked)
        self.scene().removeItem(seg)
        
    def checkRemoveHandle(self, h):
        ## called when a handle is about to display its context menu
        if self.closed:
            return len(self.handles) > 3
        else:
            return len(self.handles) > 2
        
    def paint(self, p, *args):
        pass
    
    def boundingRect(self):
        return self.shape().boundingRect()

    def shape(self):
        p = QtGui.QPainterPath()
        if len(self.handles) == 0:
            return p
        p.moveTo(self.handles[0]['item'].pos())
        for i in range(len(self.handles)):
            p.lineTo(self.handles[i]['item'].pos())
        p.lineTo(self.handles[0]['item'].pos())
        return p

    def getArrayRegion(self, data, img, axes=(0,1), **kwds):
        """
        Return the result of ROI.getArrayRegion(), masked by the shape of the 
        ROI. Values outside the ROI shape are set to 0.
        """
        br = self.boundingRect()
        if br.width() > 1000:
            raise Exception()
        sliced = ROI.getArrayRegion(self, data, img, axes=axes, fromBoundingRect=True, **kwds)
        
        if img.axisOrder == 'col-major':
            mask = self.renderShapeMask(sliced.shape[axes[0]], sliced.shape[axes[1]])
        else:
            mask = self.renderShapeMask(sliced.shape[axes[1]], sliced.shape[axes[0]])
            mask = mask.T
            
        # reshape mask to ensure it is applied to the correct data axes
        shape = [1] * data.ndim
        shape[axes[0]] = sliced.shape[axes[0]]
        shape[axes[1]] = sliced.shape[axes[1]]
        mask = mask.reshape(shape)

        return sliced * mask

    def setPen(self, *args, **kwds):
        ROI.setPen(self, *args, **kwds)
        for seg in self.segments:
            seg.setPen(*args, **kwds)



class LineSegmentROI(ROI):
    """
    ROI subclass with two freely-moving handles defining a line.
    
    ============== =============================================================
    **Arguments**
    positions      (list of two length-2 sequences) The endpoints of the line 
                   segment. Note that, unlike the handle positions specified in 
                   other ROIs, these positions must be expressed in the normal
                   coordinate system of the ROI, rather than (0 to 1) relative
                   to the size of the ROI.
    \**args        All extra keyword arguments are passed to ROI()
    ============== =============================================================
    """
    
    def __init__(self, positions=(None, None), pos=None, handles=(None,None), **args):
        if pos is None:
            pos = [0,0]
            
        ROI.__init__(self, pos, [1,1], **args)
        #ROI.__init__(self, positions[0])
        if len(positions) > 2:
            raise Exception("LineSegmentROI must be defined by exactly 2 positions. For more points, use PolyLineROI.")
        
        for i, p in enumerate(positions):
            self.addFreeHandle(p, item=handles[i])
                
        
    def listPoints(self):
        return [p['item'].pos() for p in self.handles]
            
    def paint(self, p, *args):
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(self.currentPen)
        h1 = self.handles[0]['item'].pos()
        h2 = self.handles[1]['item'].pos()
        p.drawLine(h1, h2)
        
    def boundingRect(self):
        return self.shape().boundingRect()
    
    def shape(self):
        p = QtGui.QPainterPath()
    
        h1 = self.handles[0]['item'].pos()
        h2 = self.handles[1]['item'].pos()
        dh = h2-h1
        if dh.length() == 0:
            return p
        pxv = self.pixelVectors(dh)[1]
        if pxv is None:
            return p
            
        pxv *= 4
        
        p.moveTo(h1+pxv)
        p.lineTo(h2+pxv)
        p.lineTo(h2-pxv)
        p.lineTo(h1-pxv)
        p.lineTo(h1+pxv)
      
        return p
    
    def getArrayRegion(self, data, img, axes=(0,1), order=1, **kwds):
        """
        Use the position of this ROI relative to an imageItem to pull a slice 
        from an array.
        
        Since this pulls 1D data from a 2D coordinate system, the return value 
        will have ndim = data.ndim-1
        
        See ROI.getArrayRegion() for a description of the arguments.
        """
        
        imgPts = [self.mapToItem(img, h['item'].pos()) for h in self.handles]
        rgns = []
        for i in range(len(imgPts)-1):
            d = Point(imgPts[i+1] - imgPts[i])
            o = Point(imgPts[i])
            r = fn.affineSlice(data, shape=(int(d.length()),), vectors=[Point(d.norm())], origin=o, axes=axes, order=order, **kwds)
            rgns.append(r)
            
        return np.concatenate(rgns, axis=axes[0])
        

class _PolyLineSegment(LineSegmentROI):
    # Used internally by PolyLineROI
    def __init__(self, *args, **kwds):
        self._parentHovering = False
        LineSegmentROI.__init__(self, *args, **kwds)
        
    def setParentHover(self, hover):
        # set independently of own hover state
        if self._parentHovering != hover:
            self._parentHovering = hover
            self._updateHoverColor()
        
    def _makePen(self):
        if self.mouseHovering or self._parentHovering:
            return fn.mkPen(255, 255, 0)
        else:
            return self.pen
        
    def hoverEvent(self, ev):
        # accept drags even though we discard them to prevent competition with parent ROI
        # (unless parent ROI is not movable)
        if self.parentItem():
            if self.parentItem().translatable:
                ev.acceptDrags(QtCore.Qt.LeftButton)
            return LineSegmentROI.hoverEvent(self, ev)  
        
class scanTool(PolyLineROI):
    sigClicked = QtCore.Signal(object, object)
    def __init__(self, positions, closed=False, pos=None, **args):
        
        if pos is None:
            pos = [0,0]
            
        self.closed = closed
        self.segments = []
        self.translatable = False
        ROI.__init__(self, pos, size=[1,1], **args)
        self.setPoints(positions)

    def mouseClickEvent(self, ev):
        view_point = ev.scenePos()
        # print(pos)
        view = ev.currentItem
        view_point = view.mapToView(view_point)-view_point
        # view_point=self.mapSceneToView(ev.pos())
        self.setPoints([[x['pos'].x(),x['pos'].y()] for x in self.handles]+[[view_point.x(),view_point.y()]])
        # print(self.mapSceneToView(ev.pos()),1111)

    def setMouseHover(self, hover):
        ## Inform all the ROI's segments that the mouse is(not) hovering over it
        # ROI.setMouseHover(self, hover)
        # for s in self.segments:
        #     s.setParentHover(hover)
        pass

    def addHandle(self, info, index=None):
        h = ROI.addHandle_scan(self, info, index=index)
        h.sigRemoveRequested.connect(self.removeHandle)
        self.stateChanged(finish=True)
        return h

    def addSegment(self, h1, h2, index=None):
        seg = _PolyLineSegment_scan(handles=(h1, h2), pen=self.pen, parent=self, movable=False)
        if index is None:
            self.segments.append(seg)
        else:
            self.segments.insert(index, seg)
        seg.sigClicked.connect(self.segmentClicked)
        seg.setAcceptedMouseButtons(QtCore.Qt.LeftButton)
        seg.setZValue(self.zValue()+1)
        for h in seg.handles:
            h['item'].setDeletable(True)
            h['item'].setAcceptedMouseButtons(h['item'].acceptedMouseButtons() | QtCore.Qt.LeftButton) ## have these handles take left clicks too, so that handles cannot be added on top of other handles
    
    def finishPattern(self):
        # // delete the last handle (which was being updated dynamically), as we don't need it any longer
        self.setPoints([[x['pos'].x(),x['pos'].y()] for x in self.handles[:-1]])
        # // finish the scan pattern by reseting the active tool
        self.parentItem().getViewBox().create_pattern()

class LineSegment_scan(GraphicsObject):
    def __init__(self, positions=(None, None), **args):
        GraphicsObject.__init__(self, parent)
        self.aspectLocked = False
        self.translatable = movable
        self.rotateAllowed = False
        self.removable = removable
        self.menu = None
        self.mouseHovering = False
        self.pen = QtGui.QPen(QtGui.QColor(150, 255, 255))
        self.state = {'pos': Point(0,0), 'size': Point(1,1), 'angle': 0}
        self.setPos(pos)
        update = True
        self.setAngle(angle)
        # self.setSize(size)
        # self.setZValue(10)
        # self.isMoving = False
        # self.handleSize = 5
        # self.invertible = invertible
        # self.maxBounds = maxBounds
        # self.snapSize = snapSize
        # self.translateSnap = translateSnap
        # self.rotateSnap = rotateSnap
        # self.scaleSnap = scaleSnap

    def setPos(self, pos, y=None, update=True, finish=True):
        """Set the position of the ROI (in the parent's coordinate system).
        
        Accepts either separate (x, y) arguments or a single :class:`Point` or
        ``QPointF`` argument. 
        
        By default, this method causes both ``sigRegionChanged`` and
        ``sigRegionChangeFinished`` to be emitted. If *finish* is False, then
        ``sigRegionChangeFinished`` will not be emitted. You can then use 
        stateChangeFinished() to cause the signal to be emitted after a series
        of state changes.
        
        If *update* is False, the state change will be remembered but not processed and no signals 
        will be emitted. You can then use stateChanged() to complete the state change. This allows
        multiple change functions to be called sequentially while minimizing processing overhead
        and repeated signals. Setting ``update=False`` also forces ``finish=False``.
        """
        if y is None:
            pos = Point(pos)
        else:
            # avoid ambiguity where update is provided as a positional argument
            if isinstance(y, bool):
                raise TypeError("Positional arguments to setPos() must be numerical.")
            pos = Point(pos, y)
        self.state['pos'] = pos
        QtWidgets.QGraphicsItem.setPos(self, pos)
        if update:
            self.stateChanged(finish=finish)


class LineSegmentROI_scan(ROI):    
    def __init__(self, positions=(None, None), pos=None, handles=(None,None), **args):
        if pos is None:
            pos = [0,0]
            
        ROI.__init__(self, pos, [1,1], **args)
        #ROI.__init__(self, positions[0])
        if len(positions) > 2:
            raise Exception("LineSegmentROI must be defined by exactly 2 positions. For more points, use PolyLineROI.")
        
        for i, p in enumerate(positions):
            self.addFreeHandle(p, item=handles[i])
            
    def listPoints(self):
        return [p['item'].pos() for p in self.handles]
            
    def paint(self, p, *args):
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(pg.functions.mkPen('#99FF33', width=1, dash=[2,2]))
        h1 = self.handles[0]['item'].pos()
        h2 = self.handles[1]['item'].pos()
        p.drawLine(h1, h2)
        
    def boundingRect(self):
        return self.shape().boundingRect()
    
    def shape(self):
        p = QtGui.QPainterPath()
    
        h1 = self.handles[0]['item'].pos()
        h2 = self.handles[1]['item'].pos()
        dh = h2-h1
        if dh.length() == 0:
            return p
        pxv = self.pixelVectors(dh)[1]
        if pxv is None:
            return p
            
        pxv *= 4
        
        p.moveTo(h1+pxv)
        p.lineTo(h2+pxv)
        p.lineTo(h2-pxv)
        p.lineTo(h1-pxv)
        p.lineTo(h1+pxv)
      
        return p

class _PolyLineSegment_scan(LineSegmentROI_scan):
    # Used internally by PolyLineROI
    def __init__(self, *args, **kwds):
        self._parentHovering = False
        LineSegmentROI_scan.__init__(self, *args, **kwds)

class fiducial_marker_tool(scanTool):
    """
    Class which modifies the look of the endpoints of the scan line in order to differentiate it from the normal scan
    line
    - the line has a different look to the endpoint
    - the line has a maximum of two endpoints (a single vertex)
    """
    def __init__(self, *args, **kwds):
        self._parentHovering = False
        scanTool.__init__(self, *args, **kwds)

    def mouseClickEvent(self, ev):
        view_point = ev.scenePos()
        # print(pos)
        view = ev.currentItem
        view_point = view.mapToView(view_point) - view_point
        # view_point=self.mapSceneToView(ev.pos())
        self.setPoints([[x['pos'].x(), x['pos'].y()] for x in self.handles] + [[view_point.x(), view_point.y()]])
        # print(self.mapSceneToView(ev.pos()),1111)
        if len(self.handles)>2:
            # // delete the last handle (which was being updated dynamically), as we don't need it any longer
            self.setPoints([[x['pos'].x(), x['pos'].y()] for x in self.handles[:-1]])
            # // finish the scan pattern by reseting the active tool
            self.parentItem().getViewBox().create_pattern()

class spotTool(ROI):
    """
    A crosshair ROI whose position is at the center of the crosshairs. By default, it is scalable, rotatable
    and translatable.
    """
    positionReleased_sig = QtCore.Signal(object)
    def __init__(self, pos=None, size=None, label="", index=0,**kargs):
        if size == None:
            #size = [100e-6,100e-6]
            size=[1,1]
        if pos == None:
            pos = [0,0]
        self._shape = None
        ROI.__init__(self, pos, size, **kargs)
        self.sigRegionChanged.connect(self.invalidate)
        self.aspectLocked = True
        self.pen = pg.functions.mkPen('#99FF33', width=1)
        self.addTranslateHandle(Point(0, 0), Point(0, 0))

    def repositioned_center_by_drag(self, pos):
        self.positionReleased_sig.emit(pos)

    def invalidate(self):
        self._shape = None
        self.prepareGeometryChange()
        
    def boundingRect(self):
        #size = self.size()
        #return QtCore.QRectF(-size[0]/2., -size[1]/2., size[0], size[1]).normalized()
        return self.shape().boundingRect()
    
    #def getRect(self):
        ### same as boundingRect -- for internal use so that boundingRect can be re-implemented in subclasses
        #size = self.size()
        #return QtCore.QRectF(-size[0]/2., -size[1]/2., size[0], size[1]).normalized()
    def shape(self):
        if self._shape is None:
            radius = self.getState()['size'][1]
            p = QtGui.QPainterPath()
            p.moveTo(Point(0, -radius))
            p.lineTo(Point(0, radius))
            p.moveTo(Point(-radius, 0))
            p.lineTo(Point(radius, 0))
            p = self.mapToDevice(p)
            stroker = QtGui.QPainterPathStroker()
            stroker.setWidth(10)
            outline = stroker.createStroke(p)
            self._shape = self.mapFromDevice(outline)
        return self._shape
    
    def paint(self, p, *args):
        radius = self.getState()['size'][1]
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(self.currentPen)
        p.drawLine(Point(0, -radius), Point(0, radius))
        p.drawLine(Point(-radius, 0), Point(radius, 0))

class voiDrawTool(ROI):
    """
    Container class for multiple connected LineSegmentROIs.

    This class allows the user to draw paths of multiple line segments.

    ============== =============================================================
    **Arguments**
    positions      (list of length-2 sequences) The list of points in the path.
                   Note that, unlike the handle positions specified in other
                   ROIs, these positions must be expressed in the normal
                   coordinate system of the ROI, rather than (0 to 1) relative
                   to the size of the ROI.
    closed         (bool) if True, an extra LineSegmentROI is added connecting
                   the beginning and end points.
    \**args        All extra keyword arguments are passed to ROI()
    ============== =============================================================

    """
    sigClicked = QtCore.Signal(object, object)

    def __init__(self, positions=[], closed=False, pos=None, **args):
        if pos is None:
            pos = [0, 0]
        self.closed = closed
        self.areaFinished = 0
        self.segments = []
        self.translatable = False
        self.closed = closed
        self.segments = []
        ROI.__init__(self, pos, size=[1, 1], **args)
        self.local_position_history, self.position_history = [], []

    def addDrawPoint(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            self.local_position_history = self.local_position_history + [[ev.pos().y(), ev.pos().x()]]
            view = ev.currentItem
            view_point = view.mapToView(ev.pos())
            self.position_history = self.position_history + [[view_point.x(), view_point.y()]]
            self.setPoints(self.position_history)
            ev.accept()

    def addSegment(self, h1, h2, index=None):
        seg = LineSegmentROI(positions=(h1, h2), pen=self.pen, parent=self, movable=False)
        if index is None:
            self.segments.append(seg)
        else:
            self.segments.insert(index, seg)
        seg.setZValue(self.zValue() + 1)

    def removeMask(self):
        self.parentItem().getViewBox()._parent._parent.voi_create_widget.clear_voi_selection()


    def setPoints(self, points, closed=None):
        """
        Set the complete sequence of points displayed by this ROI.

        ============= =========================================================
        **Arguments**
        points        List of (x,y) tuples specifying handle locations to set.
        closed        If bool, then this will set whether the ROI is closed
                      (the last point is connected to the first point). If
                      None, then the closed mode is left unchanged.
        ============= =========================================================

        """
        if closed is not None:
            self.closed = closed

        self.clearSegments()

        start = -1 if self.closed else 0
        self.position_history = points
        for i in range(start, len(points) - 1):
            self.addSegment( Point(points[i]), Point(points[i + 1]))

    def clearSegments(self):
        for seg in self.segments:
            self.scene().removeItem(seg)
        self.segments = []

    def clearPoints(self):
        """
        Remove all handles and segments.
        """
        while len(self.handles) > 0:
            self.removeHandle(self.handles[0]['item'])

    def removeSegment(self, seg):
        for handle in seg.handles[:]:
            seg.removeHandle(handle['item'])
        self.segments.remove(seg)

        self.scene().removeItem(seg)

    def paint(self, p, *args):
        pass

    def boundingRect(self):
        return self.shape().boundingRect()

    def shape(self):
        p = QtGui.QPainterPath()
        if len(self.position_history) == 0:
            return p
        p.moveTo(Point(self.position_history[0]))
        for i in range(len(self.position_history)):
            p.lineTo(Point(self.position_history[i]))
        p.lineTo(Point(self.position_history[0]))
        return p

    def getArrayRegion(self, data, img, axes=(0, 1), **kwds):
        """
        Return the result of ROI.getArrayRegion(), masked by the shape of the
        ROI. Values outside the ROI shape are set to 0.
        """
        br = self.boundingRect()
        if br.width() > 1000:
            raise Exception()
        sliced = ROI.getArrayRegion(self, data, img, axes=axes, fromBoundingRect=True, **kwds)

        if img.axisOrder == 'col-major':
            mask = self.renderShapeMask(sliced.shape[axes[0]], sliced.shape[axes[1]])
        else:
            mask = self.renderShapeMask(sliced.shape[axes[1]], sliced.shape[axes[0]])
            mask = mask.T

        # reshape mask to ensure it is applied to the correct data axes
        shape = [1] * data.ndim
        shape[axes[0]] = sliced.shape[axes[0]]
        shape[axes[1]] = sliced.shape[axes[1]]
        mask = mask.reshape(shape)

        return sliced * mask

    def setPen(self, *args, **kwds):
        ROI.setPen(self, *args, **kwds)
        for seg in self.segments:
            seg.setPen(*args, **kwds)
