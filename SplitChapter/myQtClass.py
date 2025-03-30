# -*- coding: utf-8 -*-

from pyqt_import import QtCore, QtGui, QtWidgets
from turn_number import cn_turn_arab
import res_rc
import os,re

SHEETS_NUM_LIMIT = 9  #CSS模板数量限制

class MyLineEdit(QtWidgets.QLineEdit):
    def __init__(self,parent = None):
        super().__init__(parent)
        self.url = ''
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and len(event.mimeData().urls()) == 1:
            url = event.mimeData().urls()[0].url()
            if url.lower().endswith('.txt'):
                self.url = url
                event.accept()
        else:
            event.ignore()
    def dropEvent(self, event):
        super().dropEvent(event)
        open_filedialog = self.parent().parent().open_filedialog
        open_filedialog(self.url[8:])


class LinkCss(QtWidgets.QListWidget):
    def __init__(self, parent = None):

        super().__init__(parent)
        self.MainForm = self.parent().parent()
        self.stylesheet = self.MainForm.stylesheet
        self.checked_sheet = self.MainForm.checked_sheet
        self.existed_template_num = []
        self.items_limit = SHEETS_NUM_LIMIT #子项数量限制
        self.addition_item = None
        self.curdir = os.path.dirname(__file__)
        self.create_items()

        if len(self.stylesheet) < self.items_limit:
            self.setup_addition_item()
        self.itemClicked.connect(self.add_stylesheet)
    def create_items(self):
        for sheet_name in self.stylesheet:
            item = QtWidgets.QListWidgetItem(self)
            ischecked = False
            if sheet_name in self.checked_sheet:
                ischecked = True
            self.setup_item_widget(sheet_name,item,ischecked)
            self.addItem(item)


    def setup_item_widget(self,sheet_name,item:QtWidgets.QListWidgetItem,ischecked = False):
        Form = QtWidgets.QWidget()
        Form.resize(166, 40)
        transparent_background = "background-color:rgba(255, 255, 255, 0);"
        horizontalLayout = QtWidgets.QHBoxLayout(Form)
        horizontalLayout.setContentsMargins(0,0,4,0)
        horizontalLayout.setSpacing(5)
        checkBox = QtWidgets.QCheckBox(Form)
        if ischecked:
            checkBox.setChecked(True)
        horizontalLayout.addWidget(checkBox)
        lineEdit = ClickedLineEdit(Form)
        lineEdit.setMinimumSize(QtCore.QSize(60, 0))
        lineEdit.setText(sheet_name)
        lineEdit.setStyleSheet(transparent_background)
        lineEdit.setFrame(False)
        checkBox.lineEdit = lineEdit #将lineEdit绑定到checkBox上，方便查找
        horizontalLayout.addWidget(lineEdit)
        spacerItem = QtWidgets.QSpacerItem(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        horizontalLayout.addItem(spacerItem)
        del_button = QtWidgets.QToolButton(Form)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icon/delete.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        del_button.setIcon(icon)
        del_button.setMaximumWidth(15)
        del_button.setStyleSheet(transparent_background)
        del_button.setIconSize(QtCore.QSize(10, 12))
        del_button.clicked.connect(lambda x:self.delete_stylesheet(lineEdit.text(),item))
        horizontalLayout.addWidget(del_button)
        Form.setLayout(horizontalLayout)
        self.setItemWidget(item,Form)

    def setup_addition_item(self):
        item = QtWidgets.QListWidgetItem(self)
        item.setText("添加")
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(True)
        item.setFont(font)
        item.setTextAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        self.addItem(item)
        self.addition_item = item

    def add_stylesheet(self,item):
        if item != self.addition_item:
            return

        for i in range(1,self.items_limit + 1):
            if 'Style000' + str(i) not in self.stylesheet:
                break
        sheet_name = 'Style000' + str(i)
        self.stylesheet.append(sheet_name)
        self.takeItem(self.currentRow())
        self.addition_item = None
        item = QtWidgets.QListWidgetItem(self)
        self.setup_item_widget(sheet_name,item)
        if len(self.stylesheet) < self.items_limit:
            self.setup_addition_item()
        
    def delete_stylesheet(self,sheet_name,item):
        self.stylesheet.remove(sheet_name)
        self.setCurrentItem(item)
        self.takeItem(self.currentRow())
        if len(self.stylesheet) == self.items_limit - 1:
            self.setup_addition_item()

    # 返回所有选中的sheetname
    def get_checked_sheetnames(self):
        checked_sheetnames = []
        all_checkbox = self.findChildren(QtWidgets.QCheckBox)
        for checkbox in all_checkbox:
            if checkbox.isChecked():
                checked_sheetnames.append(checkbox.lineEdit.text())
        return checked_sheetnames

    def get_all_pseudoItems(self):
        #直接的子项不方便访问checkbox和lineEdit,用checkbox绑定lineEdit作为一个伪子项。
        pseudoItems = all_checkbox = self.findChildren(QtWidgets.QCheckBox)
        return pseudoItems

class ClickedLineEdit(QtWidgets.QLineEdit):
    def __init__(self,parent = None):
        super().__init__(parent)
        self.set_validator()
        self.old_text = ""
        self.setReadOnly(True)
        #编辑框按下Enter键时发送信号
        self.returnPressed.connect(self.new_sheetname)
    def set_validator(self):
        reg = QtCore.QRegExp('[a-zA-Z0-9\-]{0,30}')
        validator = QtGui.QRegExpValidator()
        validator.setRegExp(reg)
        self.setValidator(validator)
    #双击输入框解锁编辑，将输入框内容备份到self.old_text
    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent):
        self.old_text = self.text()
        self.setReadOnly(False)
    #失去焦点事件
    def focusOutEvent(self, event: QtGui.QFocusEvent):
        self.new_sheetname()
    #更新样式表名
    def new_sheetname(self):
        if self.old_text == "":
            return
        #锁定输入框
        self.setReadOnly(True)
        old_name = self.old_text
        new_name = self.text()
        #处理输入名为空
        if new_name == "":
            self.setText(old_name)
            self.old_text = ''
            return
        if old_name != new_name:
            cssview = self.parent().parent().parent()
            #处理同名情况
            if new_name in cssview.MainForm.stylesheet:
                self.setText(old_name)
                self.old_text = ''
                return
            #更新 stylesheet 字典
            index = cssview.MainForm.stylesheet.index(old_name)
            cssview.MainForm.stylesheet[index] = new_name
        #输入框失去焦点时一定要清空 self.old_text ，避免一些BUG。
        self.old_text = ''

