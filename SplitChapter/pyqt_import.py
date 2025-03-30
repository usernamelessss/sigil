import os

e = os.environ.get('SIGIL_QT_RUNTIME_VERSION', '6.5.2')
SIGIL_QT_MAJOR_VERSION = tuple(map(int, (e.split("."))))[0]

if SIGIL_QT_MAJOR_VERSION == 6:
    from PySide6 import QtWidgets,QtGui,QtCore
    import main_ui_qt6 as main_ui
    import treeview_qt6 as treeview
    import other_qt6 as other
    import edit_regexp_qt6 as edit_regexp
elif SIGIL_QT_MAJOR_VERSION == 5:
    from PyQt5 import QtWidgets,QtGui,QtCore
    import main_ui
    import treeview
    import other
    import edit_regexp
    