# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'workspace_widget_new2.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QLineEdit,
    QSizePolicy, QSpacerItem, QToolButton, QVBoxLayout,
    QWidget)

from ui.terminal_widget import TerminalWidget
import resources_icon_library

class Ui_workspace_widget(object):
    def setupUi(self, workspace_widget):
        if not workspace_widget.objectName():
            workspace_widget.setObjectName(u"workspace_widget")
        workspace_widget.resize(990, 631)
        self.gridLayout_3 = QGridLayout(workspace_widget)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gb_list = QFrame(workspace_widget)
        self.gb_list.setObjectName(u"gb_list")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.gb_list.sizePolicy().hasHeightForWidth())
        self.gb_list.setSizePolicy(sizePolicy)
        self.gb_list.setMinimumSize(QSize(0, 0))
        self.gb_list.setMaximumSize(QSize(16777215, 160))
        self.gridLayout_2 = QGridLayout(self.gb_list)
        self.gridLayout_2.setSpacing(2)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer, 0, 5, 1, 1)

        self.bt_removeMenu = QToolButton(self.gb_list)
        self.bt_removeMenu.setObjectName(u"bt_removeMenu")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.bt_removeMenu.sizePolicy().hasHeightForWidth())
        self.bt_removeMenu.setSizePolicy(sizePolicy1)
        self.bt_removeMenu.setMinimumSize(QSize(0, 0))
        self.bt_removeMenu.setMaximumSize(QSize(123890, 123890))
        icon = QIcon()
        icon.addFile(u":/FileSystem/icons/FileSystem/close_file_128x128.png", QSize(), QIcon.Normal, QIcon.Off)
        self.bt_removeMenu.setIcon(icon)
        self.bt_removeMenu.setIconSize(QSize(36, 36))
        self.bt_removeMenu.setPopupMode(QToolButton.InstantPopup)
        self.bt_removeMenu.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.gridLayout_2.addWidget(self.bt_removeMenu, 0, 4, 1, 1)

        self.bt_imageMenu = QToolButton(self.gb_list)
        self.bt_imageMenu.setObjectName(u"bt_imageMenu")
        sizePolicy1.setHeightForWidth(self.bt_imageMenu.sizePolicy().hasHeightForWidth())
        self.bt_imageMenu.setSizePolicy(sizePolicy1)
        self.bt_imageMenu.setMinimumSize(QSize(0, 0))
        self.bt_imageMenu.setMaximumSize(QSize(123890, 123890))
        icon1 = QIcon()
        icon1.addFile(u":/FileSystem/icons/FileSystem/new_file_128x128.png", QSize(), QIcon.Normal, QIcon.Off)
        self.bt_imageMenu.setIcon(icon1)
        self.bt_imageMenu.setIconSize(QSize(36, 36))
        self.bt_imageMenu.setPopupMode(QToolButton.InstantPopup)
        self.bt_imageMenu.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.bt_imageMenu.setAutoRaise(False)

        self.gridLayout_2.addWidget(self.bt_imageMenu, 0, 2, 1, 1)

        self.bt_alignMenu = QToolButton(self.gb_list)
        self.bt_alignMenu.setObjectName(u"bt_alignMenu")
        sizePolicy1.setHeightForWidth(self.bt_alignMenu.sizePolicy().hasHeightForWidth())
        self.bt_alignMenu.setSizePolicy(sizePolicy1)
        self.bt_alignMenu.setMinimumSize(QSize(0, 0))
        self.bt_alignMenu.setMaximumSize(QSize(123890, 123890))
        icon2 = QIcon()
        icon2.addFile(u":/Viewing/icons/Viewing/coordinates_128x128.png", QSize(), QIcon.Normal, QIcon.Off)
        self.bt_alignMenu.setIcon(icon2)
        self.bt_alignMenu.setIconSize(QSize(36, 36))
        self.bt_alignMenu.setPopupMode(QToolButton.InstantPopup)
        self.bt_alignMenu.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.gridLayout_2.addWidget(self.bt_alignMenu, 0, 1, 1, 1)


        self.gridLayout_3.addWidget(self.gb_list, 0, 0, 1, 1)

        self.frame = QFrame(workspace_widget)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.gridLayout = QGridLayout(self.frame)
        self.gridLayout.setObjectName(u"gridLayout")
        self.graphics_layout = QGridLayout()
        self.graphics_layout.setSpacing(2)
        self.graphics_layout.setObjectName(u"graphics_layout")

        self.gridLayout.addLayout(self.graphics_layout, 0, 0, 1, 1)

        self.grid_alignment = QGridLayout()
        self.grid_alignment.setObjectName(u"grid_alignment")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.gridLayout_renderTable = QGridLayout()
        self.gridLayout_renderTable.setSpacing(0)
        self.gridLayout_renderTable.setObjectName(u"gridLayout_renderTable")

        self.verticalLayout.addLayout(self.gridLayout_renderTable)

        self.lineEdit_coords = QLineEdit(self.frame)
        self.lineEdit_coords.setObjectName(u"lineEdit_coords")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lineEdit_coords.sizePolicy().hasHeightForWidth())
        self.lineEdit_coords.setSizePolicy(sizePolicy2)

        self.verticalLayout.addWidget(self.lineEdit_coords)

        self.widget_terminal = TerminalWidget(self.frame)
        self.widget_terminal.setObjectName(u"widget_terminal")

        self.verticalLayout.addWidget(self.widget_terminal)


        self.grid_alignment.addLayout(self.verticalLayout, 0, 0, 1, 1)


        self.gridLayout.addLayout(self.grid_alignment, 0, 1, 1, 1)


        self.gridLayout_3.addWidget(self.frame, 1, 0, 1, 1)


        self.retranslateUi(workspace_widget)

        QMetaObject.connectSlotsByName(workspace_widget)
    # setupUi

    def retranslateUi(self, workspace_widget):
        workspace_widget.setWindowTitle(QCoreApplication.translate("workspace_widget", u"DESY Image Registration", None))
        self.bt_removeMenu.setText(QCoreApplication.translate("workspace_widget", u"Remove ", None))
        self.bt_imageMenu.setText(QCoreApplication.translate("workspace_widget", u"Import", None))
        self.bt_alignMenu.setText(QCoreApplication.translate("workspace_widget", u"Align", None))
    # retranslateUi

