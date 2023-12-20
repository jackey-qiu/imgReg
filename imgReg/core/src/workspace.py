# -*- coding: utf-8 -*-


# // module to manage the field view
# from ui.workspace_widget import Ui_workspace_widget
import sys, os
from pathlib import Path
import numpy as np
import pandas as pd
import pyqtgraph as pg
import pyqtgraph.functions as fn
from PyQt5 import QtGui, QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QApplication,QMessageBox, QAbstractItemView
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import pyqtSlot as Slot
from settings_unit import ScaleBar
from geometry_unit import geometry_dialog, geometry_widget_wrapper
from field_dft_registration import mdi_field_imreg_show, MdiFieldImreg_Wrapper
from spatial_registration_module import rotatePoint
from field_fiducial_markers_unit import FiducialMarkerWidget, FiducialMarkerWidget_wrapper
from particle_tool import particle_widget_wrapper
from field_tools import FieldViewBox
from utility_widgets import check_true
from importmodule import load_im_xml, load_align_xml
from util import PandasModel

setting_file = str(Path(__file__).parent.parent.parent / 'config' / 'appsettings.ini')
ui_file_folder = Path(__file__).parent.parent / 'ui'

def quick_level(data):
    while data.size > 1e6:
        ax = np.argmax((data.shape[0],data.shape[1],data.shape[2]))
        sl = [slice(None)] * data.ndim
        sl[ax] = slice(None, None, 2)
        data = data[sl]
    return np.percentile(data, 2.5), np.percentile(data, 97.5)

def quick_min_max(data):
    from numpy import nanmin, nanmax
    while data.size > 1e6:
        ax = np.argmax((data.shape[0],data.shape[1],data.shape[2]))
        sl = [slice(None)] * data.ndim
        sl[ax] = slice(None, None, 2)
        data = data[sl]
    return nanmin(data), nanmax(data)

