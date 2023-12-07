# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'field_registration.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QDialog,
    QDialogButtonBox, QGridLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpacerItem, QWidget)

class Ui_field_registration(object):
    def setupUi(self, field_registration):
        if not field_registration.objectName():
            field_registration.setObjectName(u"field_registration")
        field_registration.resize(576, 224)
        self.gridLayout = QGridLayout(field_registration)
        self.gridLayout.setObjectName(u"gridLayout")
        self.bt_add_ref = QPushButton(field_registration)
        self.bt_add_ref.setObjectName(u"bt_add_ref")
        self.bt_add_ref.setMaximumSize(QSize(25, 16777215))

        self.gridLayout.addWidget(self.bt_add_ref, 2, 2, 1, 1)

        self.ent_target = QLineEdit(field_registration)
        self.ent_target.setObjectName(u"ent_target")

        self.gridLayout.addWidget(self.ent_target, 1, 1, 1, 1)

        self.ent_ref = QLineEdit(field_registration)
        self.ent_ref.setObjectName(u"ent_ref")

        self.gridLayout.addWidget(self.ent_ref, 2, 1, 1, 1)

        self.buttonBox = QDialogButtonBox(field_registration)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.gridLayout.addWidget(self.buttonBox, 7, 0, 1, 3)

        self.bt_add_target = QPushButton(field_registration)
        self.bt_add_target.setObjectName(u"bt_add_target")
        self.bt_add_target.setMaximumSize(QSize(25, 16777215))

        self.gridLayout.addWidget(self.bt_add_target, 1, 2, 1, 1)

        self.label_2 = QLabel(field_registration)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)

        self.label = QLabel(field_registration)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.cb_translation = QCheckBox(field_registration)
        self.cb_translation.setObjectName(u"cb_translation")
        self.cb_translation.setChecked(True)

        self.gridLayout_2.addWidget(self.cb_translation, 0, 0, 1, 1)

        self.cb_rotation = QCheckBox(field_registration)
        self.cb_rotation.setObjectName(u"cb_rotation")
        self.cb_rotation.setChecked(False)

        self.gridLayout_2.addWidget(self.cb_rotation, 0, 1, 1, 1)

        self.bt_registration = QPushButton(field_registration)
        self.bt_registration.setObjectName(u"bt_registration")

        self.gridLayout_2.addWidget(self.bt_registration, 0, 2, 1, 1)


        self.gridLayout.addLayout(self.gridLayout_2, 6, 0, 1, 3)

        self.label_3 = QLabel(field_registration)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 0, 0, 1, 3)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 8, 0, 1, 1)


        self.retranslateUi(field_registration)
        self.buttonBox.accepted.connect(field_registration.accept)
        self.buttonBox.rejected.connect(field_registration.reject)

        QMetaObject.connectSlotsByName(field_registration)
    # setupUi

    def retranslateUi(self, field_registration):
        field_registration.setWindowTitle(QCoreApplication.translate("field_registration", u"Workspace registration", None))
        self.bt_add_ref.setText(QCoreApplication.translate("field_registration", u"+", None))
        self.bt_add_target.setText(QCoreApplication.translate("field_registration", u"+", None))
        self.label_2.setText(QCoreApplication.translate("field_registration", u"Reference image", None))
        self.label.setText(QCoreApplication.translate("field_registration", u"Target image ", None))
        self.cb_translation.setText(QCoreApplication.translate("field_registration", u"Translation", None))
        self.cb_rotation.setText(QCoreApplication.translate("field_registration", u"Rotation", None))
        self.bt_registration.setText(QCoreApplication.translate("field_registration", u"Register", None))
        self.label_3.setText(QCoreApplication.translate("field_registration", u"Attention: The reference image must contain the target image for the\n"
" algorithm to function properly.", None))
    # retranslateUi

