# -*- coding: utf-8 -*-
import os
import pyqtgraph as pg
import re
import time

from PySide6 import QtCore, QtGui, QtWidgets
import numpy as np
from PySide6.QtCore import QObject
from PySide6.QtGui import QPen
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QAbstractButton
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRectF
from PySide6.QtGui import QLinearGradient, QGradient
from PySide6.QtCore import Qt, QSize

def check_true(v):
    if isinstance(v, bool):
        return v
    elif isinstance(v, int):
        if v <= 0:
            return False
        else:
            return True
    elif isinstance(v, str):
        if v.lower() == "true" or v == "1":
            return True
        else:
            return False
    elif isinstance(v, bytes):
        if v.lower() == b"true" or v == b"1":
            return True
        else:
            return False
    else:
        if v:
            return True
        else:
            return False



class CopyTable(QtWidgets.QTableWidget):
    """
    Class contains the methods that creates a table from which can be copied
    Contains also other utilities associated with interactive tables.
    """

    def __init__(self, parent=None):
        super(CopyTable, self).__init__(parent)
        self._parent = parent
        self.setAlternatingRowColors(True)

    def paste(self):
        s = self._parent.clip.text()
        rows = s.split("\n")
        selected = self.selectedRanges()
        rc = 1
        if selected:
            for r in range(selected[0].topRow(), selected[0].bottomRow() + 1):
                if (len(rows) > rc):
                    v = rows[rc].split("\t")
                    cc = 1
                    for c in range(selected[0].leftColumn(), selected[0].rightColumn() + 1):
                        if (len(v) > cc):
                            self.item(r,c).setText(v[cc])
                        cc+=1
                rc+=1
        else:
            for r in range(0, self.rowCount()):
                if (len(rows) > rc):
                    v = rows[rc].split("\t")
                    cc = 1
                    for c in range(0, self.columnCount()):
                        if (len(v) > cc):
                            self.item(r,c).setText(v[cc])
                        cc+=1
                rc+=1

    def copy(self):
        selected = self.selectedRanges()
        if selected:
            if self.horizontalHeaderItem(0):
                s = '\t' + "\t".join([str(self.horizontalHeaderItem(i).text()) for i in
                                      range(selected[0].leftColumn(), selected[0].rightColumn() + 1)])
            else:
                s = '\t' + "\t".join([str(i) for i in range(selected[0].leftColumn(), selected[0].rightColumn() + 1)])
            s = s + '\n'
            for r in range(selected[0].topRow(), selected[0].bottomRow() + 1):
                if self.verticalHeaderItem(r):
                    s += self.verticalHeaderItem(r).text() + '\t'
                else:
                    s += str(r) + '\t'
                for c in range(selected[0].leftColumn(), selected[0].rightColumn() + 1):
                    try:
                        item_text = str(self.item(r, c).text())
                        if item_text.endswith("\n"):
                            item_text = item_text[:-2]
                        s += item_text + "\t"
                    except AttributeError:
                        s += "\t"
                s = s[:-1] + "\n"  # eliminate last '\t'
            self._parent.clip.setText(s)
        else:
            if self.horizontalHeaderItem(0):
                s = '\t' + "\t".join([str(self.horizontalHeaderItem(i).text()) for i in range(0, self.columnCount())])
            else:
                s = '\t' + "\t".join([str(i) for i in range(0, self.columnCount())])
            s = s + '\n'

            for r in range(0, self.rowCount()):
                if self.verticalHeaderItem(r):
                    s += self.verticalHeaderItem(r).text() + '\t'
                else:
                    s += str(r) + '\t'
                for c in range(0, self.columnCount()):
                    try:
                        item_text = str(self.item(r, c).text())
                        if item_text.endswith("\n"):
                            item_text = item_text[:-2]
                        s += item_text + "\t"
                    except AttributeError:
                        s += "\t"
                s = s[:-1] + "\n"  # eliminate last '\t'
            self._parent.clip.setText(s)