class WorkSpace(QMainWindow, MdiFieldImreg_Wrapper, geometry_widget_wrapper, FiducialMarkerWidget_wrapper, particle_widget_wrapper):
    """
    Main class of the workspace
    """
    statusMessage_sig = Signal(str)
    progressUpdate_sig = Signal(float)
    logMessage_sig = Signal(dict)
    switch_selection_sig = Signal(str)
    #fiducial marking signals
    updateFieldMode_sig = Signal(str)
    removeTool_sig = Signal(object)
    saveimagedb_sig = Signal()

    def __init__(self, parent = None):
        """
        Initialize the class
        :param parent: parent widget
        :param settings_object: settings object
        """
        QMainWindow.__init__(self, parent)
        #super(WorkSpace, self).__init__(parent)
        uic.loadUi(str(ui_file_folder / 'img_reg_main_window.ui'), self)

        MdiFieldImreg_Wrapper.__init__(self)
        geometry_widget_wrapper.__init__(self)
        FiducialMarkerWidget_wrapper.__init__(self)
        particle_widget_wrapper.__init__(self)
        self.setMinimumSize(800, 600)
        self.widget_terminal.update_name_space('gui', self)
        self._parent = self
        self.settings_object = QtCore.QSettings(setting_file, QtCore.QSettings.IniFormat)

        self.img_backup_path = "ImageBackup.imagedb"
        self.zoomfactor_relative_to_cam = 0
        self.field_list = []
        self.field_img = []
        self.patternCollection = []
        self.tbl_render_order = TableWidgetDragRows(self)
        self.tbl_render_order.setMaximumWidth(5000)
        self.tbl_render_order.setColumnCount(3)
        self.tbl_render_order.setHorizontalHeaderLabels(["Show", "Opacity", "Layer"])
        self.gridLayout_renderTable.addWidget(self.tbl_render_order)

        # // set up the custom view box
        self.field = FieldViewBox(lockAspect=True, _parent=self)
        self.field.invertY()

        self.bt_alignMenu.setMenu(QtWidgets.QMenu(self.bt_alignMenu))
        self.bt_alignMenu.clicked.connect(self.bt_alignMenu.showMenu)
        self.bt_align = QtWidgets.QPushButton(self)
        action = QtWidgets.QWidgetAction(self.bt_alignMenu)
        action.setDefaultWidget(self.bt_align)
        self.bt_alignMenu.menu().addAction(action)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(str(ui_file_folder / 'icons' / 'Viewing' / 'coordinates_128x128.png')), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.bt_align.setIcon(icon1)
        self.bt_align.setIconSize(QtCore.QSize(32, 32))
        self.bt_align.setText("Align images")
        self.bt_align.clicked.connect(self.geometry_dialog_show)

        self.bt_dft_registration = QtWidgets.QPushButton(self)
        action = QtWidgets.QWidgetAction(self.bt_alignMenu)
        action.setDefaultWidget(self.bt_dft_registration)
        self.bt_alignMenu.menu().addAction(action)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(str(ui_file_folder / 'icons' / 'Viewing' / 'coordinates_128x128.png')), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.bt_dft_registration.setIcon(icon1)
        self.bt_dft_registration.setIconSize(QtCore.QSize(32, 32))
        self.bt_dft_registration.setText("DFT position refinement")
        self.bt_dft_registration.clicked.connect(self.launch_dft)

        self.bt_fiducial_markers = QtWidgets.QPushButton(self)
        action = QtWidgets.QWidgetAction(self.bt_alignMenu)
        action.setDefaultWidget(self.bt_fiducial_markers)
        self.bt_alignMenu.menu().addAction(action)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(str(ui_file_folder / 'icons' / 'Viewing' / 'coordinates_128x128.png')), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.bt_fiducial_markers.setIcon(icon1)
        self.bt_fiducial_markers.setIconSize(QtCore.QSize(32, 32))
        self.bt_fiducial_markers.setText("Add fiducial markers")
        self.bt_fiducial_markers.clicked.connect(self.show_fiducial_alignment)

        from pyqtgraph import GraphicsLayoutWidget
        self.graphicsView_field = GraphicsLayoutWidget(self)
        self.graphics_layout.addWidget(self.graphicsView_field)
        self.graphicsView_field.setCentralItem(self.field)
        self.set_cursor_icon()

        self.field.scene().sigMouseMoved.connect(self.field.mouseMoved_custom)

        self.ScanList_items = []
        self.move_box = None
        self.update_field_current = None
        self.field.enableAutoRange(x=False, y=False)

        original = self.field.resizeEvent

        def resizeEventWrapper(event):
            original(event)

            # // range restriction
            v = self.field.height() / self.field.width()
            d = np.max((self.X_controller_travel, self.Y_controller_travel)) / v
            self.field.setLimits(xMin=-0.6 * d,
                                 xMax=1.2 * d, \
                                 yMin=-0.1 * d * v,
                                 yMax=1.1 * d * v, \
                                 minXRange=2, minYRange=2 * v, \
                                 maxXRange=1.2 * d,
                                 maxYRange=1.2 * d * v)

        resizeEventWrapper._original = original
        self.field.resizeEvent = resizeEventWrapper
        self.drawMode = 'auto'

        self.update_environment_color(self.settings_object.value("Visuals/environmentBackgroundColor"))

        # // remove colorbar
        if hasattr(self, 'cb'):
            if self.cb in self.field.scene().items():
                self.cb.hide()
                self.cb.update()
                self.field.scene().removeItem(self.cb)
                self.field.scene().update()

        if hasattr(self, 'cb1'):
            if self.cb1 in self.field.scene().items():
                self.cb1.hide()
                self.cb1.update()
                self.field.scene().removeItem(self.cb1)
                self.field.scene().update()

        if hasattr(self, 'cb2'):
            if self.cb2 in self.field.scene().items():
                self.cb2.hide()
                self.cb2.update()
                self.field.scene().removeItem(self.cb2)
                self.field.scene().update()

        # // remove scale
        if hasattr(self, 'sb'):
            if self.sb in self.field.scene().items():
                self.sb.hide()
                self.sb.update()
                self.field.removeItem(self.sb)
                self.field.scene().update()

        # // check for the ablation cell:

        self.X_controller_travel, self.Y_controller_travel = 100000, 100000
        if self.settings_object.contains("Stages"):
            if "(100 mm X 100mm)" in self.settings_object.value('Stages'):
                self.X_controller_travel, self.Y_controller_travel = 100000, 100000
            elif "(150 mm X 150 mm)" in self.settings_object.value('Stages'):
                self.X_controller_travel, self.Y_controller_travel = 150000, 150000
            elif "(50 mm X 50 mm)" in self.settings_object.value('Stages'):
                self.X_controller_travel, self.Y_controller_travel = 50000, 50000

        # self.add_workspace()
        self.autoRange(padding=0.02)
        if self.settings_object.contains("FileManager/restoreimagedb"):
            self.img_backup_path = self.settings_object.value("FileManager/restoreimagedb")

        self.imageBuffer = ImageBufferInfo(self,
                                           self.img_backup_path)
        self.tbl_render_order.imageBuffer = self.imageBuffer

        # // draw scalebar
        self.draw_scalebar()
        self.connect_slots()
        self.imageBuffer.recallImgBackup()
        self.highlightFirstImg()
        
    @Slot(int)    
    def switch_mode(self, tabIndex):
        tabText = self.tabWidget.tabText(tabIndex).lower()
        if 'fiducial' in tabText:
            self.field.set_mode('fiducial_marker')
            self.update_fiducial()
            if hasattr(self, 'move_box'):
                self.move_box.hide()
        elif 'dft' in tabText:
            self.field.set_mode('dft')
            if hasattr(self, 'move_box'):
                self.move_box.hide()
        elif 'geometry' in tabText or 'particle' in tabText:
            self.field.set_mode('select')
            self.update_geo()
            if hasattr(self, 'move_box'):
                self.move_box.show()
            if 'particle' in tabText:#filled the save pars for particle tracking
                self.set_pars_for_locating_particle_on_gui()

    def set_cursor_icon(self, cursor_type="cross"):
        """
        Change the cursor icon
        :param type:
        :return:
        """
        if cursor_type == "cross":
            cursor_custom = QtGui.QCursor(QtGui.QPixmap(str(ui_file_folder / 'icons' / 'Cursors' / 'target_cursor_32x32.png')))
        elif cursor_type == "pen":
            cursor_custom = QtGui.QCursor(QtGui.QPixmap(":/icon/cursor_pen.png"), hotX=26, hotY=23)
        elif cursor_type == "align":
            cursor_custom = QtGui.QCursor(QtGui.QPixmap(str(ui_file_folder / 'icons' / 'Cursors' / "registration_cursor_32x32.png")), hotX=26, hotY=23)
        self.graphicsView_field.setCursor(cursor_custom)

    def connect_slots(self):
        """
        :return:
        """
        #save image buffer sig
        self.saveimagedb_sig.connect(self.imageBuffer.writeImgBackup)
        #tabwidget signal
        self.tabWidget.tabBarClicked.connect(self.switch_mode)
        #dft slots
        self.connect_slots_dft()
        #fiducial slots
        self.connect_slots_fiducial()
        #geo slots
        self.connect_slots_geo()
        #particle slots
        self.connect_slots_par()
        #widget events
        self.bt_removeMenu.setMenu(QtWidgets.QMenu(self.bt_removeMenu))
        self.bt_removeMenu.clicked.connect(self.bt_removeMenu.showMenu)
        self.bt_delete = QtWidgets.QPushButton(self)
        action = QtWidgets.QWidgetAction(self.bt_removeMenu)
        action.setDefaultWidget(self.bt_delete)
        self.bt_removeMenu.menu().addAction(action)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(str(ui_file_folder / 'icons' / 'FileSystem' / 'close_file_128x128.png')), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.bt_delete.setIcon(icon1)
        self.bt_delete.setIconSize(QtCore.QSize(32, 32))
        self.bt_delete.setText("Delete Selected Images")
        self.bt_delete.clicked.connect(self.tbl_render_order.deleteSelection)
        self.bt_clear_tbl = QtWidgets.QPushButton(self)
        action = QtWidgets.QWidgetAction(self.bt_removeMenu)
        action.setDefaultWidget(self.bt_clear_tbl)
        self.bt_removeMenu.menu().addAction(action)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(str(ui_file_folder / 'icons' / 'FileSystem' / 'close_file_128x128.png')), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.bt_clear_tbl.setIcon(icon1)
        self.bt_clear_tbl.setIconSize(QtCore.QSize(32, 32))
        self.bt_clear_tbl.setText("Clear workspace")
        self.bt_clear_tbl.clicked.connect(self.clear)
        self.tbl_render_order.cellClicked.connect(self.tblItemClicked)

        self.bt_imageMenu.setMenu(QtWidgets.QMenu(self.bt_imageMenu))
        self.bt_imageMenu.clicked.connect(self.bt_imageMenu.showMenu)
        self.bt_recall_imagedb = QtWidgets.QPushButton(self)
        action = QtWidgets.QWidgetAction(self.bt_imageMenu)
        action.setDefaultWidget(self.bt_recall_imagedb)
        self.bt_imageMenu.menu().addAction(action)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(str(ui_file_folder / 'icons' / 'FileSystem' / 'open_folder_128x128.png')), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.bt_recall_imagedb.setIcon(icon1)
        self.bt_recall_imagedb.setIconSize(QtCore.QSize(32, 32))
        self.bt_recall_imagedb.setText("Load Image Database")
        self.bt_recall_imagedb.clicked.connect(self.loadImgBufferFromDisk)

        self.bt_export_imagedb = QtWidgets.QPushButton(self)
        action = QtWidgets.QWidgetAction(self.bt_imageMenu)
        action.setDefaultWidget(self.bt_export_imagedb)
        self.bt_imageMenu.menu().addAction(action)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(str(ui_file_folder / 'icons' / 'FileSystem' / 'save_as_128x128.png')), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.bt_export_imagedb.setIcon(icon1)
        self.bt_export_imagedb.setIconSize(QtCore.QSize(32, 32))
        self.bt_export_imagedb.setText("Save and export images")
        self.bt_export_imagedb.clicked.connect(self.saveImageBuffer)

        self.bt_import_image = QtWidgets.QPushButton(self)
        action = QtWidgets.QWidgetAction(self.bt_imageMenu)
        action.setDefaultWidget(self.bt_import_image)
        self.bt_imageMenu.menu().addAction(action)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(str(ui_file_folder / 'icons' / 'FileSystem' / 'open_folder_128x128.png')), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.bt_import_image.setIcon(icon1)
        self.bt_import_image.setText("Import image")
        self.bt_import_image.setIconSize(QtCore.QSize(32, 32))
        self.bt_import_image.clicked.connect(lambda: self.import_image_from_disk())

    def expand_full(self):
        self.mdi_field_widget.autoRange()

    def select_align(self, evt):
        self.switch_selection_sig.emit('align')
        if evt:
            #$ create an aligment mark tool
            self.mdi_field_widget.field.mode = 'align'

    def select_distance_measure(self,evt):
        self.switch_selection_sig.emit('distance_measure')
        if evt:
            self.mdi_field_widget.field.mode = 'distance_measure'

    def select_area_measure(self,evt):
        self.switch_selection_sig.emit('area_measure')
        if evt:
            self.mdi_field_widget.field.mode = 'area_measure'

    def select_navigate(self,evt):
        self.switch_selection_sig.emit('navigate')
        if evt:
            # // create a navigation tool
            self.mdi_field_widget.field.mode = 'navigate'

    def select_selection(self,evt):
        self.switch_selection_sig.emit('select')
        if evt:
            # // create a selection rectangle when dragging
            self.mdi_field_widget.field.mode = 'select'

    def select_grid(self,evt):
        self.switch_selection_sig.emit('grid')
        if evt:
            self.mdi_field_widget.field.mode = 'grid'

    def select_image_area(self,evt):
        self.switch_selection_sig.emit('image_area')
        if evt:
            self.mdi_field_widget.field.mode = 'image_area'

    def select_line(self,evt):
        self.switch_selection_sig.emit('line')
        if evt:
            self.mdi_field_widget.field.mode = 'line'

    def select_spot(self,evt):
        self.switch_selection_sig.emit('spot')
        if evt:
            self.mdi_field_widget.field.mode = 'spot'

    def select_area(self,evt):
        self.switch_selection_sig.emit('area')
        if evt:
            self.mdi_field_widget.field.mode = 'area'

    def switch_selection(self, active=''):
        if active!='select':
            self.actionSelect.blockSignals(True)
            self.actionSelect.setChecked(False)
            self.actionSelect.blockSignals(False)
        else:
            self.actionSelect.blockSignals(True)
            self.actionSelect.setChecked(True)
            self.actionSelect.blockSignals(False)
        if active!='navigate':
            self.actionNavigateSample.blockSignals(True)
            self.actionNavigateSample.setChecked(False)
            self.actionNavigateSample.blockSignals(False)
        else:
            self.actionNavigateSample.blockSignals(True)
            self.actionNavigateSample.setChecked(True)
            self.actionNavigateSample.blockSignals(False)
        if active!='line':
            self.actionLine.blockSignals(True)
            self.actionLine.setChecked(False)
            self.actionLine.blockSignals(False)
        else:
            self.actionLine.blockSignals(True)
            self.actionLine.setChecked(True)
            self.actionLine.blockSignals(False)
        if active!='grid':
            self.actionGrid.blockSignals(True)
            self.actionGrid.setChecked(False)
            self.actionGrid.blockSignals(False)
        else:
            self.actionGrid.blockSignals(True)
            self.actionGrid.setChecked(True)
            self.actionGrid.blockSignals(False)
        if active!='area':
            self.actionArea.blockSignals(True)
            self.actionArea.setChecked(False)
            self.actionArea.blockSignals(False)
        else:
            self.actionArea.blockSignals(True)
            self.actionArea.setChecked(True)
            self.actionArea.blockSignals(False)
        if active!='spot':
            self.actionSpot.blockSignals(True)
            self.actionSpot.setChecked(False)
            self.actionSpot.blockSignals(False)
        else:
            self.actionSpot.blockSignals(True)
            self.actionSpot.setChecked(True)
            self.actionSpot.blockSignals(False)
        if active!='align':
            self.actionAlignmentMarks.blockSignals(True)
            self.actionAlignmentMarks.setChecked(False)
            self.actionAlignmentMarks.blockSignals(False)
        else:
            self.actionAlignmentMarks.blockSignals(True)
            self.actionAlignmentMarks.setChecked(True)
            self.actionAlignmentMarks.blockSignals(False)
        if active!='distance_measure':
            self.actionMeasure.blockSignals(True)
            self.actionMeasure.setChecked(False)
            self.actionMeasure.blockSignals(False)
        else:
            self.actionMeasure.blockSignals(True)
            self.actionMeasure.setChecked(True)
            self.actionMeasure.blockSignals(False)
        if active!='area_measure':
            self.actionArea_measure.blockSignals(True)
            self.actionArea_measure.setChecked(False)
            self.actionArea_measure.blockSignals(False)
        else:
            self.actionArea_measure.blockSignals(True)
            self.actionArea_measure.setChecked(True)
            self.actionArea_measure.blockSignals(False)

    def add_workspace(self):
        self.workarea_bg = WorkArea(parent=self._parent,
                                    width=self.X_controller_travel,
                                    height=self.Y_controller_travel,
                                    color=self.settings_object.value("Visuals/workspaceBackgroundColor"))
        self.field.addItem(self.workarea_bg)

    def update_environment_color(self, color):
        """
        Updates the color of the widget
        :param color:
        :return:
        """
        if color:
            self.field.setBackgroundColor(color)

    def _clear_borders(self):
        # // when a new dataset is added, remove the selection box in the field view
        for k in self.field_img:
            if isinstance(k, pg.ImageItem):
                k.setBorder(None)

            elif isinstance(k, list):
                for v in k:
                    v.setBorder(None)
            elif isinstance(k, ImageBufferObject):
                k.setBorder(None)
            else:
                # // must be scatterplotitem
                print(type(k))

    def _show_border(self):
        if check_true(self.settings_object.value("Visuals/showBox")):
            border_pen = fn.mkPen(color=self.settings_object.value("Visuals/boxColor"),
                                  width=int(self.settings_object.value("Visuals/boxLinewidth")))
            self.update_field_current.setBorder(border_pen)
        else:
            self.update_field_current.setBorder(None)

    def tblItemClicked(self, row, column):
        # // set a border around the clicked item and set it as the current image
        loc = self.tbl_render_order.item(row, 2).loc
        # // in theory, the row should be == self.field_list.index(loc)
        if self.field_list.index(loc) >= 0:
            self._clear_borders()
            self.update_field_current = self.field_img[self.field_list.index(loc)]
            self._show_border()

    def drawModeUpdate(self, status):
        # // function to update the drawMode and re-render the current widget
        # // set the drawMode
        self.drawMode = status

        # // update the Figure: re-add to the pipeline
        current_group = self._parent.dock_groupselection.selected_groups[0]
        if current_group:
            self.field_remove(current_group)
            self.field_list.insert(0, current_group)
            self.field_add(current_group)

    def import_image_from_disk(self, source_path_list = []):
        # // open up an image for importing data
        import os
        if len(source_path_list) < 1:
            dialog = QtWidgets.QFileDialog()
            path = QtCore.QDir.toNativeSeparators(self.settings_object.value("FileManager/currentimagedbDir"))
            if os.path.exists(path):
                try:
                    os.chdir(path)
                except:
                    QtCore.qDebug("Error: invalid directory")
            source_path_list, _ = dialog.getOpenFileNames(self, "Open image file to be imported", os.getcwd(), \
                                                        "Image file (*.tif *.tiff *.png *.jpeg *.jpg *.bmp);;All Files (*)")
        

        if len(source_path_list) > 0:
            for filePath in source_path_list:
                if not os.path.exists(filePath):
                    continue
                d = {}
                d["Path"] = filePath
                d["Name"] = os.path.split(filePath)[-1]
                d["Focus"] = 0.0
                d["Opacity"] = 100
                d["Visible"] = True
                d["Parent"] = ""
                d["DTYPE"] = "RGBA"
                d["BaseFolder"] = os.path.dirname(filePath)
                # // check for .align file
                if os.path.exists(os.path.splitext(filePath)[0] + ".Align"):
                    xml_path = os.path.splitext(filePath)[0] + ".Align"
                    ret = load_align_xml(xml_path)
                    if ret:
                        d.update(ret)

                self.imageBuffer.load_qi(d)

            self.settings_object.setValue("FileManager/currentimagedbDir", os.path.dirname(source_path_list[0]))
            self.tbl_render_order.resizeRowsToContents()
            self.tbl_render_order.setColumnWidth(0, 55)
        
    def loadImgBufferFromDisk(self):
        import os
        dialog = QtWidgets.QFileDialog()
        path = QtCore.QDir.toNativeSeparators(self.settings_object.value("FileManager/currentimagedbDir"))
        if os.path.exists(path):
            try:
                os.chdir(path)
            except:
                QtCore.qDebug("Error: invalid directory")
        source_path_list, _ = dialog.getOpenFileName(self, "Open .imagedb file to be imported", os.getcwd(), \
                                                     "imagedb files (*.imagedb);;All Files (*)")

        # // select files based on tumbnails
        exclude_file_list = []
        # imagedb_paths = []
        # import glob
        # file_l = glob.glob(os.path.join(os.path.dirname(xml_path), '*'))
        # import xml.etree.ElementTree as ET
        # tree = ET.parse(xml_path)
        # root = tree.getroot()
        # for i, child in enumerate(root):
        #     if 'Image' in child.tag:
        #         if os.path.join(os.path.dirname(xml_path), root[i][0].text) in file_l:
        #             imagedb_paths.append(os.path.join(os.path.dirname(xml_path), root[i][0].text))
        # exclude_file_list =  imagedb_select_show(self, imagedb_paths)

        if os.path.exists(source_path_list):
            dict_list = self.imageBuffer.load_imagedb(xml_path=source_path_list, exclude_file_list=exclude_file_list)
            self.settings_object.setValue("FileManager/currentimagedbDir", os.path.dirname(source_path_list))
        else:
            self.statusMessage_sig.emit("Invalid path for the .imagedb file")
            return None

        if dict_list:
            self.imageBuffer.attrList += dict_list
            self.imageBuffer.writeImgBackup()

    def saveImageBuffer(self):
        import os
        dialog = QtWidgets.QFileDialog()
        path = QtCore.QDir.toNativeSeparators(self.settings_object.value("FileManager/currentimagedbDir"))
        if os.path.exists(path):
            os.chdir(path)
        source_path_list, _ = dialog.getSaveFileName(self, "Open .imagedb file to be imported", os.getcwd(), \
                                                     "imagedb files (*.imagedb);;All Files (*)")
        if os.path.exists(os.path.dirname(source_path_list)):
            # self.imageBuffer.writeimagedb(xml_path=source_path_list)
            self.imageBuffer.writeImgBackup(path=source_path_list)
        else:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       """<p>Invalid export path.<p>""")

    def launch_dft(self):
        """
        Launches the DFT position refinement. This takes two images, and performs registration on them
        :return:
        """
        mdi_field_imreg_show(self._parent)

    def launch_orb(self):
        """
        Launches the ORB registration tool to register images using feature detection
        :return:
        """

    def show_fiducial_alignment(self):
        """
        Show the gui for the fiducial alginment
        :return:
        """
        # if not isinstance(self.update_field_current.loc, dict):
        #     self.statusMessage_sig.emit("Please select an image to start this process.")

        
        image = self.update_field_current
        current_group = self.update_field_current.loc

        if isinstance(current_group, dict):
            attrs = current_group
        else:
            self.statusMessage_sig.emit("Please select an image to start this process.")

        fiducial_marker_dialog = FiducialMarkerWidget(self, image, attrs=attrs)
        # // connect the signals
        fiducial_marker_dialog.updateFieldMode_sig.connect(self.field.set_mode)
        fiducial_marker_dialog.removeTool_sig.connect(self.field.remove_item)
        fiducial_marker_dialog.saveimagedb_sig.connect(self.imageBuffer.writeImgBackup)
        self.field.fiducialMarkerAdded_sig.connect(fiducial_marker_dialog.add_field_tool)

        fiducial_marker_dialog.initialize_field()
        fiducial_marker_dialog.show()

    def update_cmap(self):
        if bool(self._parent.settings_object.value("Visuals/showColorBar")) and (not
        self._parent.settings_object.value("Visuals/showColorBar") == "false"):
            show_colorbar = True
        else:
            show_colorbar = False
        if self._parent.dock_colormap.multivol_mode == 1:
            if not hasattr(self._parent, 'lut'):
                self.requestLutUpdate_sig.emit(self.update_field_current.loc.get_dataset())
            # // update colormap field view
            if self.update_field_current:
                if hasattr(self.update_field_current, 'setLookupTable'):
                    self.update_field_current.setLookupTable(self._parent.dock_colormap.lut[:, :].astype(np.ubyte))
            if show_colorbar and not self._parent.dock_colormap.rgba_display_mode:
                self.redraw_colorbar()
        elif self._parent.dock_colormap.multivol_mode == 2:
            self.update_field()
        elif self._parent.dock_colormap.multivol_mode == 3:
            self.update_field()
        else:
            if show_colorbar and not self._parent.dock_colormap.rgba_display_mode:
                self.redraw_colorbar()
        self.draw_scalebar()

    def update_level_region(self, channel=0):
        """
        Update the value range that is visible in the image and the colorbar
        :param channel:
        :return:
        """
        # // get thresholds
        current_group = self._parent.dock_groupselection.selected_groups[0]
        dset = current_group.get_dataset()

        if not "Thresholds" in dset.attrs.keys():
            clim_t1 = quick_min_max(self._parent.position_tracker.retrieve_slice(dset, ['spatialx', 'spatialy', 'spatialz']))
            if dset.shape[1] > 1:
                t_ = np.zeros(shape=(2, dset.shape[1]))
                if t_.shape[1] > 1000:
                    t_ = np.zeros(shape=(2, 1))
                    t_[0, 0], t_[1, 0] = quick_level(
                        self._parent.position_tracker.retrieve_slice(dset, ['spatialx', 'spatialy', 'spatialz']),
                        channel_spec=0)
                dset.attrs["Thresholds"] = t_
                clim_t1 = quick_level(
                    self._parent.position_tracker.retrieve_slice(dset, ['spatialx', 'spatialy', 'spatialz']))
                dset.attrs["Thresholds"][:, self.slice_selectn] = clim_t1
            else:
                t_ = np.zeros(shape=(2, 1))
                dset.attrs["Thresholds"] = t_
                clim_t1 = quick_level(
                    self._parent.position_tracker.retrieve_slice(dset, ['spatialx', 'spatialy', 'spatialz']))
                dset.attrs["Thresholds"][:, 0] = clim_t1
        else:
            c = int(self._parent.position_tracker.channel_dict[channel])
            if dset.attrs["Thresholds"].shape[1] == dset.shape[1]:
                clim_t1 = (dset.attrs["Thresholds"][0, c], \
                           dset.attrs["Thresholds"][1, c])
                if clim_t1[0] == 0 and clim_t1[1] == 0:
                    clim_t1 = quick_level(
                        self._parent.position_tracker.retrieve_slice(dset, ['spatialx', 'spatialy', 'spatialz']).astype(
                            np.float))
                    dset.attrs["Thresholds"][0, c] = clim_t1[0]
                    dset.attrs["Thresholds"][1, c] = clim_t1[1]
                    self._parent.dock_colormap.bt0.setRegion(clim_t1)
            else:
                clim_t1 = (dset.attrs["Thresholds"][0, 0], dset.attrs["Thresholds"][1, 0])
                if clim_t1[0] == 0 and clim_t1[1] == 0:
                    clim_t1 = quick_level(
                        self._parent.position_tracker.retrieve_slice(dset, ['spatialx', 'spatialy', 'spatialz']))
                    dset.attrs["Thresholds"][0, 0] = clim_t1[0]
                    dset.attrs["Thresholds"][1, 0] = clim_t1[1]
                    self._parent.dock_colormap.bt0.setRegion(clim_t1)

        # // apply the levels to the image
        if self._parent.dock_colormap.multivol_mode == 1:
            if self._parent.dock_colormap.rb_cb_log.isChecked():
                # // in log mode, the value must be larger then one
                if clim_t1[0] <= 0:
                    # // if <0, bring the limit up to 1 when the limit is below 0
                    clim_t1 = (0.000000001, clim_t1[1])
                if clim_t1[1] <= 0:
                    # // if <0, bring the limit up to 1 when the limit is below 0
                    clim_t1 = (clim_t1[0], 0.000000001)
                if self.update_field_current:
                    self.update_field_current.setLevels((np.log10(clim_t1[0]), np.log10(clim_t1[1])))
            elif self._parent.dock_colormap.rb_cb_lin.isChecked() or self._parent.dock_colormap.rb_cb_cdf.isChecked():
                if self.update_field_current:
                    self.update_field_current.setLevels(clim_t1)
        else:
            # // RGB mode / RG mode: no option but to redraw the entire image
            self.update_field()
        # // update the range of the colorbar to the new range
        self.redraw_colorbar()

    def draw_scalebar(self):
        """
        Draw a scalebar
        :return:
        """
        # // remove current scalebar

        if hasattr(self, 'sb'):
            if self.sb in self.field.scene().items():
                self.sb.hide()
                self.sb.update()
                self.field.removeItem(self.sb)
                self.field.scene().update()

        if self.settings_object.value("Visuals/showScalebar"):
            zoom = 1.0

        
        # // save this settings to the settings file
        self.sb = ScaleBar(size=float(self.settings_object.value("ScaleSize")),
                           height=int(self.settings_object.value("ScaleHeight")),
                           position=self.settings_object.value("ScalePosition"),
                           brush=self.settings_object.value("ScaleColor"),
                           pen=self.settings_object.value("ScaleColor"),
                           fs=int(self.settings_object.value("ScaleFontSize")),
                           suffix='um')
        self.field.addItem(self.sb)
        self.sb.setParentItem(self.field)
        self.sb._scaleAnchor__parent = self.field
        # self.sb.anchor((1, 1), (1, 1), offset=(-30, -30))
        self.sb.updateBar()
        self.show_scale_bar(self.settings_object.value("Visuals/showScalebar"))
        # print(type(self.settings_object.value("Visuals/showScalebar")))
        #self.show_scale_bar(False)

    def show_scale_bar(self, enabled):
        if type(enabled)==str:
            if enabled in ['0', 'False', 'false']:
                enabled = False
            else:
                enabled = True
        elif type(enabled) == bool:
            pass
        elif type(enabled)==int:
            if enabled==0:
                enabled = False
            else:
                enabled = True
        if enabled:
            self.sb.show()
        else:
            print("hiding scalebar")
            self.sb.hide()

    def delete(self, row):
        """
        Deletes a specific row from the table
        :param row:
        :return:
        """
        item = self.tbl_render_order.item(row, 2)
        if item.loc in self.field_list:
            i = self.field_list.index(item.loc)

            # // delete image from the buffer
            if isinstance(self.field_img[i], ImageBufferObject):
                self.imageBuffer.removeImgBackup(item.loc)
            # // untick the image in the pipeline
            elif isinstance(self.field_img[i], pg.ImageItem):
                self.clearSingleTick.emit(item.loc)

            self.field.removeItem(self.field_img[i])
            del self.field_img[i]
            del self.field_list[i]

        # // removing row from field list
        self.tbl_render_order.removeRow(row)

        # // recalculate_all the render order
        self.tbl_render_order.field_order_update()

    def clear(self):
        """
        Clear the workspace by removing all images.
        :return:
        """
        # // clear internal list
        self.field.clear()
        # // alternative is to delete all items in the field view
        for img in self.field_img:
            self.field.removeItem(img)
            img.deleteLater()

        self.field_list = []
        self.field_img = []
        self.move_box = False
        self.update_field_current = None

        # // clear imageBuffer and backup
        self.imageBuffer.attrList = []
        self.imageBuffer.writeImgBackup()

        # // clear table
        self.tbl_render_order.clear()
        self.tbl_render_order.setColumnCount(3)
        self.tbl_render_order.setRowCount(0)
        self.tbl_render_order.setHorizontalHeaderLabels(["Show", "Opacity", "Layer"])
        # self.tbl_render_order.setAlternatingRowColors(True)
        self.tbl_render_order.horizontalHeader().ResizeMode = QtWidgets.QHeaderView.ResizeToContents

        # // remove colorbar
        if hasattr(self, 'cb'):
            if self.cb in self.field.scene().items():
                self.field.scene().removeItem(self.cb)
                self.field.scene().update()

        # // remove scale
        if hasattr(self, 'sb'):
            if self.sb in self.field.scene().items():
                self.field.removeItem(self.sb)
                self.field.scene().update()

        # // remove crosshair
        # self.field._remove_crosshair()

        # // restore the WorkArea
        self.add_workspace()
        self.autoRange(padding=0.02)

        # // reset the pipeline checkboxes left of the datasets
        # self.clearTicks.emit()

        # // go through the project, and set visibility of each sample group to false.


    def goto(self):
        # // focus on the currently selected dataset in the field view
        row = self.tbl_render_order.currentRow()
        i = self.tbl_render_order.item(row, 2)
        if i:
            self.autoRange(items=[self.field_img[self.field_list.index(i.loc)]])

    def update_slice(self, z):
        # // update the slice displayed in the workspace (the spatial memory dataset is resliced and the image is updated.
        if not self.update_field_current:
            # // if self.update_field_current ==  None, do not refresh the field
            return None

        img = self.update_field_current

        current_group = self._parent.dock_groupselection.selected_groups[0]
        dset = current_group.get_dataset()

        if isinstance(img, ImageBufferObject):
            return None

        if isinstance(img, pg.ImageItem):
            if not self._parent._dock_colormap.rgba_display_mode:
                if self._parent.dock_colormap.multivol_mode == 1:
                    # // check which axis are spatial,x and spatial,y
                    img1 = self._parent.position_tracker.retrieve_slice(dset, ['spatialx', 'spatialy'],
                                                                        channel_spec=0).astype(float)

                    # // draw the images
                    if self._parent.dock_colormap.rb_cb_log.isChecked():
                        img.setImage(np.log10(np.clip(img1, 0.000000001, np.infty)))

                    elif self._parent.dock_colormap.rb_cb_lin.isChecked() or self._parent.dock_colormap.rb_cb_cdf.isChecked():
                        img.setImage(img1)

                    if not "Thresholds" in dset.attrs.keys():
                        clim_t1 = quick_min_max(np.expand_dims(img1, axis=0).astype(np.float64))
                    else:
                        c = int(self._parent.position_tracker.channel_dict[0])
                        clim_t1 = (dset.attrs["Thresholds"][0, c], \
                                   dset.attrs["Thresholds"][1, c])

                    # // Set the new levels
                    if self._parent.dock_colormap.rb_cb_log.isChecked():
                        # // in log mode, the value must be larger then one
                        if clim_t1[0] <= 0:
                            # // if <0, bring the limit up to 1 when the limit is below 0
                            clim_t1 = (0.000000001, clim_t1[1])
                        if clim_t1[1] <= 0:
                            # // if <0, bring the limit up to 1 when the limit is below 0
                            clim_t1 = (clim_t1[0], 0.000000001)
                        img.setLevels((np.log10(clim_t1[0]), np.log10(clim_t1[1])))
                    elif self._parent.dock_colormap.rb_cb_lin.isChecked() or self._parent.dock_colormap.rb_cb_cdf:
                        img.setLevels(clim_t1)

                elif self._parent.dock_colormap.multivol_mode == 2:
                    # // multi-volume (RG mapping enabled)
                    channels_enabled = 1, 2
                    img1 = np.transpose(
                        self._parent.position_tracker.retrieve_slice(dset, ['spatialx', 'spatialy'],
                                                                     channel_spec=0)).astype(float)
                    if hasattr(img1, 'mask'):
                        img1.mask = False
                    img2 = np.atleast_2d(
                        self._parent.position_tracker.retrieve_slice(dset, ['spatialx', 'spatialy'],
                                                                     channel_spec=1)).astype(float)
                    if hasattr(img2, 'mask'):
                        img2.mask = False
                    # // get thresholds
                    if not "Thresholds" in self._parent.dock_groupselection.selected_groups[0].attrs.keys():
                        clim_t1 = quick_level(img1)
                        clim_t2 = quick_level(img2)
                    else:
                        c1 = int(self._parent.position_tracker.channel_dict[0])
                        c2 = int(self._parent.position_tracker.channel_dict[1])
                        clim_t1 = (self._parent.dock_groupselection.selected_groups[0].attrs["Thresholds"][0, c1], \
                                   self._parent.dock_groupselection.selected_groups[0].attrs["Thresholds"][1, c1])
                        clim_t2 = (self._parent.dock_groupselection.selected_groups[0].attrs["Thresholds"][0, c2], \
                                   self._parent.dock_groupselection.selected_groups[0].attrs["Thresholds"][1, c2])

                    rg_map = np.dstack(
                        ((np.clip(img1, clim_t1[0], clim_t1[1]) - clim_t1[0]) / (clim_t1[1] - clim_t1[0]) * 255, \
                         (np.clip(img2, clim_t2[0], clim_t2[1]) - clim_t2[0]) / (clim_t2[1] - clim_t2[0]) * 255, \
                         np.zeros(img1.shape)))

                    img.levels = None
                    img.lut = None
                    img.setImage(rg_map)

                elif self._parent.dock_colormap.multivol_mode == 3:
                    # // mutli-volume (RGB mapping) is enabled
                    img1 = np.atleast_2d(self._parent.position_tracker.retrieve_slice(dset, ['spatialx', 'spatialy'],
                                                                                      channel_spec=0)).astype(float)
                    if hasattr(img1, 'mask'):
                        img1.mask = False

                    img2 = np.atleast_2d(self._parent.position_tracker.retrieve_slice(dset, ['spatialx', 'spatialy'],
                                                                                      channel_spec=1)).astype(float)
                    if hasattr(img2, 'mask'):
                        img2.mask = False

                    img3 = np.atleast_2d(self._parent.position_tracker.retrieve_slice(dset, ['spatialx', 'spatialy'],
                                                                                      channel_spec=2)).astype(float)
                    if hasattr(img3, 'mask'):
                        img3.mask = False
                    # // get thresholds
                    if not "Thresholds" in self._parent.dock_groupselection.selected_groups[0].attrs.keys():
                        clim_t1 = quick_level(img1)
                        clim_t2 = quick_level(img2)
                        clim_t3 = quick_level(img3)
                    else:
                        c1 = int(self._parent.position_tracker.channel_dict[0])
                        c2 = int(self._parent.position_tracker.channel_dict[1])
                        c3 = int(self._parent.position_tracker.channel_dict[2])
                        clim_t1 = (self._parent.dock_groupselection.selected_groups[0].attrs["Thresholds"][0, c1], \
                                   self._parent.dock_groupselection.selected_groups[0].attrs["Thresholds"][1, c1])
                        clim_t2 = (self._parent.dock_groupselection.selected_groups[0].attrs["Thresholds"][0, c2], \
                                   self._parent.dock_groupselection.selected_groups[0].attrs["Thresholds"][1, c2])
                        clim_t3 = (self._parent.dock_groupselection.selected_groups[0].attrs["Thresholds"][0, c3], \
                                   self._parent.dock_groupselection.selected_groups[0].attrs["Thresholds"][1, c3])

                    rgba_map = np.dstack(
                        ((np.clip(img1, clim_t1[0], clim_t1[1]) - clim_t1[0]) / (clim_t1[1] - clim_t1[0]) * 255, \
                         (np.clip(img2, clim_t2[0], clim_t2[1]) - clim_t2[0]) / (clim_t2[1] - clim_t2[0]) * 255, \
                         (np.clip(img3, clim_t3[0], clim_t3[1]) - clim_t3[0]) / (clim_t3[1] - clim_t3[0]) * 255))
                    img.setImage(rgba_map)


    def update_field(self, dset=None, alt_display0=np.array([]), alt_display1=np.array([]), alt_display2=np.array([])):
        """
        Refreshes the data in the field image, redisplays the image, and the colorbars are redrawn. To be used
        when either the data changes, or when the number of channels (in RGB image) changes.

        :param dset:
        :param alt_display0:
        :param alt_display1:
        :param alt_display2:
        :return:
        """
        current_group = self

        # // search for the image of the dset in the workspace. If found, update the image
        if not (current_group in self.field_list):
            return None
        img = self.field_img[self.field_list.index(current_group)]

        self._parent.dock_colormap.im_update(current_group)

        if isinstance(img, ImageBufferObject):
            return None
        if isinstance(img, pg.ImageItem):
            if self._parent.dock_colormap.rgba_display_mode == False:
                if self._parent.dock_colormap.multivol_mode == 1:
                    # // check which axis are spatial,x and spatial,y
                    c = int(self._parent.position_tracker.channel_dict[0])
                    if len(alt_display0.shape) == 2:
                        img1 = alt_display0
                    else:
                        img1 = self._parent.position_tracker.retrieve_slice(dset, ["spatialy", "spatialx"]).T

                    if not "Thresholds" in dset.attrs.keys():
                        clim_t1 = quick_min_max(np.expand_dims(img1, axis=0).astype(np.double))
                    else:
                        if dset.attrs["Thresholds"].shape[1] > c:
                            clim_t1 = (dset.attrs["Thresholds"][0, c],
                                       dset.attrs["Thresholds"][1, c])
                        else:
                            clim_t1 = quick_min_max(np.expand_dims(img1, axis=0).astype(np.double))
                    # // draw the images
                    if self._parent.dock_colormap.rb_cb_log.isChecked():
                        img.setImage(np.log10(np.clip(img1, 0.000000001, np.infty)))

                    elif self._parent.dock_colormap.rb_cb_lin.isChecked() or self._parent.dock_colormap.rb_cb_cdf.isChecked():
                        img.setImage(img1)

                    # // Set the new levels
                    if self._parent.dock_colormap.rb_cb_log.isChecked():
                        # // in log mode, the value must be larger then one
                        if clim_t1[0] <= 0:
                            # // if <0, bring the limit up to 1 when the limit is below 0
                            clim_t1 = (0.000000001, clim_t1[1])
                        if clim_t1[1] <= 0:
                            # // if <0, bring the limit up to 1 when the limit is below 0
                            clim_t1 = (clim_t1[0], 0.000000001)
                        img.setLevels((np.log10(clim_t1[0]), np.log10(clim_t1[1])))
                    elif self._parent.dock_colormap.rb_cb_lin.isChecked() or self._parent.dock_colormap.rb_cb_cdf:
                        img.setLevels(clim_t1)

                    # // check if LUT is available
                    if not hasattr(self._parent, "lut"):
                        self.requestLutUpdate_sig.emit(dset)
                    self.update_cmap()

                elif self._parent.dock_colormap.multivol_mode > 1:
                    # // update the colormap, so the transparency is already updated before the new image is created
                    self.redraw_colorbar()
                    multi_map_list = []
                    for k in range(self._parent.dock_colormap.multivol_mode):
                        if k == 1:
                            if len(alt_display0.shape) == 2:
                                img_arr = alt_display0
                            else:
                                img_arr = np.atleast_2d(
                                    self._parent.position_tracker.retrieve_slice(dset, ["spatialx", "spatialy"],
                                                                                 channel_spec=1)).astype(float)
                        elif k == 2:
                            if len(alt_display1.shape) == 2:
                                img_arr = alt_display1
                            else:
                                img_arr = np.atleast_2d(
                                    self._parent.position_tracker.retrieve_slice(dset, ["spatialx", "spatialy"],
                                                                                 channel_spec=2)).astype(float)
                        else:
                            img_arr = np.atleast_2d(
                                self._parent.position_tracker.retrieve_slice(dset, ["spatialx", "spatialy"],
                                                                             channel_spec=k)).astype(float)
                        if hasattr(img_arr, 'mask'):
                            img_arr.mask = False

                        # // get thresholds
                        if not "Thresholds" in dset.attrs.keys():
                            clim = quick_level(img_arr)
                        else:
                            c1 = int(self._parent.position_tracker.channel_dict[k])
                            clim = (dset.attrs["Thresholds"][0, c1],
                                       dset.attrs["Thresholds"][1, c1])

                        # // create a custom image by mixing the colors for different channels
                        # if current_group.node.channel_dict.label[k] in self._parent.atom_database.nuclide_database.keys():
                        #     color0 = "#" + self._parent.atom_database.nuclide_database[
                        #         current_group.node.channel_dict.label[k]].color
                        color0_tuple = self._parent.dock_channels.channels[k].color.toTuple()
                        clipped_relative_img = (np.clip(img_arr, clim[0], clim[1]) - clim[0]) / (
                                    clim[1] - clim[0])
                        rg_map0 = np.dstack(
                            (clipped_relative_img * color0_tuple[0],
                             clipped_relative_img * color0_tuple[1],
                             clipped_relative_img * color0_tuple[2],
                             np.zeros(clipped_relative_img.shape)))
                        multi_map_list.append(rg_map0)

                    sum_stack = multi_map_list[0]
                    for k in range(1, len(multi_map_list)):
                        sum_stack += multi_map_list[k]
                    # print(sum_stack[:10,100], 976778677)
                    sum_stack = np.clip(sum_stack, 0, 255)
                    idx_alpha = np.sum(sum_stack, axis=2)
                    idx_alpha /= np.percentile(idx_alpha, 95)
                    idx_alpha *= 255
                    alpha = self._parent.dock_colormap.lut[:, 3]
                    sum_stack[:, :, 3] = alpha[np.clip(idx_alpha.astype(np.int), 0, 255)]
                    img.levels = None
                    img.lut = None
                    img.setImage(sum_stack)

            elif self._parent.dock_colormap.rgba_display_mode:
                img.setImage(np.transpose(dset.value, (1, 0, 2)))

        

    def geometry_dialog_show(self):
        """
        This launches the geometry editor app.
        
        :type: this function launches the geometry dialog for the selected image in the workspace
        """
        # // switch the currently selected image.
        if not self.update_field_current:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       """<p>No image selected in the render table. Therefore, no image can be aligned.<p>""")
            return None
        # // check the dataset type: is a dataset associated with this image or not?
        if isinstance(self.update_field_current.loc, dict):
            # // imageBufferObject
            aspect_ratio_window = geometry_dialog(parent=self, attrs=self.update_field_current.loc,
                                                  shape=(
                                                  self.update_field_current.width, self.update_field_current.height, 1))
            aspect_ratio_window.show()
        ret = aspect_ratio_window.exec_()
        # // datasets are already updated, but imageBufferObject require and update of the backup file
        if isinstance(self.update_field_current.loc, dict):
            if ret == 1:
                d = aspect_ratio_window.retrieve_attrs()
                # // apply the settings to the image itself
                self.update_field_current.loc = d
                # // apply the settings to the imagedb
                self.imageBuffer.updateImgBackup(d)

    def update_outl(self, outl):
        img = self.update_field_current
        if not outl.any():
            outl = [1, 1, 1, 1, 1, 1]

        if outl[0] != outl[1]:
            x_aspect = 1
        else:
            x_aspect = 1
        if outl[2] != outl[3]:
            y_aspect = 1
        else:
            y_aspect = 1

        # // rescale to 1:1
        s = img._scale
        img.scale(1 / s[0], 1 / s[1])
        # // rescale to new dimensions
        img.scale(1 / x_aspect, 1 / y_aspect)
        img._scale = (1 / x_aspect, 1 / y_aspect)

    def remove_mask(self):
        try:
            if self.voi_mask in self.field.allChildren():
                self.field.removeItem(self.voi_mask)
        except:
            pass

    def remove_color_overlay(self):
        try:
            if self.voi_color_overlay in self.field.allChildren():
                self.field.removeItem(self.voi_color_overlay)
        except:
            pass

    def start_simulation_image(self):
        self.timer = QtCore.QTimer()
        self.frame_num = 0
        self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.update_img)

        img = self.update_field_current
        current_group = img.loc
        dset = current_group.get_dataset()

        arr = np.zeros((dset.shape[3], dset.shape[4]))
        arr[:self.frame_num, :] = dset[0, 3, 0, :self.frame_num, :]
        if arr.shape[0] > 0 and arr.shape[1] > 0:
            self._parent.workspace.update_field(alt_display0=arr.T)

        self.timer.start(1000)

    def update_img(self):
        """
        update the current image with a new array. When the array is smaller, it is padded to have the correct size.
        :param img:
        :return:
        """
        img = self.update_field_current
        current_group = img.loc
        dset = current_group.get_dataset()

        arr = np.zeros((dset.shape[3], dset.shape[4]))
        arr[:self.frame_num, :] = dset[0, 3, 0, :self.frame_num, :]
        if arr.shape[0] > 0 and arr.shape[1] > 0:
            self._parent.workspace.update_field(alt_display0=arr.T)
        self.frame_num += 5
        #     if len(self.outline) == 6:
        #         # // if outline was calculated, scale the image
        #         outl = self.outline.copy()
        #         outl[3] = outl[2]+np.abs(outl[3]-outl[2])*(img.shape[1]/self.log_scanNumber)
        #         self._parent.workspace.update_outl(outl = outl)
        #         self._parent.workspace.update_field_current.setPos(pg.Point(outl[0], outl[2]))
        #     else:
        #         self._parent.workspace.update_outl(outl = [0, img.shape[0]*self.sb_spot.value()/self.sb_dosage.value(), 0, img.shape[1]*self.sb_spot.value(), 0, 1])
        #     self._parent.workspace.autoRange(items=[self._parent.workspace.update_field_current])
        # QtCore.QTimer.singleShot(1000, self.analysis_busy_reset)

    def update_mask(self, mask_display0=np.array([]), mask_color=(255, 0, 0, 128), opacity=0.7):
        """
        This adds a single VOI mask on top of the viewer. It is a single image which changes color.
        :param mask_display0:
        :param mask_color:
        :param opacity:
        :return:
        """
        if not self.update_field_current:
            # // if self.update_field_current ==  None, do not overlay the voi_mask on the field
            return None
        # // check which axis are spatial,x and spatial,y
        if len(mask_display0.shape) != 2:
            # // if no voi_mask is provided, it cannot be rendered
            return None
        # red_mask = np.dstack((mask_display0,mask_display0*0,mask_display0*0,mask_display0/2))

        # // make sure the mask is present in the image:
        if not hasattr(self, 'voi_mask'):
            self.add_mask(mask_display0=mask_display0)
            return None
        else:
            # // check if the mask is an item in the field
            if not self.voi_mask in self.field.allChildren():
                self.field.addItem(self.voi_mask)

        # // draw the images
        self.voi_mask.setImage(image=mask_display0, opacity=opacity)
        # // create LUT
        if not isinstance(mask_color, tuple):
            pg.colorTuple(mask_color)
        lut = np.zeros((5, 4))
        lut[1, :] = mask_color
        lut[2, :] = mask_color
        lut[3, :] = mask_color
        lut[4, :] = mask_color
        lut[1, 3] = 32
        lut[2, 3] = 64
        lut[3, 3] = 96
        lut[4, 3] = 128
        self.voi_mask.setLookupTable(lut)

        self.voi_mask.show()
        # // make sure the mask is on the top level
        self.voi_mask.setZValue(len(self.field_img) + 1)

    def add_mask(self, mask_display0=np.array([]), mask_color=(255, 0, 0, 128)):
        current_group = self._parent.dock_groupselection.selected_groups[0]
        dset = current_group.get_dataset()

        # // adds a transparent overlay to the current image selected in the viewbox
        self.voi_mask = pg.ImageItem()
        self.field.addItem(self.voi_mask)

        if not self.update_field_current:
            # // if self.update_field_current ==  None, do not overlay the voi_mask on the field
            return None
        # // check which axis are spatial,x and spatial,y
        if len(mask_display0.shape) != 2:
            # // if no voi_mask is provided, it cannot be rendered
            return None

        # // draw the images
        self.voi_mask.setImage(image=mask_display0, opacity=0.7)

        # // create LUT
        if not isinstance(mask_color, tuple):
            pg.colorTuple(mask_color)

        lut = np.zeros((5, 4))
        lut[1, :] = mask_color
        lut[2, :] = mask_color
        lut[3, :] = mask_color
        lut[4, :] = mask_color
        lut[1, 3] = 32
        lut[2, 3] = 64
        lut[3, 3] = 96
        lut[4, 3] = 128

        self.voi_mask.setLookupTable(lut)
        self.voi_mask.setZValue(len(self.field_img) + 1)

        if "Outline" in dset.attrs.keys():
            outl = dset.attrs["Outline"]
            if outl[0] > outl[1]:
                self.voi_mask.getViewBox().invertX()
            if outl[2] < outl[3]:
                self.voi_mask.getViewBox().invertY()
        else:
            outl = [1, 1, 1, 1, 1, 1]

        if outl[0] != outl[1]:
            if dset.shape[4] > 1:
                x_aspect = dset.shape[4] / abs(outl[0] - outl[1])
            else:
                x_aspect = 1
        else:
            x_aspect = 1
        if outl[2] != outl[3]:
            if dset.shape[3] > 1:
                y_aspect = dset.shape[3] / abs(outl[2] - outl[3])
            else:
                y_aspect = 1
        else:
            y_aspect = 1

        self.voi_mask.outl = outl

        # // translates the dataset in the field view based on the left corner coordinate in the outline
        self.voi_mask.setPos(pg.Point(outl[0], outl[2]))
        # // rotate the dataset if a rotation transformation is required
        if 'Rotation' in dset.attrs.keys():
            self.voi_mask.setRotation(dset.attrs['Rotation'])

        self.voi_mask._scale = (1 / x_aspect, 1 / y_aspect)
        self.voi_mask.scale(1 / x_aspect, 1 / y_aspect)
        return self.voi_mask

    def add_color_overlay(self, mask_display0=np.array([]), opacity=0.9):
        """
        That adds color overlay
        :param mask_display0:
        :return:
        """
        current_group = self.update_field_current.loc
        dset = current_group.get_dataset()

        # // adds a transparent overlay to the current image selected in the viewbox
        self.voi_color_overlay = pg.ImageItem()
        self.field.addItem(self.voi_color_overlay)

        if not self.update_field_current:
            # // if self.update_field_current ==  None, do not overlay the voi_color_overlay on the field
            return None
        # // check which axis are spatial,x and spatial,y
        if len(mask_display0.shape) != 3:
            # // if no voi_color_overlay is provided, it cannot be rendered
            return None

        # // draw the images
        self.voi_color_overlay.setImage(image=mask_display0, opacity=opacity)
        self.voi_color_overlay.setZValue(len(self.field_img) + 1)

        if "Outline" in dset.attrs.keys():
            outl = dset.attrs["Outline"]
            if outl[0] > outl[1]:
                self.voi_color_overlay.getViewBox().invertX()
            if outl[2] < outl[3]:
                self.voi_color_overlay.getViewBox().invertY()
        else:
            outl = [1, 1, 1, 1, 1, 1]

        if outl[0] != outl[1]:
            if mask_display0.shape[0] > 1:
                x_aspect = mask_display0.shape[0] / abs(outl[0] - outl[1])
            else:
                x_aspect = 1
        else:
            x_aspect = 1
        if outl[2] != outl[3]:
            if mask_display0.shape[1] > 1:
                y_aspect = mask_display0.shape[1] / abs(outl[2] - outl[3])
            else:
                y_aspect = 1
        else:
            y_aspect = 1

        self.voi_color_overlay.outl = outl
        # // translates the dataset in the field view based on the left corner coordinate in the outline
        self.voi_color_overlay.setPos(pg.Point(outl[0], outl[2]))
        # // rotate the dataset if a rotation transformation is required
        if 'Rotation' in dset.attrs.keys():
            self.voi_color_overlay.setRotation(dset.attrs['Rotation'])

        self.voi_color_overlay._scale = (1 / x_aspect, 1 / y_aspect)
        self.voi_color_overlay.scale(1 / x_aspect, 1 / y_aspect)
        return self.voi_color_overlay

    def update_color_overlay(self, mask_display0=np.array([]), opacity=0.9):
        """
        This adds a single VOI mask on top of the viewer. It is a single image which changes color.
        :param mask_display0:
        :param mask_color:
        :param opacity:
        :return:
        """
        if not self.update_field_current:
            # // if self.update_field_current ==  None, do not overlay the voi_mask on the field
            return None
        # // check which axis are spatial,x and spatial,y
        if len(mask_display0.shape) != 3:
            # // if no voi_mask is provided, it cannot be rendered
            return None
        # red_mask = np.dstack((mask_display0,mask_display0*0,mask_display0*0,mask_display0/2))

        # // make sure the mask is present in the image:
        if not hasattr(self, 'voi_color_overlay'):
            self.add_color_overlay(mask_display0=mask_display0, opacity=opacity)
            return None
        else:
            # // check if the mask is an item in the field
            if not self.voi_color_overlay in self.field.allChildren():
                self.field.addItem(self.voi_color_overlay)

        # // draw the images
        self.voi_color_overlay.setImage(image=mask_display0, opacity=opacity)
        # // create LUT
        self.voi_color_overlay.show()
        # // make sure the mask is on the top level
        self.voi_color_overlay.setZValue(len(self.field_img) + 10)

    def on_project_browser_clicked(self, current_group):
        """
        If the node is in the project, select the object in the field img
        """
        if current_group in self.field_list:
            field_i = self.field_list.index(current_group)
            # // autorange
            self.autoRange(items=[self.field_img[field_i]])
            # // set selected in the layer order table
            self.tbl_render_order.clearSelection()
            self.tbl_render_order.item(field_i, 0).setSelected(True)
            self.tbl_render_order.item(field_i, 2).setSelected(True)
            self.update_field_current = self.field_img[field_i]
            self._clear_borders()
            self._show_border()
        else:
            self.tbl_render_order.clearSelection()
            # // zoom out
            self.autoRange()

    def on_table_order_clicked(self, item):
        row = item.row()
        if item:
            pass
        else:
            return None

        current_group = self.tbl_render_order.item(row, 2).loc
        if 1:
            field_i = self.field_list.index(current_group)
            if self.tbl_render_order.item(row, 0).checkState():
                self.field_img[field_i].show()
            elif not self.tbl_render_order.item(row, 0).checkState():
                self.field_img[field_i].hide()
            return None

    def field_add(self, current_group):
        self.field_list.insert(0, current_group)

        # // draw the data into the field view
        self.draw_data(current_group)

        rowPosition = 0
        self.tbl_render_order.insertRow(rowPosition)
        self.tbl_render_order.setRowHeight(0, 20)
        cb = QtWidgets.QTableWidgetItem()
        cb.setCheckState(QtCore.Qt.CheckState.Checked)
        if self._parent.dock_colormap.rgba_display_mode:
            cb.setBackground(QtGui.QColor("#FF7510"))
        else:
            cb.setBackground(QtGui.QColor("#99FF33"))
        self.tbl_render_order.setItem(rowPosition, 0, cb)
        self.tbl_render_order.itemClicked.connect(lambda item: self.on_table_order_clicked(item))
        if "SampleName" in current_group.attrs:
            p = QtWidgets.QTableWidgetItem(
                '{}'.format("{} - {}".format(current_group.name, current_group.attrs["SampleName"])))
        p.loc = current_group
        self.tbl_render_order.setItem(rowPosition, 2, p)

        self.tbl_render_order.resizeRowsToContents()
        self.tbl_render_order.setColumnWidth(0, 60)
        # self.tbl_render_order.setRowHeight(0, 20)

        # return None
        self.autoRange(items=[self.update_field_current])
        self.tbl_render_order.field_order_update()

    def draw_data(self, current_group=None):
        """
        This function decides whether how to render the data
        """
        self._parent.dock_colormap.rgba_display_mode = False
        # // check if the data is an RGB(A) image
        dset = current_group.get_dataset()

        if 'DTYPE' in dset.attrs.keys():
            if dset.attrs['DTYPE'] == 'RGBA':
                if len(dset.shape) == 3:
                    if dset.shape[2] == 3 or \
                            dset.shape[2] == 4:
                        self._parent.dock_colormap.rgba_display_mode = True
        # // if the drawMode is set to automatic, decide the drawMode
        if self.drawMode == "auto":
            # // render the reconstructed images as qimage and all split dataset as voxel-clouds
            if "NodeType" in current_group.attrs.keys():
                if current_group.attrs["NodeType"] == "MultiplexedImage" or current_group.attrs["NodeType"] == "RGBA":
                    self.draw_image(dset)
                elif current_group.attrs["NodeType"] == "MultiplexedPointCloud":
                    self.draw_points(dset)
                else:
                    self.draw_image(dset)
            else:
                self.draw_image(dset)
        # // render the images
        elif self.drawMode == "image" or self._parent.dock_colormap.rgba_display_mode:
            self.draw_image(dset)
        elif self.drawMode == "points":
            self.draw_points(dset)

    def autoRange(self, items=None, padding=0.2):
        """
        Set the range of the view box to make all children visible.
        Note that this is not the same as enableAutoRange, which causes the view to 
        automatically auto-range whenever its contents are changed.
        
        ==============  ============================================================
        **Arguments:**
        padding         The fraction of the total data range to add on to the final
                        visible range. By default, this value is set between 0.02
                        and 0.1 depending on the size of the ViewBox.
        items           If specified, this is a list of items to consider when
                        determining the visible range.
        ==============  ============================================================
        """
        if items:
            bounds = self.field.mapFromItemToView(items[0], items[0].boundingRect()).boundingRect()
        else:
            bounds = self.field.childrenBoundingRect(items=items)
        if bounds is not None:
            self.field.setRange(bounds, padding=padding)

    def field_remove(self, current_group):
        # // update the table and the render order
        if current_group in self.field_list:
            try:
                self.delete(self.field_list.index(current_group))
            except:
                QtCore.qDebug("Failed to delete group")

    def progressUpdate(self, v):
        # slot for updating the progressbar
        self.progressbar.setValue(v)

    def statusUpdate(self, m):
        # slot for showing a message in the statusbar.
        self.statusbar.showMessage(m)

    def closeEvent(self, event):
        import time
        quit_msg = "About to Exit the program, do you want to save the current settings? "
        reply = QMessageBox.question(self, 'Message', 
                        quit_msg, QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            print('saving the image to db')
            self.saveimagedb_sig.emit()
            event.accept()
        elif reply == QMessageBox.No:
            event.ignore()

class WorkArea(pg.GraphicsObject):
    """
    This class is meant for displaying a colored zone in the field view, wihout listing it in the field render list
    """

    def __init__(self, parent, width, height, color):
        pg.GraphicsObject.__init__(self)
        # pg.QtCore.qInstallMsgHandler(lambda *args: None)
        # // draw 100 mm x100 mm square behind the samples
        self.width = width
        self.height = height
        self.color = color
        self._parent = parent
        self.update_object()

    def update_color(self, color):
        self.color = color
        self.update_object()

    def update_size(self, width, height):
        self.width = width
        self.height = height

    def update_object(self):
        self.pic = QtGui.QPicture()
        p = QtGui.QPainter(self.pic)
        p.setPen(pg.mkPen(QtGui.QColor(self.color)))
        p.setBrush(QtGui.QBrush(QtGui.QColor(self.color)))
        p.drawRect(QtCore.QRectF(0, 0, self.width, self.height))
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.pic)

    def boundingRect(self):
        return pg.QtCore.QRectF(self.pic.boundingRect())


