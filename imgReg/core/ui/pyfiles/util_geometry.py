# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'util_geometry.ui'
##
## Created by: Qt User Interface Compiler version 6.2.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QDial,
    QDialog, QDialogButtonBox, QGridLayout, QHeaderView,
    QLabel, QLineEdit, QRadioButton, QSizePolicy,
    QSpacerItem, QTabWidget, QTableWidget, QTableWidgetItem,
    QWidget)

class Ui_util_geometry(object):
    def setupUi(self, util_geometry):
        if not util_geometry.objectName():
            util_geometry.setObjectName(u"util_geometry")
        util_geometry.resize(363, 529)
        self.gridLayout = QGridLayout(util_geometry)
        self.gridLayout.setSpacing(2)
        self.gridLayout.setContentsMargins(4, 4, 4, 4)
        self.gridLayout.setObjectName(u"gridLayout")
        self.buttonBox_aspect = QDialogButtonBox(util_geometry)
        self.buttonBox_aspect.setObjectName(u"buttonBox_aspect")
        self.buttonBox_aspect.setOrientation(Qt.Horizontal)
        self.buttonBox_aspect.setStandardButtons(QDialogButtonBox.Apply|QDialogButtonBox.Cancel|QDialogButtonBox.Ok|QDialogButtonBox.Reset)

        self.gridLayout.addWidget(self.buttonBox_aspect, 0, 0, 1, 1)

        self.tabWidget = QTabWidget(util_geometry)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setEnabled(True)
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.gridLayout_2 = QGridLayout(self.tab)
#ifndef Q_OS_MAC
        self.gridLayout_2.setSpacing(6)
