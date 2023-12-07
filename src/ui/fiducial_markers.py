# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'fiducial_markers.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QGroupBox,
    QLabel, QPushButton, QSizePolicy, QWidget)
import ui.resources_icon_library_rc

class Ui_fiducial_markers(object):
    def setupUi(self, fiducial_markers):
        if not fiducial_markers.objectName():
            fiducial_markers.setObjectName(u"fiducial_markers")
        fiducial_markers.resize(1058, 284)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(fiducial_markers.sizePolicy().hasHeightForWidth())
        fiducial_markers.setSizePolicy(sizePolicy)
        fiducial_markers.setMaximumSize(QSize(16777215, 16777215))
        icon = QIcon()
        icon.addFile(u":/icon/Teledyne_r.png", QSize(), QIcon.Normal, QIcon.Off)
        fiducial_markers.setWindowIcon(icon)
        self.gridLayout = QGridLayout(fiducial_markers)
        self.gridLayout.setObjectName(u"gridLayout")
        self.lbl_general_info = QLabel(fiducial_markers)
        self.lbl_general_info.setObjectName(u"lbl_general_info")
        self.lbl_general_info.setMaximumSize(QSize(16777215, 50))
        self.lbl_general_info.setFrameShape(QFrame.Box)
        self.lbl_general_info.setWordWrap(True)

        self.gridLayout.addWidget(self.lbl_general_info, 2, 0, 1, 2)

        self.grid_actions = QGridLayout()
        self.grid_actions.setObjectName(u"grid_actions")
        self.bt_align = QPushButton(fiducial_markers)
        self.bt_align.setObjectName(u"bt_align")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.bt_align.sizePolicy().hasHeightForWidth())
        self.bt_align.setSizePolicy(sizePolicy1)
        self.bt_align.setMinimumSize(QSize(200, 0))
        icon1 = QIcon()
        icon1.addFile(u":/icon/registration.png", QSize(), QIcon.Normal, QIcon.Off)
        self.bt_align.setIcon(icon1)

        self.grid_actions.addWidget(self.bt_align, 0, 0, 1, 1)

        self.bt_reset = QPushButton(fiducial_markers)
        self.bt_reset.setObjectName(u"bt_reset")
        sizePolicy1.setHeightForWidth(self.bt_reset.sizePolicy().hasHeightForWidth())
        self.bt_reset.setSizePolicy(sizePolicy1)
        icon2 = QIcon()
        icon2.addFile(u":/icon/refresh.png", QSize(), QIcon.Normal, QIcon.Off)
        self.bt_reset.setIcon(icon2)

        self.grid_actions.addWidget(self.bt_reset, 1, 0, 1, 1)

        self.bt_close = QPushButton(fiducial_markers)
        self.bt_close.setObjectName(u"bt_close")
        sizePolicy1.setHeightForWidth(self.bt_close.sizePolicy().hasHeightForWidth())
        self.bt_close.setSizePolicy(sizePolicy1)
        icon3 = QIcon()
        icon3.addFile(u":/icon/remove_selected.png", QSize(), QIcon.Disabled, QIcon.On)
        self.bt_close.setIcon(icon3)

        self.grid_actions.addWidget(self.bt_close, 2, 0, 1, 1)


        self.gridLayout.addLayout(self.grid_actions, 2, 2, 4, 1)

        self.gb_image_info = QGroupBox(fiducial_markers)
        self.gb_image_info.setObjectName(u"gb_image_info")
        self.gb_image_info.setMaximumSize(QSize(16777215, 16777215))
        self.gridLayout_3 = QGridLayout(self.gb_image_info)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.lbl_image_tag = QLabel(self.gb_image_info)
        self.lbl_image_tag.setObjectName(u"lbl_image_tag")

        self.gridLayout_3.addWidget(self.lbl_image_tag, 0, 1, 1, 1)

        self.lbl_image_tag_info = QLabel(self.gb_image_info)
        self.lbl_image_tag_info.setObjectName(u"lbl_image_tag_info")

        self.gridLayout_3.addWidget(self.lbl_image_tag_info, 0, 0, 1, 1)


        self.gridLayout.addWidget(self.gb_image_info, 3, 0, 3, 1)

        self.gb_alignment_mark_table = QGroupBox(fiducial_markers)
        self.gb_alignment_mark_table.setObjectName(u"gb_alignment_mark_table")
        self.gb_alignment_mark_table.setMaximumSize(QSize(16777215, 16777215))
        self.gridLayout_4 = QGridLayout(self.gb_alignment_mark_table)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.grid_alignment_mark = QGridLayout()
        self.grid_alignment_mark.setSpacing(0)
        self.grid_alignment_mark.setObjectName(u"grid_alignment_mark")

        self.gridLayout_4.addLayout(self.grid_alignment_mark, 0, 0, 1, 1)


        self.gridLayout.addWidget(self.gb_alignment_mark_table, 3, 1, 3, 1)


        self.retranslateUi(fiducial_markers)

        QMetaObject.connectSlotsByName(fiducial_markers)
    # setupUi

    def retranslateUi(self, fiducial_markers):
        fiducial_markers.setWindowTitle(QCoreApplication.translate("fiducial_markers", u"Fiducial Markers", None))
        self.lbl_general_info.setText(QCoreApplication.translate("fiducial_markers", u"Use the Alignment Marks tool to place TWO sets of alignment marks on the image to be aligned. For the best results, use features which are as far apart as possible, for example the diagonal corners at the opposite sides. Note that it is not possible to place the first point outside the boundaries of the image. Click \"Apply\" to perform the alignment.", None))
        self.bt_align.setText(QCoreApplication.translate("fiducial_markers", u"Align", None))
        self.bt_reset.setText(QCoreApplication.translate("fiducial_markers", u"Reset", None))
        self.bt_close.setText(QCoreApplication.translate("fiducial_markers", u"Close", None))
        self.gb_image_info.setTitle(QCoreApplication.translate("fiducial_markers", u"Image information", None))
        self.lbl_image_tag.setText(QCoreApplication.translate("fiducial_markers", u"-", None))
        self.lbl_image_tag_info.setText(QCoreApplication.translate("fiducial_markers", u"Image to be aligned:", None))
        self.gb_alignment_mark_table.setTitle(QCoreApplication.translate("fiducial_markers", u"Placed Alignment Marks:", None))
    # retranslateUi