class ImageBufferInfo(QtCore.QObject):
    statusMessage_sig = Signal(str)
    progressUpdate_sig = Signal(float)
    logMessage_sig = Signal(dict)

    def __init__(self, parent, img_backup_path):
        super(ImageBufferInfo, self).__init__()
        self.attrList = []
        self._parent = parent
        self.img_backup_path = img_backup_path

    def load_imagedb(self, xml_path, exclude_file_list=[]):
        tempAttrList = load_im_xml(xml_path, exclude_file=exclude_file_list,
                                   progressbar=None)
        self.logMessage_sig.emit({"type": "info",
                                  "message": "imagedb data files loaded into project.",
                                  "class": "ImportDialog"})
        for d in tempAttrList[::-1]:
            self.load_qi(d)
        self._parent.tbl_render_order.resizeRowsToContents()
        self._parent.tbl_render_order.setColumnWidth(0, 55)
        return tempAttrList

    def load_qi(self, d, showGUI=False):
        """
        This loads an image based on a dictionary of keys
        :param showGUI:
        :param d: the dictionary. It must have a Path, Center, Size, and Name keys as minimum
        :return:
        """
        import os
        if os.path.exists(d['Path']):
            if os.path.splitext(d['Path'])[-1].lower() == ".bmp":
                qi = QtGui.QPixmap(d['Path'])
            elif os.path.splitext(d['Path'])[-1].lower() == ".jpg" or os.path.splitext(d['Path'])[
                -1].lower() == ".jpeg":
                qi = QtGui.QPixmap(d['Path'])
            elif os.path.splitext(d['Path'])[-1].lower() == ".png":
                qi = QtGui.QPixmap(d['Path'])
                if not qi:
                    # // try to copy the png to bmp and import it. This is a workaround as the PNG is actually a BMP
                    import shutil
                    new_file = os.path.join(os.path.splitext(d['Path'])[0] + ".bmp")
                    shutil.copy(d['Path'], new_file)
                    qi = QtGui.QPixmap()
                    ret = qi.load(new_file, format="BMP")
            elif os.path.splitext(d['Path'])[-1].lower() == ".tif" or os.path.splitext(d['Path'])[
                -1].lower() == ".tiff":
                qi = QtGui.QPixmap(d['Path'])
            else:
                QtCore.qDebug("Image format not supported")
                qi = None
                # self.statusMessage_sig.emit("Image {} format not supported.".format(os.path.splitext(d['Path'])[-1].lower()))
        else:
            QtCore.qDebug("Path not found")
            # self.statusMessage_sig.emit("{} does not exist.".format(d['Path']))
            qi = None

        if qi:
            # // load the center and size keys into the dict using the aspect reatio tool (if needed)
            if ("Center" not in d.keys()):
                if ("Outline" not in d.keys()):
                    # // set the center to the current center in the workspace
                    d["Center"] = [0] * 3
                    d["Center"][0] = self._parent.X_controller_travel//2
                    d["Center"][1] = self._parent.Y_controller_travel//2
                    d["Center"][2] = 0
                else:
                    # // calculate the center based on the outline
                    d["Center"] = [0] * 3
                    d["Center"][0] = abs(d["Outline"][1] - d["Outline"][0]) / 2.0 + d["Outline"][0]
                    d["Center"][1] = abs(d["Outline"][3] - d["Outline"][2]) / 2.0 + d["Outline"][2]
                    d["Center"][2] = abs(d["Outline"][5] - d["Outline"][4]) / 2.0 + d["Outline"][4]

            if ("Size" not in d.keys()) and ("Outline" not in d.keys()):
                d["Size"] = (qi.size().width(), qi.size().height(), 1)

            if "Outline" not in d.keys():
                if "Center" in d.keys() and "Size" in d.keys():
                    d["Outline"] = [0] * 6
                    d["Outline"][0] = d["Center"][0] - d["Size"][0] / 2
                    d["Outline"][1] = d["Center"][0] + d["Size"][0] / 2
                    d["Outline"][2] = d["Center"][1] - d["Size"][1] / 2
                    d["Outline"][3] = d["Center"][1] + d["Size"][1] / 2
                    if len(d["Size"]) > 2 and len(d["Center"]) > 2:
                        d["Outline"][4] = d["Center"][2] - d["Size"][2] / 2
                        d["Outline"][5] = d["Center"][2] + d["Size"][2] / 2

            aspect_ratio = []
            aspect_ratio.append(d["Outline"][1] - d["Outline"][0])
            aspect_ratio.append(d["Outline"][3] - d["Outline"][2])
            aspect_ratio.append(d["Outline"][5] - d["Outline"][4])
            aspect_ratio[0] /= qi.size().width()
            aspect_ratio[1] /= qi.size().height()
            aspect_ratio[2] /= 1
            d.update({'AspectRatio': aspect_ratio})

            if "Opacity" in d.keys():
                opa = float(d["Opacity"])
                if opa > 100:
                    opa = 100
                elif opa < 0:
                    opa = 0
            else:
                opa = 100

            # // calculate the outline based on the center and size
            img = ImageBufferObject(width=d['Size'][0], height=d['Size'][1],
                                    pos=(d["Outline"][0], d["Outline"][2]), pixmap=qi, opacity=opa,
                                    attrs=d)
            self._parent.field.addItem(img)
            # // reset the scale for rotation
            s = list(img._scale)
            if s[0] == 0:
                s[0] = 1
            if s[1] == 0:
                s[1] = 1

            # img.scale(1 / s[0], 1 / s[1])
            tr = QtGui.QTransform()
            tr.scale(1 / s[0], 1 / s[1])
            img.setTransform(tr)

            if not "Rotation" in d.keys():
                d["Rotation"] = 0
            # img.rotate(d['Rotation'])
            img.setRotation(d["Rotation"])
            # img.scale(s[0], s[1])
            tr = QtGui.QTransform()
            tr.scale(s[0], s[1])
            img.setTransform(tr)

            # // apply coordinate transformation for rotation in the XY plane
            
            v = rotatePoint(centerPoint=d['Center'], point=[d["Outline"][0], d["Outline"][2]],
                            angle=d['Rotation'])
            img.setPos(pg.Point(v[0], v[1]))
            self._parent.field.autoRange(padding=0.02)
            self._parent.field_img.insert(0, img)
            # // set current image in the field view
            self._parent.update_field_current = img
            # // attach the label to the image
            img.loc = d

            # // add to the renderlist
            rowPosition = 0
            self._parent.tbl_render_order.insertRow(rowPosition)

            cb = QtWidgets.QTableWidgetItem()
            cb.setBackground(QtGui.QColor("#368AD4"))
            cb.setCheckState(QtCore.Qt.CheckState.Checked)
            self._parent.tbl_render_order.setItem(rowPosition, 0, cb)
            self._parent.field_list.insert(0, img.loc)
            self._parent.tbl_render_order.itemClicked.connect(lambda item: self._parent.on_table_order_clicked(item))

            sb = QtWidgets.QSpinBox()
            sb.setRange(0, 100)
            sb.setValue(int(opa))
            sb.editingFinished.connect(self.update_opacity)
            self._parent.tbl_render_order.setCellWidget(rowPosition, 1, sb)
            sb.loc = img.loc

            p = QtWidgets.QTableWidgetItem(d["Name"])
            p.loc = d

            self._parent.tbl_render_order.setItem(rowPosition, 2, p)

            if showGUI:
                # geometry_window = geometry_dialog(parent=self._parent, attrs=d,
                                                #   shape=(qi.size().width() * 10, qi.size().height() * 10, 1),
                                                #   axis=(0, 1, 2))
                geometry_window = geometry_dialog(parent=self._parent, attrs=d,
                                                  shape=(qi.size().width(), qi.size().height(), 1),
                                                  axis=(0, 1, 2))
                geometry_window.show()
                ret = geometry_window.exec_()
                # // add the image to the imagebuffer
            # self._parent.update_geo()
            # self.addImgBackup(self._parent.attrs_geo)
            img.loc = d
            self.addImgBackup(d)

    def update_opacity(self):
        sb = self.sender()
        if sb.loc in self._parent.field_list:
            ind = self._parent.field_list.index(sb.loc)
            self._parent.field_img[ind].setOpacity(sb.value() / 100.0)
            sb.loc["Opacity"] = sb.value()
            self.writeImgBackup()

    def addImgBackup(self, dict_image):
        # // function to add a dataset to current backup file
        self.attrList.append(dict_image)
        self.writeImgBackup()

    def writeImgBackup(self, path = None):
        # // flushes the current image buffer to the backup file
        from export_module import write_im_xml
        if path == None:
            write_im_xml(self.img_backup_path, self.attrList, distributed=True)
        else:
            write_im_xml(path, self.attrList, distributed=True)

    def updateImgBackup(self, newDict):
        """
        Function to update a ImageBufferObject in the backup file
        :return:
        """
        # //  search every image to remove from active list
        for i, n in enumerate(self.attrList):
            # // search for name match
            if n["Path"] == newDict["Path"]:
                # // found match
                self.attrList[i] = newDict

        # // update the backup file by refreshing
        self.writeImgBackup()

    def removeImgBackup(self, d):
        """
        Function to remove a file from the current backup file
        :param d:
        :return:
        """
        # //  search every image to remove from active list
        for i, n in enumerate(self.attrList):
            # // search for name match
            if n["Path"] == d["Path"]:
                # // found match
                del self.attrList[i]

        # // remove from the backup file by refreshing
        self.writeImgBackup()

    def writeimagedb(self, xml_path):
        # // save the image buffer to a specified location
        #settings = QtCore.QSettings(self._parent._parent.__appStore__, QtCore.QSettings.IniFormat)
        settings = self._parent.settings_object
        if settings.value('Hardware/CPUthreading') == '1':
            def onDataReady(obj_result):
                self._parent.thread_func.quit()

            def func(self, progressSignal):
                from export_module import write_im_xml
                write_im_xml = write_im_xml(xml_path, self.attrList, distributed=False)
                # // copy all images to the export folder
                import shutil
                l = len(self.attrList)
                for i, d in enumerate(self.attrList):
                    import os
                    if os.path.exists(d['Path']):
                        shutil.copy2(d['Path'], os.path.dirname(xml_path))
                    else:
                        QtCore.qDebug("Path not found")
                    progressSignal.emit(((i + 1) / l) * 100)
                    # self._parent._parent.progressbar.setValue(((i + 1) / l) * 100)
                return self

            self._parent.thread_func = QtCore.QThread(self._parent)

            class Worker(QtCore.QObject):
                finished = Signal()
                dataReady = Signal(object)
                progressSignal = Signal(float)

                def __init__(self, parent, func, *args, **kwargs):
                    # QtCore.QObject.__init__(self, *args, **kwargs)
                    super(Worker, self).__init__()
                    self.func = func
                    self.args = args
                    self.kwargs = kwargs

                @QtCore.Slot(str, object)
                def run_func(self):
                    r = func(*self.args, progressSignal=self.progressSignal, **self.kwargs)
                    self.dataReady.emit(r)
                    self.finished.emit()

            self.obj = Worker(self, func, self)
            self.obj.moveToThread(self._parent.thread_func)
            self.obj.progressSignal.connect(self._parent._parent.progressUpdate)
            self.obj.dataReady.connect(onDataReady)

            self._parent.thread_func.started.connect(self.obj.run_func)
            self._parent.thread_func.start()
        else:
            pass

    def recallImgBackup(self):
        import os
        # // recall the previous imagedb if the path is valid
        if self.img_backup_path:
            if os.path.exists(self.img_backup_path):
                dict_list = self.load_imagedb(xml_path=self.img_backup_path)
                # self.attrList = dict_list