#endif
        self.gridLayout_2.setContentsMargins(4, 4, 4, 4)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setSpacing(2)
        self.gridLayout_4.setContentsMargins(4, 4, 4, 4)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.rb_outline = QRadioButton(self.tab)
        self.rb_outline.setObjectName(u"rb_outline")
        self.rb_outline.setChecked(False)

        self.gridLayout_4.addWidget(self.rb_outline, 1, 0, 1, 1)

        self.rb_totdim = QRadioButton(self.tab)
        self.rb_totdim.setObjectName(u"rb_totdim")

        self.gridLayout_4.addWidget(self.rb_totdim, 1, 1, 1, 1)

        self.rb_pixdim = QRadioButton(self.tab)
        self.rb_pixdim.setObjectName(u"rb_pixdim")
        self.rb_pixdim.setChecked(True)

        self.gridLayout_4.addWidget(self.rb_pixdim, 0, 0, 1, 1)

        self.rb_center = QRadioButton(self.tab)
        self.rb_center.setObjectName(u"rb_center")

        self.gridLayout_4.addWidget(self.rb_center, 0, 1, 1, 1)

        self.rb_rotation = QRadioButton(self.tab)
        self.rb_rotation.setObjectName(u"rb_rotation")

        self.gridLayout_4.addWidget(self.rb_rotation, 0, 2, 1, 1)


        self.gridLayout_2.addLayout(self.gridLayout_4, 2, 0, 1, 3)

        self.label_9 = QLabel(self.tab)
        self.label_9.setObjectName(u"label_9")

        self.gridLayout_2.addWidget(self.label_9, 1, 0, 1, 3)

        self.label_8 = QLabel(self.tab)
        self.label_8.setObjectName(u"label_8")

        self.gridLayout_2.addWidget(self.label_8, 0, 0, 1, 1)

        self.cb_mirror = QCheckBox(self.tab)
        self.cb_mirror.setObjectName(u"cb_mirror")
        self.cb_mirror.setEnabled(False)

        self.gridLayout_2.addWidget(self.cb_mirror, 7, 1, 1, 1)

        self.lbl_rot = QLabel(self.tab)
        self.lbl_rot.setObjectName(u"lbl_rot")
        self.lbl_rot.setAlignment(Qt.AlignCenter)

        self.gridLayout_2.addWidget(self.lbl_rot, 14, 1, 1, 2)

        self.label_5 = QLabel(self.tab)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout_2.addWidget(self.label_5, 11, 0, 1, 1)

        self.label_3 = QLabel(self.tab)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_2.addWidget(self.label_3, 14, 0, 1, 1)

        self.ent_unitz = QLineEdit(self.tab)
        self.ent_unitz.setObjectName(u"ent_unitz")
        self.ent_unitz.setEnabled(False)

        self.gridLayout_2.addWidget(self.ent_unitz, 5, 2, 1, 1)

        self.lbl_box_z = QLabel(self.tab)
        self.lbl_box_z.setObjectName(u"lbl_box_z")

        self.gridLayout_2.addWidget(self.lbl_box_z, 5, 0, 1, 1)

        self.label_2 = QLabel(self.tab)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_2.addWidget(self.label_2, 10, 0, 1, 1)

        self.lbl_aspect_ratio = QLabel(self.tab)
        self.lbl_aspect_ratio.setObjectName(u"lbl_aspect_ratio")
        self.lbl_aspect_ratio.setAlignment(Qt.AlignCenter)

        self.gridLayout_2.addWidget(self.lbl_aspect_ratio, 12, 1, 1, 2)

        self.lbl_box_y = QLabel(self.tab)
        self.lbl_box_y.setObjectName(u"lbl_box_y")

        self.gridLayout_2.addWidget(self.lbl_box_y, 4, 0, 1, 1)

        self.label_7 = QLabel(self.tab)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout_2.addWidget(self.label_7, 13, 0, 1, 1)

        self.lbl_center_pos = QLabel(self.tab)
        self.lbl_center_pos.setObjectName(u"lbl_center_pos")
        self.lbl_center_pos.setAlignment(Qt.AlignCenter)

        self.gridLayout_2.addWidget(self.lbl_center_pos, 10, 1, 1, 2)

        self.lbl_outline = QLabel(self.tab)
        self.lbl_outline.setObjectName(u"lbl_outline")
        self.lbl_outline.setAlignment(Qt.AlignCenter)

        self.gridLayout_2.addWidget(self.lbl_outline, 13, 1, 1, 2)

        self.label_4 = QLabel(self.tab)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout_2.addWidget(self.label_4, 9, 0, 1, 1)

        self.lbl_pixdim = QLabel(self.tab)
        self.lbl_pixdim.setObjectName(u"lbl_pixdim")
        self.lbl_pixdim.setAlignment(Qt.AlignCenter)

        self.gridLayout_2.addWidget(self.lbl_pixdim, 8, 1, 1, 2)

        self.lbl_pixcount = QLabel(self.tab)
        self.lbl_pixcount.setObjectName(u"lbl_pixcount")
        self.lbl_pixcount.setAlignment(Qt.AlignCenter)

        self.gridLayout_2.addWidget(self.lbl_pixcount, 9, 1, 1, 2)

        self.ent_dimz = QLineEdit(self.tab)
        self.ent_dimz.setObjectName(u"ent_dimz")

        self.gridLayout_2.addWidget(self.ent_dimz, 5, 1, 1, 1)

        self.ent_dimy = QLineEdit(self.tab)
        self.ent_dimy.setObjectName(u"ent_dimy")

        self.gridLayout_2.addWidget(self.ent_dimy, 4, 1, 1, 1)

        self.cb_flip = QCheckBox(self.tab)
        self.cb_flip.setObjectName(u"cb_flip")
        self.cb_flip.setEnabled(False)

        self.gridLayout_2.addWidget(self.cb_flip, 7, 2, 1, 1)

        self.lbl_totdim = QLabel(self.tab)
        self.lbl_totdim.setObjectName(u"lbl_totdim")
        self.lbl_totdim.setAlignment(Qt.AlignCenter)

        self.gridLayout_2.addWidget(self.lbl_totdim, 11, 1, 1, 2)

        self.ent_unity = QLineEdit(self.tab)
        self.ent_unity.setObjectName(u"ent_unity")
        self.ent_unity.setEnabled(False)

        self.gridLayout_2.addWidget(self.ent_unity, 4, 2, 1, 1)

        self.ent_unitx = QLineEdit(self.tab)
        self.ent_unitx.setObjectName(u"ent_unitx")
        self.ent_unitx.setEnabled(False)

        self.gridLayout_2.addWidget(self.ent_unitx, 3, 2, 1, 1)

        self.label_6 = QLabel(self.tab)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_2.addWidget(self.label_6, 8, 0, 1, 1)

        self.ent_dimx = QLineEdit(self.tab)
        self.ent_dimx.setObjectName(u"ent_dimx")
        self.ent_dimx.setMaxLength(32767)

        self.gridLayout_2.addWidget(self.ent_dimx, 3, 1, 1, 1)

        self.label = QLabel(self.tab)
        self.label.setObjectName(u"label")

        self.gridLayout_2.addWidget(self.label, 12, 0, 1, 1)

        self.lbl_box_x = QLabel(self.tab)
        self.lbl_box_x.setObjectName(u"lbl_box_x")

        self.gridLayout_2.addWidget(self.lbl_box_x, 3, 0, 1, 1)

        self.cb_aspect_ratio = QCheckBox(self.tab)
        self.cb_aspect_ratio.setObjectName(u"cb_aspect_ratio")
        self.cb_aspect_ratio.setChecked(True)

        self.gridLayout_2.addWidget(self.cb_aspect_ratio, 7, 0, 1, 1)

        self.dial_rotation = QDial(self.tab)
        self.dial_rotation.setObjectName(u"dial_rotation")
        self.dial_rotation.setMinimumSize(QSize(100, 100))
        self.dial_rotation.setMaximum(360)
        self.dial_rotation.setSingleStep(10)
        self.dial_rotation.setPageStep(45)
        self.dial_rotation.setWrapping(True)
        self.dial_rotation.setNotchesVisible(True)

        self.gridLayout_2.addWidget(self.dial_rotation, 6, 0, 1, 3)

        self.tabWidget.addTab(self.tab, "")
        self.tab_marks = QWidget()
        self.tab_marks.setObjectName(u"tab_marks")
        self.gridLayout_3 = QGridLayout(self.tab_marks)
        self.gridLayout_3.setSpacing(2)
        self.gridLayout_3.setContentsMargins(4, 4, 4, 4)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.lbl_alignment = QLabel(self.tab_marks)
        self.lbl_alignment.setObjectName(u"lbl_alignment")

        self.gridLayout_3.addWidget(self.lbl_alignment, 0, 0, 1, 1)

        self.tbl_align = QTableWidget(self.tab_marks)
        if (self.tbl_align.columnCount() < 2):
            self.tbl_align.setColumnCount(2)
        __qtablewidgetitem = QTableWidgetItem()
        self.tbl_align.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tbl_align.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        if (self.tbl_align.rowCount() < 2):
            self.tbl_align.setRowCount(2)
        self.tbl_align.setObjectName(u"tbl_align")
        self.tbl_align.setRowCount(2)
        self.tbl_align.horizontalHeader().setCascadingSectionResizes(False)
        self.tbl_align.horizontalHeader().setMinimumSectionSize(300)
        self.tbl_align.horizontalHeader().setProperty("showSortIndicator", False)
        self.tbl_align.horizontalHeader().setStretchLastSection(True)

        self.gridLayout_3.addWidget(self.tbl_align, 1, 0, 1, 1)

        self.tabWidget.addTab(self.tab_marks, "")

        self.gridLayout.addWidget(self.tabWidget, 4, 0, 1, 2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 5, 0, 1, 1)


        self.retranslateUi(util_geometry)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(util_geometry)
    # setupUi

    def retranslateUi(self, util_geometry):
        util_geometry.setWindowTitle(QCoreApplication.translate("util_geometry", u"Position and size", None))
        self.rb_outline.setText(QCoreApplication.translate("util_geometry", u"Outline", None))
        self.rb_totdim.setText(QCoreApplication.translate("util_geometry", u"Total size", None))
        self.rb_pixdim.setText(QCoreApplication.translate("util_geometry", u"Pixel dimensions", None))
        self.rb_center.setText(QCoreApplication.translate("util_geometry", u"Center", None))
        self.rb_rotation.setText(QCoreApplication.translate("util_geometry", u"Rotation", None))
        self.label_9.setText(QCoreApplication.translate("util_geometry", u"Adjust the precise size and location of the image\n"
" by entering values (if known).", None))
        self.label_8.setText(QCoreApplication.translate("util_geometry", u"Image Size and Alignment", None))
        self.cb_mirror.setText(QCoreApplication.translate("util_geometry", u"Mirror", None))
        self.lbl_rot.setText(QCoreApplication.translate("util_geometry", u"0", None))
        self.label_5.setText(QCoreApplication.translate("util_geometry", u"Total size [\u00b5m]", None))
        self.label_3.setText(QCoreApplication.translate("util_geometry", u"Rotation [deg]", None))
        self.lbl_box_z.setText(QCoreApplication.translate("util_geometry", u"Pixel dimensions z [\u00b5m]", None))
        self.label_2.setText(QCoreApplication.translate("util_geometry", u"Center position [\u00b5m]", None))
        self.lbl_aspect_ratio.setText(QCoreApplication.translate("util_geometry", u"0,0,0", None))
        self.lbl_box_y.setText(QCoreApplication.translate("util_geometry", u"Pixel dimensions y [\u00b5m]", None))
        self.label_7.setText(QCoreApplication.translate("util_geometry", u"Outline", None))
        self.lbl_center_pos.setText(QCoreApplication.translate("util_geometry", u"0x0x0", None))
        self.lbl_outline.setText(QCoreApplication.translate("util_geometry", u"[0,0],[0,0],[0,0]", None))
        self.label_4.setText(QCoreApplication.translate("util_geometry", u"Pixel count", None))
        self.lbl_pixdim.setText(QCoreApplication.translate("util_geometry", u"0x0x0", None))
        self.lbl_pixcount.setText(QCoreApplication.translate("util_geometry", u"0x0x0", None))
        self.cb_flip.setText(QCoreApplication.translate("util_geometry", u"Flip", None))
        self.lbl_totdim.setText(QCoreApplication.translate("util_geometry", u"0x0x0", None))
        self.label_6.setText(QCoreApplication.translate("util_geometry", u"Pixel dimensions [\u00b5m]", None))
        self.ent_dimx.setInputMask("")
        self.label.setText(QCoreApplication.translate("util_geometry", u"Aspect ratio XY,XZ,YZ", None))
        self.lbl_box_x.setText(QCoreApplication.translate("util_geometry", u"Pixel dimensions x [\u00b5m]", None))
        self.cb_aspect_ratio.setText(QCoreApplication.translate("util_geometry", u"Lock aspect ratio XY", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("util_geometry", u"Alignment and Positioning", None))
        self.lbl_alignment.setText(QCoreApplication.translate("util_geometry", u"Placed Alignment Marks", None))
        ___qtablewidgetitem = self.tbl_align.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("util_geometry", u"Original Image Location [pix]", None));
        ___qtablewidgetitem1 = self.tbl_align.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("util_geometry", u"New Sample Position [mm]", None));
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_marks), QCoreApplication.translate("util_geometry", u"Alignment Marks", None))
    # retranslateUi