class TableWidgetDragRows(CopyTable):
    rowsSwitched_sig = QtCore.Signal(int, int)
    dropEventCompleted_sig = QtCore.Signal()

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent = parent
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        # // this lock mode can temporary lock all drag movement
        self.locked_status = False
        self.installEventFilter(self)

    def setMultiRowSel(self, selection):
        """
        allow multiple rows to be selected
        :param selection:
        :return:
        """
        self.setSelectionMode(self.MultiSelection)
        for i in selection:
            self.selectRow(i)
        self.setSelectionMode(self.ExtendedSelection)

    def dropEvent(self, event):
        """
        This code runs when a line is dragged and dropped onto the table
        :param event:
        :return:
        """
        if self.locked_status:
            return

        if not event.isAccepted() and event.source() == self:
            drop_row = self.drop_on(event)
            rows = sorted(set(item.row() for item in self.selectedItems()))
            rows_to_move = []
            for row_index in rows:
                row_data = []
                for column_index in range(self.columnCount()):
                    row_data += [QtWidgets.QTableWidgetItem(self.item(row_index, column_index))]
                rows_to_move += [row_data]

            # for i, row in enumerate(rows_to_move):
            #     row[2].loc = self.item(rows[i], 2).loc

            # %increase row count
            # self.setRowCount(self.rowCount()+1)

            # // reorganize field list by inserting the new rows
            for row_index in reversed(rows):
                self.rowsSwitched_sig.emit(drop_row, row_index)
                # self._parent.field_list.insert(drop_row, self._parent.field_list.pop(row_index))

            for row_index, data in enumerate(rows_to_move):
                row_index += drop_row
                self.insertRow(row_index)
                for column_index, column_data in enumerate(data):
                    self.setItem(row_index, column_index, column_data)

                self.setRowHeight(row_index, 20)
                self.setRowHeight(drop_row, 20)

            for row_index in range(len(rows_to_move)):
                self.item(drop_row + row_index, 0).setSelected(True)
                # self.item(drop_row + row_index, 1).setSelected(True)

            for row_index in reversed(rows):
                if row_index < drop_row:
                    self.removeRow(row_index)
                else:
                    self.removeRow(row_index + len(rows_to_move))

            event.accept()
            self.dropEventCompleted_sig.emit()

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


class LoadingAnimationDialog(QtWidgets.QDialog):
    """
    Class for displaying loading animations
    """

    def __init__(self, parent):
        super(LoadingAnimationDialog, self).__init__(parent)

    def start_loading_animation(self):
        self.loading_movie = QtGui.QMovie(":/icon/loading.gif")
        self.loading_movie.setScaledSize(QtCore.QSize(60, 60))
        self.loading_label = QtGui.QLabel()
        self.loading_label.setMovie(self.loading_movie)
        self.loading_label.setAlignment(QtCore.Qt.AlignCenter)
        self.loading_movie.start()

    def stop_loading_animation(self):
        self.loading_movie.stop()
        # QtCore.qDebug("stop animation")
        self.loading_movie.setParent(None)
        self.loading_movie.deleteLater()
        self.loading_label.setParent(None)
        self.loading_label.deleteLater()


class DialogWithCheckBox(QtWidgets.QMessageBox):
    """
    Shows a dialog with a checkbox
    """

    def __init__(self, parent=None):
        """

        :param parent:
        """
        super(DialogWithCheckBox, self).__init__()
        self.checkbox = QtGui.QCheckBox()
        # // Access the Layout of the MessageBox to add the Checkbox
        layout = self.layout()
        layout.addWidget(self.checkbox, 2, 2)

    def exec_(self, *args, **kwargs):
        """
        Override the exec_ method so you can return the value of the checkbox
        """
        return QtWidgets.QMessageBox.exec_(self, *args, **kwargs), self.checkbox.isChecked()