class ImageBufferObject(pg.GraphicsObject):
    """
    This class is meant for displaying a picture in the field view, without listing it in the field render list
    """

    def __init__(self, width=None, height=None, pos=(0, 0), rot=0, Visible=True, pixmap=None, attrs={}, opacity=100):
        pg.GraphicsObject.__init__(self)
        self.width = width
        self.height = height
        self.axisOrder = 'row-major'
        self._scale = [1, 1]
        self.attrs = attrs
        if pixmap is not None:
            self.setPixmap(pixmap)
            self.pixmap = pixmap

        if width is not None and height is None:
            s = float(width) / self.pixmap.width()
            self.scale(s, s)
            self._scale = (s, s)
        elif height is not None and width is None:
            s = float(height) / self.pixmap.height()
            self.scale(s, s)
            self._scale = (s, s)
        elif width is not None and height is not None and (self.pixmap.width() > 0) and (self.pixmap.height() > 0):
            self._scale = (float(width) / self.pixmap.width(), float(height) / self.pixmap.height())
            # self.scale(self._scale[0], self._scale[1])
            tr = QtGui.QTransform()
            tr.scale(self._scale[0], self._scale[1])
            self.setTransform(tr)
        else:
            self._scale = (width, height)
            self.scale(self._scale[0], self._scale[1])
            

        self.setOpacity(opacity / 100)
        self.border = None

    def setPixmap(self, pixmap):
        self.pixmap = pixmap
        self.update()

    def paint(self, p, *args):
        p.setRenderHint(p.Antialiasing)
        p.drawPixmap(0, 0, self.pixmap)
        if self.border is not None:
            p.setPen(self.border)
            p.drawRect(self.boundingRect())

    def boundingRect(self):
        return QtCore.QRectF(self.pixmap.rect())

    def setBorder(self, b):
        self.border = fn.mkPen(b)
        self.update()

    def mapToData(self, obj):
        tr = self.inverseDataTransform()
        return tr.map(obj)

    def inverseDataTransform(self):
        """Return the transform that maps from this image's local coordinate
        system to its input array.

        See dataTransform() for more information.
        """
        tr = QtGui.QTransform()
        if self.axisOrder == 'row-major':
            # transpose
            tr.scale(1, -1)
            tr.rotate(-90)
        return tr

