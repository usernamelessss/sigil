# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'other.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QListWidgetItem,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

from myQtClass import LinkCss
import res_rc

class Ui_ohter(object):
    def setupUi(self, ohter):
        if not ohter.objectName():
            ohter.setObjectName(u"ohter")
        ohter.setWindowModality(Qt.ApplicationModal)
        ohter.resize(265, 99)
        ohter.setWindowTitle(u"\u5176\u4ed6\u8bbe\u7f6e")
        icon = QIcon()
        icon.addFile(u":/icon/plugin.png", QSize(), QIcon.Normal, QIcon.Off)
        ohter.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(ohter)
        self.verticalLayout.setSpacing(5)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(5, 5, 5, 5)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.import_css = QCheckBox(ohter)
        self.import_css.setObjectName(u"import_css")

        self.horizontalLayout.addWidget(self.import_css)

        self.link_css = LinkCss(ohter)
        self.link_css.setObjectName(u"link_css")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.link_css.sizePolicy().hasHeightForWidth())
        self.link_css.setSizePolicy(sizePolicy)
        self.link_css.setMinimumSize(QSize(146, 40))

        self.horizontalLayout.addWidget(self.link_css)

        self.horizontalLayout.setStretch(1, 1)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.add_img_code = QCheckBox(ohter)
        self.add_img_code.setObjectName(u"add_img_code")

        self.horizontalLayout_2.addWidget(self.add_img_code)

        self.mod_code = QPushButton(ohter)
        self.mod_code.setObjectName(u"mod_code")
        self.mod_code.setMinimumSize(QSize(146, 0))

        self.horizontalLayout_2.addWidget(self.mod_code)

        self.horizontalLayout_2.setStretch(1, 1)

        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.retranslateUi(ohter)
        self.mod_code.clicked.connect(ohter.open_img_code)

        QMetaObject.connectSlotsByName(ohter)
    # setupUi

    def retranslateUi(self, ohter):
        self.import_css.setText(QCoreApplication.translate("ohter", u"\u94fe\u63a5\u5230\u6837\u5f0f\u8868", None))
        self.add_img_code.setText(QCoreApplication.translate("ohter", u"\u5bfc\u5165\u9996\u56fe\u4ee3\u7801", None))
        self.mod_code.setText(QCoreApplication.translate("ohter", u"\u4fee\u6539\u4ee3\u7801", None))
        pass
    # retranslateUi

