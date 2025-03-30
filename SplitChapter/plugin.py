# -*- coding: utf-8 -*-

import configparser
import os
import re
import subprocess
import sys
import time
from html import unescape
from platform import system
from threading import Thread

from pyqt_import import QtCore, QtGui, QtWidgets, SIGIL_QT_MAJOR_VERSION, main_ui, treeview, other, edit_regexp

CHAPTERS = []  # [ text ]
TEXT = ''
BUILD = False
DEFAULT_REGEXPS = [
    "^\\s*第[一二三四五六七八九十零〇百千两]+卷.*$",
    "^\\s*第[一二三四五六七八九十零〇百千两]+部.*$",
    "^\\s*第[一二三四五六七八九十零〇百千两]+章.*$",
    "^\\s*第[一二三四五六七八九十零〇百千两]+回.*$",
    "^\\s*第[一二三四五六七八九十零〇百千两]+节.*$",
    "^\\s*第[一二三四五六七八九十零〇百千两]+集.*$",
    "^\\s*第\\d+卷.*$",
    "^\\s*第\\d+部.*$",
    "^\\s*第\\d+章.*$",
    "^\\s*第\\d+回.*$",
    "^\\s*第\\d+节.*$",
    "^\\s*第\\d+集.*$",
    "^\\s*卷[一二三四五六七八九十零〇]+.*$",
    "^\\s*(序[1-9言曲]?|(内容)?简介|后记|尾声)$",
    "^\\s*\\d+\\s*$",
    "^[一二三四五六七八九十〇]+$"
]


class ModConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr):
        # 重定义 ConfigParser 的 optionxform 函数，取消其 option 强制小写的特性。
        return optionstr