class LenLineEdit(QtWidgets.QLineEdit):
    def __init__(self,parent = None):
        super().__init__(parent)
    def focusOutEvent(self,event):
        super().focusOutEvent(event)
        self.parent().reflash_highlight()

class PreviewTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.mainform = self.parent().parent()
        self.seq_check_switch = False
        self.title_numbers = [] # 储存每行标题包含数字、级别、标题地址
    def mouseDoubleClickEvent(self, e):
        x = e.x()
        y = e.y() 
        pos = QtCore.QPoint(x,y)#获得鼠标相对于控件的坐标
        item = self.itemAt(pos)
        self.setCurrentItem(item)
        if not item:
            return
        font = QtGui.QFont()
        row = item.data(2, 0)
        if row in self.mainform.ignore_title['ignore_position']:
            font.setStrikeOut(False)
            item.setFont(0,font)
            self.mainform.ignore_title['ignore_position'].remove(row)
        else:
            font.setStrikeOut(True)
            item.setFont(0,font)
            self.mainform.ignore_title['ignore_position'].append(row)
    
    def seq_check(self):
        if self.seq_check_switch == False:
            self.seq_check_switch = True
            self.parent().seqcheck_button.setText('ON')
        else:
            self.seq_check_switch = False
            self.parent().seqcheck_button.setText('OFF')
            for length,item in self.parent().len_collection:
                item.setForeground(0,QtGui.QColor(0,0,0))
            for length,item in self.parent().highlight_collection:
                item.setForeground(0,QtGui.QColor(255,0,0))
            return

        if self.title_numbers == []:
            titles_count = len(self.parent().titles)
            if titles_count == 0: #没有标题则返回
                return
            re_number = re.compile(r'\d+|[一二两三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟萬〇零]+')

            for i in range(titles_count): #初始化 self.title_numbers
                title = self.parent().titles[i][1]
                #中文数字转阿拉伯数字
                numstr = re_number.search(title)
                if numstr is not None:
                    if numstr[0] > 'A':
                        number = cn_turn_arab(numstr.group())
                    else:
                        number = int(numstr.group())
                    if not isinstance(number,int):
                        number = -1
                    else:
                        pass
                else:
                    number = -1

                self.title_numbers.append((number,                              #数字
                                           self.parent().titles[i][0],          #级别
                                           self.parent().len_collection[i][1])) #item

        title_numbers = self.title_numbers
        titles_count = len(title_numbers)
        title_numbers.sort(key=lambda x:x[1],reverse=False)

        color = ['#FF0033','#FF3300','#FF0099','#990099','#990099','#990099','#990099']
        for i in range(1,titles_count):
            num = title_numbers[i][0]
            lv = title_numbers[i][1]
            last_num = title_numbers[i-1][0]
            last_lv = title_numbers[i-1][1]
            item = title_numbers[i][2]
            item.setForeground(0,QtGui.QColor('#005500'))
            if lv != last_lv:
                color.pop(0)
                continue
            if num > 0 and last_num >= 0 and num - last_num == 1: #章节
                continue
            elif num == 0 or num == 1:
                continue
            else:
                item.setForeground(0,QtGui.QColor(color[0]))
        item = title_numbers[0][2]
        item.setForeground(0,QtGui.QColor('#005500'))