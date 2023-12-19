# -*- coding: utf-8 -*-
import os
from pathlib import Path
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtWidgets import  QAbstractItemView
from spatial_registration_module import rotatePoint
import pyqtgraph as pg
import numpy as np
import math
from util import qt_image_to_array, PandasModel
import trackpy as tp
import pandas as pd
import copy
from spatial_registration_module import rotatePoint

class particle_widget_wrapper(object):
    """
    Module contains tool to change the position and rotation of the image in the workspace.
    """

    def __init__(self):
        self.attrs_par = None
        self.shape_par = None
        self.markers = None
        self.markers_clicked = None
        self.axis_par = (0,1,2)
        #self.particle_info = pd.DataFrame({}, columns = ['y', 'x', 'mass', 'size', 'ecc', 'signal', 'raw_mass', 'ep', 'frame'])
        # // disable registration mark tab
        # // enable field view
        self.setEnabled(True)
        #self.init_pandas_model()
        
    def init_pandas_model(self, data, table_view_widget_name='tableView_particle_info'):
        #disable_all_tabs_but_one(self, tab_widget_name, tab_indx)
        self.pandas_model = PandasModel(data = data, tableviewer = getattr(self, table_view_widget_name), main_gui=self)
        getattr(self, table_view_widget_name).setModel(self.pandas_model)
        getattr(self, table_view_widget_name).resizeColumnsToContents()
        getattr(self, table_view_widget_name).setSelectionBehavior(QAbstractItemView.SelectRows)
        getattr(self, table_view_widget_name).horizontalHeader().setStretchLastSection(True)

    #callback whenever switch to a different image, being called once
    def update_par(self):
        self.attrs_par = self.update_field_current.loc
        self.shape_par = (self.update_field_current.width, self.update_field_current.height, 1)
        # % get length from outline
        if not 'Outline' in self.attrs_par.keys():
            self.attrs_par['Outline'] = [0, self.shape_par[self.axis_geo[0]], 0, self.shape_par[self.axis_geo[1]], 0,
                                     self.shape_par[self.axis_geo[2]]]

        if not "Rotation" in self.attrs_par.keys():
            self.attrs_par['Rotation'] = 0

        # // display the selected image in the center
        # self.autoRange(items=[self.update_field_current])

    def extract_kwargs_for_locating_particle(self):
        kwargs = {
            'diameter': int(self.lineEdit_diameter.text()),
            'minmass': float(self.lineEdit_minmass.text()),
            'maxsize': float(self.lineEdit_maxsize.text()),
            'invert': self.comboBox_invert.currentText()=='True',
            'noise_size': float(self.doubleSpinBox_noise_size.value()),
            'threshold': float(self.lineEdit_threshold.text())
        }
        return kwargs

    def connect_slots_par(self):
        self.pushButton_locate.clicked.connect(self.track_particle)
        self.pushButton_annotate_particle.clicked.connect(self.annotate)
        self.tableView_particle_info.clicked.connect(self.annotate_clicked_row)

    def track_particle(self):
        np_array_gray = qt_image_to_array(self.update_field_current.pixmap.toImage())
        particle_info = tp.locate(np_array_gray, **self.extract_kwargs_for_locating_particle()).round(1)
        self.init_pandas_model(particle_info)

    def annotate(self):
        if self.markers!=None:
            self.field.removeItem(self.markers)
        if self.markers_clicked!=None:
            self.field.removeItem(self.markers_clicked)        
        self.markers = pg.ScatterPlotItem(size=10, pen=pg.mkPen(255, 0, 255, 255), brush=pg.mkBrush(255, 255, 255, 120))
        spots = zip(self.pandas_model._data.x, self.pandas_model._data.y, self.pandas_model._data.mass)
        spots = [{'pos':self.scale_rotate_and_translate([x,y]), 'data': value, 'symbol':'+'} for x, y, value in spots]
        self.markers.addPoints(spots)
        self.field.addItem(self.markers)

    def annotate_clicked_row(self, index=None):
        if self.markers_clicked!=None:
            self.field.removeItem(self.markers_clicked)        
        x = self.pandas_model._data.x.to_list()[index.row()]
        y = self.pandas_model._data.y.to_list()[index.row()]
        mass = self.pandas_model._data.mass.to_list()[index.row()]
        self.markers_clicked = pg.ScatterPlotItem(size=10, pen=pg.mkPen(0, 255, 0, 255), brush=pg.mkBrush(255, 255, 255, 120))
        spots = [{'pos':self.scale_rotate_and_translate([x,y]), 'data': mass, 'symbol':'+'}]
        self.markers_clicked.addPoints(spots)
        self.field.addItem(self.markers_clicked)

    def scale_rotate_and_translate(self, pot):
        return np.array(rotatePoint([0,0], np.array(pot) * np.array(self.update_field_current._scale), self.update_field_current.loc['Rotation'])) + np.array(self.update_field_current.pos())