class MainForm(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainForm, self).__init__()
        self.ui = ui = main_ui.Ui_MainWindow()
        ui.setupUi(self)
        self.init_function()
        self.load_ini()
        self.centralwidget = self.centralWidget()
        self.path_input_line = self.ui.path_input_line
        self.ui.filename_rule_le.setText("Chapter0001")
        self.gridLayout = self.findChild(QtWidgets.QGridLayout)
        self.ruleBox_widget = {
            'lev_1': self.findChild(QtWidgets.QSpinBox, 'lev_1'),
            'l1_regexp': self.findChild(QtWidgets.QComboBox, 'l1_regexp'),
            'l1_split': self.findChild(QtWidgets.QCheckBox, 'l1_split')
        }
        for exp in self.preset_regexp:
            self.ruleBox_widget['l1_regexp'].addItem(exp)
        self.ruleBox_widget['l1_regexp'].setCurrentText('')
        self.ruleBox_count = 1  # 正则框的数量（包括空框）
        self.ignore_title = {'regexp': {}, 'ignore_position': []}  # 'regexp'键储存上一次匹配正则，'ignore_position'键储存待忽略标题位置。
        self.current_height = self.sizeHint().height()  # 因为调用sizeHint().height()的高度未必能及时反馈，所以用current_height来计算高度。
        self.inc_height = None
        self.setFixedHeight(self.current_height)

    def init_function(self):
        self.ui.template_btn.clicked.connect(self.mod_template)
        self.ui.open_btn.clicked.connect(self.open_filedialog)
        self.ui.add_rule_box_tool.clicked.connect(self.add_rule_box)
        self.ui.dec_rule_box_tool.clicked.connect(self.dec_rule_box)
        self.ui.edit_preset_regexp_tool.clicked.connect(self.edit_preset_regexp)
        self.ui.comfirm.clicked.connect(self.comfirmed)
        self.ui.preview_btn.clicked.connect(self.preview)
        self.ui.analysis_btn.clicked.connect(self.auto_analysis)
        self.ui.readme_lbl.clicked.connect(self.readme)

    def load_ini(self):

        conf = ModConfigParser()
        cfgpath = os.path.join(CURDIR, 'config.ini')

        if os.path.exists(cfgpath):
            conf.read(cfgpath, encoding="utf-8")
            try:
                self.ini_openpath = conf.get('ini_info', 'ini_path')
                self.highlight_len = conf.get('ini_info', 'highlight_len')
                self.preset_regexp = []
                regexp_items = conf.items('regexp')
                if regexp_items:
                    for op, regexp in regexp_items:
                        self.preset_regexp.append(regexp)
            except:
                self.default_ini()
        else:
            self.default_ini()

    def default_ini(self):
        self.ini_openpath = os.path.expanduser('~')
        self.preset_regexp = DEFAULT_REGEXPS
        self.highlight_len = '30'

    def open_filedialog(self, drop_path=None):
        if not drop_path:
            if SIGIL_QT_MAJOR_VERSION == 6:
                args = {"parent": self, "dir": self.ini_openpath, "filter": "*.txt"}
            elif SIGIL_QT_MAJOR_VERSION == 5:
                args = {"parent": self, "directory": self.ini_openpath, "filter": "*.txt"}
            file = QtWidgets.QFileDialog.getOpenFileName(**args)
            if not file[0]:
                return
            txt_path = file[0]
        else:
            txt_path = drop_path
        self.ini_openpath = os.path.dirname(txt_path)
        path_input_line = self.findChild(QtWidgets.QLineEdit, 'path_input_line')
        path_input_line.setText(txt_path)
        txt_process = Thread(target=read_text_threading, args=(txt_path,))
        txt_process.start()

    def comfirmed(self):
        settings = self.get_settings()
        if settings['txt_path'] and not settings['txt_path'].startswith('可'):
            self.settings = settings
            global BUILD
            BUILD = True
            QtCore.QCoreApplication.instance().quit()
        else:
            QtWidgets.QMessageBox.information(self, '警告', '文件路径不能为空，请输入文件路径！')

    def other_settings(self):
        self.other = Other(self)
        self.other.import_css.setChecked(int(self.is_import_css))
        self.other.add_img_code.setChecked(int(self.is_img_code))
        self.other.show()

    def mod_template(self):
        template_path = os.path.join(CURDIR, 'template/template.txt')
        startfile(template_path)

    def get_settings(self):
        settings = {}
        settings['txt_path'] = self.path_input_line.text()  # str
        settings['ruleBox_count'] = count = self.ruleBox_count  # int
        settings['lev'], settings['regexp'], settings['split'] = {}, {}, {}
        for i in range(1, count + 1):
            settings['lev']['lev_%d' % i] = self.ruleBox_widget['lev_%d' % i].value()  # int
            settings['regexp']['l%d_regexp' % i] = self.ruleBox_widget['l%d_regexp' % i].currentText()  # str
            settings['split']['l%d_split' % i] = self.ruleBox_widget['l%d_split' % i].isChecked()  # bool
        settings['ignore'] = self.ignore_title
        return settings

    def preview(self):
        settings = self.get_settings()
        if settings['txt_path'] == '' or settings['txt_path'].startswith('可'):
            QtWidgets.QMessageBox.information(self, '警告', '文件路径不能为空，请输入文件路径！')
            return
        else:
            ignore = False
            if self.ignore_title['regexp'] == settings['regexp']:
                if self.ignore_title['ignore_position'] != []:
                    ignore = True
            else:
                self.ignore_title['ignore_position'].clear()
            titles = split_text(settings, preview=True)
            self.view = TitleTree(self, titles, ignore)
            self.view.show()
            self.ignore_title['regexp'] = settings['regexp'].copy()

    def readme(self):
        template_path = os.path.join(CURDIR, 'readme.txt')
        startfile(template_path)

    def add_rule_box(self):

        if self.ruleBox_count >= 15:
            return
        self.ruleBox_count += 1
        order = self.ruleBox_count
        lev_box = QtWidgets.QSpinBox(self.centralwidget)
        lev_box.setStyleSheet("background-color:rgba(255, 255, 255, 0);")
        lev_box.setFrame(False)
        lev_box.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        lev_box.setSuffix("级标题")
        lev_box.setMinimum(1)
        lev_box.setMaximum(6)
        lev_box.setProperty("value", 2)
        lev_box.setObjectName("lev_%d" % order)
        self.gridLayout.addWidget(lev_box, order, 0, 1, 1)
        self.ruleBox_widget["lev_%d" % order] = lev_box

        regexp = QtWidgets.QComboBox(self.centralwidget)
        regexp.setEnabled(True)
        font = QtGui.QFont("SimSun", 9, 50)
        regexp.setFont(font)
        regexp.setAutoFillBackground(False)
        regexp.setEditable(True)
        regexp.setObjectName("l%d_regexp" % order)
        for reg in self.preset_regexp:
            regexp.addItem(reg)
        regexp.setCurrentText("")
        self.gridLayout.addWidget(regexp, order, 1, 1, 1)
        self.ruleBox_widget["l%d_regexp" % order] = regexp

        page_split = QtWidgets.QCheckBox(self.centralwidget)
        page_split.setChecked(True)
        page_split.setObjectName("l%d_split" % order)
        self.gridLayout.addWidget(page_split, order, 2, 1, 1, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.ruleBox_widget["l%d_split" % order] = page_split
        if self.inc_height is None:
            # 增加的高度 = 网格布局第二行单元格高度 + 布局单元格的垂直间距
            self.inc_height = self.gridLayout.cellRect(1, 1).height() + self.gridLayout.verticalSpacing()
        self.setFixedHeight(self.current_height + self.inc_height)
        self.current_height += self.inc_height

    def dec_rule_box(self):
        order = self.ruleBox_count
        if order < 2:
            return
        self.ruleBox_widget['lev_%d' % order].deleteLater()
        del self.ruleBox_widget['lev_%d' % order]
        self.ruleBox_widget['l%d_regexp' % order].deleteLater()
        del self.ruleBox_widget['l%d_regexp' % order]
        self.ruleBox_widget['l%d_split' % order].deleteLater()
        del self.ruleBox_widget['l%d_split' % order]
        self.setFixedHeight(self.current_height - self.inc_height)
        self.current_height -= self.inc_height
        self.ruleBox_count -= 1

    def edit_preset_regexp(self):
        self.editbox = EditRegExp(self)
        self.editbox.show()

    def auto_analysis(self):
        def try_regexp(regexp):
            while TEXT == '':
                time.sleep(0.1)
            if re.search(regexp, TEXT, re.MULTILINE):
                return True
            else:
                return False

        txt_path = self.path_input_line.text()
        if txt_path == '' or txt_path.startswith('可'):
            QtWidgets.QMessageBox.information(self, '警告', '文件路径不能为空，请输入文件路径！')
            return

        self.setCursor(QtCore.Qt.WaitCursor)  # 改变鼠标光标为等待
        available_regexp = []
        for regexp in self.preset_regexp:
            if try_regexp(regexp):
                available_regexp.append(regexp)
        if available_regexp:
            need_boxes_num = len(available_regexp) - self.ruleBox_count
            if need_boxes_num > 0:
                for i in range(need_boxes_num):
                    self.add_rule_box()
            elif need_boxes_num < 0:
                for i in range(abs(need_boxes_num)):
                    self.dec_rule_box()
            index = 0
            for regexp in available_regexp:
                index += 1
                self.ruleBox_widget["l%d_regexp" % index].setCurrentText(regexp)
        else:
            QtWidgets.QMessageBox.information(self, '警告', '未能匹配到任何标题！')
        self.setCursor(QtCore.Qt.ArrowCursor)  # 改变光标为正常


class EditRegExp(QtWidgets.QWidget):
    def __init__(self, parent=None):
        self.parent_ = parent
        super(EditRegExp, self).__init__(None)
        ui = edit_regexp.Ui_edit_regexp()
        ui.setupUi(self)
        self.listWidget = self.findChild(QtWidgets.QListWidget, 'exp_listview')
        self.view_regexp()

    def parent(self):
        return self.parent_

    def view_regexp(self):
        mainform = self.parent()
        for regexp in mainform.preset_regexp:
            item = QtWidgets.QListWidgetItem(regexp)
            item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)
            self.listWidget.addItem(item)

    def add_item(self):
        item = QtWidgets.QListWidgetItem('请在此输入正则表达式')
        item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)
        self.listWidget.addItem(item)

    def dec_item(self):
        cur_row = self.listWidget.currentRow()
        self.listWidget.takeItem(cur_row)

    def move_up_item(self):
        cur_row = self.listWidget.currentRow()
        if cur_row == 0:
            return
        item = self.listWidget.takeItem(cur_row)
        self.listWidget.insertItem(cur_row - 1, item)
        self.listWidget.setCurrentRow(cur_row - 1)

    def move_down_item(self):
        cur_row = self.listWidget.currentRow()
        if cur_row == self.listWidget.count() - 1:
            return
        item = self.listWidget.takeItem(cur_row)
        self.listWidget.insertItem(cur_row + 1, item)
        self.listWidget.setCurrentRow(cur_row + 1)

    def closeEvent(self, event):
        mainform = self.parent()
        regexps = []
        for index in range(self.listWidget.count()):
            item = self.listWidget.item(index)
            regexps.append(item.text())
        # 更新主窗口的预置正则
        if regexps == []:
            mainform.preset_regexp = DEFAULT_REGEXPS
        else:
            mainform.preset_regexp = regexps
        # 更新编辑框的预置正则
        ruleBox = mainform.ruleBox_widget
        for i in range(1, mainform.ruleBox_count + 1):
            ruleBox['l%d_regexp' % i].clear()
            for exp in mainform.preset_regexp:
                ruleBox['l%d_regexp' % i].addItem(exp)
            ruleBox['l%d_regexp' % i].setCurrentText('')