class TableWidgetDragRows(QtWidgets.QTableWidget):
    def __init__(self, parent, *args, **kwargs):
        super(TableWidgetDragRows, self).__init__(parent)
        self.imageBuffer = None
        self._parent = parent
        self.copy_image_to_project_idx = 0
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.horizontalHeader().setStretchLastSection(True)
        self.installEventFilter(self)

    def setMultiRowSel(self, selection):
        self.setSelectionMode(self.MultiSelection)
        for i in selection:
            self.selectRow(i)
        self.setSelectionMode(self.ExtendedSelection)
        # self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

    def dropEvent(self, event):
        if not event.isAccepted() and event.source() == self:
            drop_row = self.drop_on(event)

            rows = sorted(set(item.row() for item in self.selectedItems()))
            rows_to_move = []
            for row_index in rows:
                row_data = []
                for column_index in range(self.columnCount()):
                    if column_index == 1:
                        row_data += [self.cellWidget(row_index, 1)]
                        # self.removeCellWidget(row_index,1)
                    else:
                        row_data += [QtWidgets.QTableWidgetItem(self.item(row_index, column_index))]
                rows_to_move += [row_data]

            for i, row in enumerate(rows_to_move):
                row[2].loc = self.item(rows[i], 2).loc

            # //increase row count
            # self.setRowCount(self.rowCount()+1)

            # // reorganize field list by inserting the new rows
            for row_index in reversed(rows):
                self._parent.field_list.insert(drop_row, self._parent.field_list.pop(row_index))
                self._parent.field_img.insert(drop_row, self._parent.field_img.pop(row_index))

            for row_index, data in enumerate(rows_to_move):
                row_index += drop_row
                self.insertRow(row_index)
                for column_index, column_data in enumerate(data):
                    if column_index == 1:
                        self.setCellWidget(row_index, 1, column_data)
                    else:
                        self.setItem(row_index, column_index, column_data)

                self.setRowHeight(row_index, 20)
                self.setRowHeight(drop_row, 20)

            for row_index in range(len(rows_to_move)):
                self.item(drop_row + row_index, 0).setSelected(True)
                self.item(drop_row + row_index, 2).setSelected(True)

            for row_index in reversed(rows):
                if row_index < drop_row:
                    self.removeRow(row_index)
                else:
                    self.removeRow(row_index + len(rows_to_move))

            self.field_order_update()
            event.accept()

        super().dropEvent(event)

    def drop_on(self, event):
        index = self.indexAt(event.pos())
        if not index.isValid():
            return self.rowCount()

        return index.row() + 1 if self.is_below(event.pos(), index) else index.row()

    def is_below(self, pos, index):
        rect = self.visualRect(index)
        margin = 2
        if pos.y() - rect.top() < margin:
            return False
        elif rect.bottom() - pos.y() < margin:
            return True
        # noinspection PyTypeChecker
        return rect.contains(pos, True) and not (
                    int(self.model().flags(index)) & QtCore.Qt.ItemIsDropEnabled) and pos.y() >= rect.center().y()

    def field_order_update(self):
        # // reset the Z-order based on the field_img order
        p = len(self._parent.field_img)
        for i, k in enumerate(self._parent.field_img):
            k.setZValue(p - i)

    def eventFilter(self, widget, event):
        if (event.type() == QtCore.QEvent.KeyPress and widget is self):
            if event.key() == QtCore.Qt.Key_Delete:
                self.deleteSelection()
            elif event.key() == QtCore.Qt.Key_Home:
                self.zorder_up_full()
                return True
            elif event.key() == QtCore.Qt.Key_End:
                self.zorder_down_full()
                return True
            elif event.key() == QtCore.Qt.Key_Up:
                self.zorder_up()
                return True
            elif event.key() == QtCore.Qt.Key_Down:
                self.zorder_down()
                return True

        return QtWidgets.QWidget.eventFilter(self, widget, event)

    def zorder_up_full(self):
        # // change the render order
        row = self.currentRow()
        if row > 0:
            field_i = self._parent.field_list.index(self.item(row, 2).loc)
            # // move item completly upwards in the table
            column = 1
            self.insertRow(0)
            self.setRowHeight(0, 20)
            for i in range(self.columnCount()):
                if i == 1:
                    # // moving the progressbar
                    pb = self.cellWidget(row + 1, 1)
                    self.setCellWidget(0, 1, pb)
                else:
                    self.setItem(0, i, self.takeItem(row + 1, i))
                    self.setCurrentCell(0, column)
            self.removeRow(row + 1)
            # // mirror change in field_img and field_list
            temp = self._parent.field_img[field_i]
            del self._parent.field_img[field_i]
            self._parent.field_img.insert(0, temp)
            temp = self._parent.field_list[field_i]
            del self._parent.field_list[field_i]
            self._parent.field_list.insert(0, temp)
        self.field_order_update()

    def zorder_up(self):
        # // change the render order
        row = self.currentRow()
        if row > 0:
            field_i = self._parent.field_list.index(self.item(row, 2).loc)
            # // move item upwards in the table
            column = 1
            self.insertRow(row - 1)
            for i in range(self.columnCount()):
                if i == 1:
                    # // moving the progressbar
                    pb = self.cellWidget(row + 1, 1)
                    self.setCellWidget(row - 1, 1, pb)
                else:
                    self.setItem(row - 1, i, self.takeItem(row + 1, i))
                    self.setCurrentCell(row - 1, column)
            self.setRowHeight(row, 20)
            self.setRowHeight(row - 1, 20)
            self.removeRow(row + 1)
            # // mirror change in field_img and field_list
            self._parent.field_img[field_i], self._parent.field_img[field_i - 1] = self._parent.field_img[field_i - 1], \
                                                                                   self._parent.field_img[field_i]
            self._parent.field_list[field_i], self._parent.field_list[field_i - 1] = self._parent.field_list[
                                                                                         field_i - 1], \
                                                                                     self._parent.field_list[field_i]
        self.field_order_update()

    def zorder_down(self):
        # // change the render order
        row = self.currentRow()
        if row < self.rowCount() - 1:
            field_i = self._parent.field_list.index(self.item(row, 2).loc)
            # // move item downwards in the table
            column = 1
            self.insertRow(row + 2)
            for i in range(self.columnCount()):
                if i == 1:
                    # // moving the progressbar
                    pb = self.cellWidget(row, 1)
                    self.setCellWidget(row + 2, 1, pb)
                else:
                    self.setItem(row + 2, i, self.takeItem(row, i))
                    self.setCurrentCell(row + 2, column)
            self.removeRow(row)
            # // mirror change in field_img and field_list
            self._parent.field_img[field_i], self._parent.field_img[field_i + 1] = self._parent.field_img[field_i + 1], \
                                                                                   self._parent.field_img[field_i]
            self._parent.field_list[field_i], self._parent.field_list[field_i + 1] = self._parent.field_list[
                                                                                         field_i + 1], \
                                                                                     self._parent.field_list[field_i]
            self.resizeRowsToContents()
        self.field_order_update()

    def zorder_down_full(self):
        # // change the render order
        row = self.currentRow()
        if row < self.rowCount() - 1:
            field_i = self._parent.field_list.index(self.item(row, 2).loc)
            # // move item downwards in the table
            column = 1
            final_row = self.rowCount()
            self.insertRow(final_row)
            self.setRowHeight(0, 20)
            for i in range(self.columnCount()):
                if i == 1:
                    # // moving the progressbar
                    pb = self.cellWidget(row, 1)
                    self.setCellWidget(final_row, 1, pb)
                else:
                    self.setItem(final_row, i, self.takeItem(row, i))
                    self.setCurrentCell(final_row, column)
            self.removeRow(row)
            # // mirror change in._parent field_img and._parent field_list
            temp = self._parent.field_img[field_i]
            del self._parent.field_img[field_i]
            self._parent.field_img.append(temp)
            temp = self._parent.field_list[field_i]
            del self._parent.field_list[field_i]
            self._parent.field_list.append(temp)
        self.resizeRowsToContents()
        self.field_order_update()

    def deleteSelection(self):
        items = self.selectedItems()
        if len(items) == 0:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       """<p>No image selected in the render table. Therefore, no image can be deleted from the render table.<p>""")
            return None

        # // list the location to remove
        locToRemove = []
        for k in items:
            if k.column() == 2:
                loc = self.item(k.row(), 2).loc
                locToRemove.append(loc)

        # // remove the locations in the list
        for loc in locToRemove:
            if isinstance(loc, dict):
                # // delete from table and update render order
                self._parent.field_remove(loc)

    def contextMenuEvent(self, event):
        if self.columnAt(event.pos().x()) == 2:
            a = self.item(self.rowAt(event.pos().y()), 2).loc
            if isinstance(a, dict):
                self.copy_image_to_project_idx = self._parent.field_list.index(a)
                self.menu = QtWidgets.QMenu(self)
                copy_action = QtGui.QAction('Remove Image', self.deleteSelection)
                copy_action.triggered.connect(self.remove)
                self.menu.addAction(copy_action)

                # copy_action = QtGui.QAction('Add Image Recognition Zone', self)
                # copy_action.triggered.connect(self.set_selection_zone)
                # self.menu.addAction(copy_action)
                self.menu.popup(QtGui.QCursor.pos())


def main():
    import qdarkstyle
    app = QApplication(sys.argv)
    myWin = WorkSpace()
    myWin.showMaximized() 
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    myWin.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