class Other(QtWidgets.QWidget):
    def __init__(self, parent=None):
        self.parent_ = parent
        super(Other, self).__init__(None)
        ui = other.Ui_ohter()
        ui.setupUi(self)
        self.import_css = self.findChild(QtWidgets.QCheckBox, 'import_css')
        self.add_img_code = self.findChild(QtWidgets.QCheckBox, 'add_img_code')
        self.cssview = self.findChild(QtWidgets.QListWidget)
        self.code_button = self.findChild(QtWidgets.QPushButton, 'mod_code')
        if not self.import_css.isChecked():
            self.cssview.setEnabled(False)
        if not self.add_img_code.isChecked():
            self.code_button.setEnabled(False)
        self.import_css.stateChanged.connect(self.cssview_switch)
        self.add_img_code.stateChanged.connect(self.codebutton_switch)

    def parent(self):
        return self.parent_

    def cssview_switch(self, status):
        if status:
            self.cssview.setEnabled(True)
        else:
            self.cssview.setEnabled(False)

    def codebutton_switch(self, status):
        if status:
            self.code_button.setEnabled(True)
        else:
            self.code_button.setEnabled(False)

    def open_img_code(self):
        notepad = os.path.join(os.getenv('WINDIR'), 'notepad.exe')
        template_path = os.path.join(CURDIR, 'template/template.txt')
        os.system('{notepad} {template}'.format(notepad=notepad, template=template_path))

    def closeEvent(self, event):
        new_sheet = {}
        checked_sheet = []
        pseudoItems = self.cssview.get_all_pseudoItems()
        for pseudoItem in pseudoItems:
            sheetname = pseudoItem.lineEdit.text()
            if pseudoItem.isChecked():
                checked_sheet.append(sheetname)
        self.parent().checked_sheet = checked_sheet
        self.parent().is_import_css = '1' if self.import_css.isChecked() else '0'
        self.parent().is_img_code = '1' if self.add_img_code.isChecked() else '0'


class TitleTree(QtWidgets.QWidget):

    def __init__(self, parent, titles=[], ignore=False):
        super(TitleTree, self).__init__()
        self.parent_ = parent
        self.ui = treeview.Ui_Form()
        self.ui.setupUi(self)
        self.limit_lineEdit = self.findChild(QtWidgets.QLineEdit, 'limit_lineEdit')
        self.limit_lineEdit.setValidator(QtGui.QIntValidator(0, 9999))
        self.limit_lineEdit.setText(self.parent_.highlight_len)
        self.lenth_limit = int(self.parent_.highlight_len)
        # 编辑框按下Enter键时发送信号
        self.limit_lineEdit.returnPressed.connect(self.reflash_highlight)

        self.seqcheck_button = self.findChild(QtWidgets.QPushButton, 'seqCheckSwitch')

        self.titles = titles  # 储存每行标题的级别和标题名称
        self.len_collection = []  # 储存每行标题的长度及子项地址
        self.highlight_collection = []  # 储存高亮标题的长度及地址
        self.build_tree(ignore)

    def build_tree(self, ignore):
        last_lv = '9'
        self.tree = self.findChild(QtWidgets.QTreeWidget, 'title_tree')
        self.verticalLayout = self.findChild(QtWidgets.QVBoxLayout, 'verticalLayout')
        item = QtWidgets.QTreeWidgetItem()
        count = 0
        for lv, title in self.titles:
            if lv < last_lv:
                try:
                    parent = item.parent().parent()
                except:
                    parent = item.parent()
            elif lv > last_lv:
                parent = item
            item = QtWidgets.QTreeWidgetItem(parent)
            item.setText(0, title)
            item.setData(2, 0, count)
            self.len_collection.append((len(title), item))
            if len(title) > self.lenth_limit:
                # 设前景高亮，背景设在QSS且QSS权值更高，所以这里设前景高亮
                item.setForeground(0, QtGui.QColor(255, 0, 0))
                self.highlight_collection.append((len(title), item))
            if parent == None:
                self.tree.addTopLevelItem(item)
            last_lv = lv
            count += 1

        if ignore:
            for row in self.parent().ignore_title['ignore_position']:
                ignore_item = self.len_collection[row][1]
                font = QtGui.QFont()
                font.setStrikeOut(True)
                ignore_item.setFont(0, font)

        self.tree.expandAll()
        self.verticalLayout.addWidget(self.tree)

    def reflash_highlight(self):
        self.limit_lineEdit.clearFocus()
        if self.lenth_limit == int(self.limit_lineEdit.text()):
            return
        self.lenth_limit = int(self.limit_lineEdit.text())
        self.parent().highlight_len = self.limit_lineEdit.text()
        for length, item in self.highlight_collection:
            item.setForeground(0, QtGui.QColor(0, 0, 0))
        self.highlight_collection.clear()
        for length, item in self.len_collection:
            if length > self.lenth_limit:
                item.setForeground(0, QtGui.QColor(255, 0, 0))
                self.highlight_collection.append((length, item))

    def parent(self):
        return self.parent_


def read_text_threading(txt_path):
    global TEXT

    if not os.path.exists(txt_path):
        TEXT = ''
        return

    try:
        with open(txt_path, 'r', encoding='utf-8') as txtfile:
            text = txtfile.read()
    except:
        try:
            with open(txt_path, 'r', encoding='utf-16') as txtfile:
                text = txtfile.read()
        except:
            with open(txt_path, 'r', encoding='gbk', errors='ignore') as txtfile:
                text = txtfile.read()

    # 空文件时TEXT加一个空白符，防止主线程因等待TEXT而卡死。
    if text == '':
        TEXT = ' '
        return

    text = unescape(text)
    text = text.replace(r'&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    TEXT = text


def split_text(settings={}, preview=False):
    while TEXT == '':
        time.sleep(0.1)
    text = TEXT
    titles_catched = []
    title_tags = []

    count = settings['ruleBox_count']

    def sub_lv(match, lv, order):
        title_ = re.sub(r'^\s+|\s+$', r'', match.group())
        title = '<h%d>' % lv + title_ + '</h%d>' % lv
        if preview:
            return title
        split_char = '<✄>' if settings['split']['l%d_split' % order] else ''
        return split_char + title

    for order in range(1, count + 1):
        lv = settings['lev']['lev_%d' % order]
        regexp = re.sub('^\s*$', '', settings['regexp']['l%d_regexp' % order])
        if regexp:
            text = re.sub(regexp, lambda m: sub_lv(m, lv, order), text, flags=re.MULTILINE)

    if preview:
        titles_catched = re.findall(r'<h(\d)>(.*?)<', text)
        return titles_catched

    ignore_list = []
    if settings['ignore']['regexp'] == settings['regexp']:
        if settings['ignore']['ignore_position'] != []:
            ignore_list = settings['ignore']['ignore_position']

    sub_ignore_count = [-1]

    def sub_ignore(match):
        sub_ignore_count[0] += 1
        if sub_ignore_count[0] == ignore_list[0]:
            ignore_list.pop(0)
            return match.group(1)
        return match.group(0)

    if ignore_list:
        ignore_list.sort()
        match_count = ignore_list[-1] + 1
        text = re.sub(r'(?:<✄>)?<h\d>(.*?)</h\d>', sub_ignore, text, match_count)

    title_tags = re.findall(r'<✄><h\d>(.*)<', text)
    chapter_list = text.split('<✄>')
    if re.match('\s*$', chapter_list[0]):
        chapter_list.pop(0)  # 第一个分章没有内容
    else:
        title_tags = [''] + title_tags  # 给第一个分章加标题位
    global CHAPTERS
    CHAPTERS = chapter_list
    return title_tags


def norepeat_filename(prefix, order):
    filename = prefix + order + ".xhtml"
    repeat = False
    while True:
        for mid, href in bk.text_iter():
            if href.lower().endswith(filename.lower()):
                repeat = True
                break
        if not repeat:
            break
        prefix += '_'
        filename = prefix + order + ".xhtml"
        repeat = False
    return filename


def build_xhtml(title_tags, mainform):
    chapter_list = CHAPTERS
    chapter_filename_rule = mainform.ui.filename_rule_le.text().strip()
    chapter_filename_prefix = re.sub(r"\d+$", r'', chapter_filename_rule)
    chapter_order = re.search(r"\d+$", chapter_filename_rule).group() if re.search(r"\d+$",
                                                                                   chapter_filename_rule) else ""

    chapter_order_len = len(chapter_order)
    if chapter_order_len > 0:
        order_index = int(chapter_order)
    else:
        order_index = 0
    bk_spine = bk.getspine_epub3()

    with open(os.path.join(CURDIR, 'template/template.txt'), 'r', encoding='utf-8') as tpl:
        xhtml_template = tpl.read()
        indent = re.search(r"([ \t]*)\[MAIN\]", xhtml_template)
        indent = indent.group(1) if indent else ""
    for chapter_text in chapter_list:
        title = title_tags.pop(0)
        xhtml = re.sub(r"\[TITLE\]", title, xhtml_template)
        xhtml = re.sub(r"[ \t]*\[MAIN\]", set_p_em(chapter_text, indent), xhtml, 1)
        suffix_order = '0' * (chapter_order_len - len(str(order_index))) + str(order_index)
        chapter_filename = chapter_filename_prefix + suffix_order + '.xhtml'
        order_index += 1
        unique_id = chapter_filename
        mime = 'application/xhtml+xml'
        try:
            bk.addfile(unique_id, chapter_filename, xhtml, mime)
        except:
            chapter_filename = norepeat_filename(chapter_filename_prefix, suffix_order)
            unique_id = chapter_filename
            bk.addfile(unique_id, chapter_filename, xhtml, mime)
        bk_spine.append((unique_id, None, None))

    bk.setspine_epub3(bk_spine)


def set_p_em(text, indent=""):
    blank_chars = "\r\n\t\x20\xa0\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u200b\u200c\u200d\u202f\u2060\u3000\ufeff"
    text = text.strip(blank_chars).replace("\\", "\\\\")
    formatted_text = ''
    para = re.split('\r\n|\n', text)
    for p in para:
        p = p.strip(blank_chars)
        if p and p[0] != '<':
            if p:
                formatted_text += indent + '<p>' + p + '</p>\n'
        elif p and p[0] == '<':
            formatted_text += indent + p + '\n'
        else:
            formatted_text += indent + '<p><br/></p>\n'
    if formatted_text:
        return formatted_text[0:-1]
    else:
        return ""


def write_ini_file(mainform):
    conf = ModConfigParser()
    conf.add_section("ini_info")
    conf.set("ini_info", "ini_path", mainform.ini_openpath)
    conf.set("ini_info", "highlight_len", mainform.highlight_len)

    conf.add_section("regexp")
    if mainform.preset_regexp:
        order = 0
        for regexp in mainform.preset_regexp:
            order += 1
            conf.set("regexp", 'exp_%d' % order, regexp)

    with open(os.path.join(CURDIR, 'config.ini'), 'w', encoding='utf-8') as cf:
        conf.write(cf)


def startfile(path):
    _platform = system()
    if _platform == "Darwin":  # Mac OS
        subprocess.call(["open", path])
    elif _platform == "Linux":  # Linux
        subprocess.call(["xdg-open", path])
    else:
        try:
            os.startfile(path)  # windows
        except:
            # 不支持的平台
            pass


def run(book):
    global bk
    bk = book
    global CURDIR
    CURDIR = os.path.dirname(os.path.realpath(__file__))
    app = QtWidgets.QApplication(sys.argv)
    win = MainForm()
    win.show()
    app.exec()

    write_ini_file(win)

    if BUILD:
        title_tags = split_text(win.settings)
        build_xhtml(title_tags, win)

    return 0


if __name__ == "__main__":
    from sigil_env import Ebook

    bk = Ebook('test.epub')
    run(bk)
    bk.save_as("test_repack.epub")
