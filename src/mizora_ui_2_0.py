from idlelib.searchengine import get_selection
from importlib import reload
from PySide2 import QtWidgets, QtCore, QtGui
import os
import hou
import _houdini

reload(_houdini)

thumbnail_path = '/Users/kmaev/Documents/hou_dev/arcane_tower/mizora/mizora/resources/mizora_thumbnail.JPG'


class Assembler(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Assembler, self).__init__(parent=parent)
        self.resize(900, 500)
        self.setWindowTitle('Mizora 2:0')
        self.central_layout = QtWidgets.QVBoxLayout()
        self.central_layout.setAlignment(QtCore.Qt.AlignTop)

        # Context Line creation
        self.context_line = QtWidgets.QLineEdit()
        self.context_line.setPlaceholderText(
            "Write parent node here: '/obj/my_geometry'")

        self.central_layout.addWidget(self.context_line)
        # Set completer to context line
        self.set_completer()

        # Search Group Widgets

        self.search_grp = QtWidgets.QGroupBox()
        self.search_grp_layout = QtWidgets.QHBoxLayout()
        self.search_grp.setLayout(self.search_grp_layout)
        self.central_layout.addWidget(self.search_grp)

        # Add search QLine
        self.search_line = QtWidgets.QLineEdit()
        self.search_line.setPlaceholderText('Search variable')
        self.search_grp_layout.addWidget(self.search_line)

        self.search_btn = QtWidgets.QPushButton("Search")
        self.search_grp_layout.addWidget(self.search_btn)

        # Add Edit Group
        self.edit_grp = QtWidgets.QGroupBox()
        self.edit_grp_layout = QtWidgets.QHBoxLayout()
        self.edit_grp.setLayout(self.edit_grp_layout)
        self.central_layout.addWidget(self.edit_grp)

        # Add Search Output QList

        self.search_result_list = QtWidgets.QListWidget()
        self.edit_grp_layout.addWidget(self.search_result_list)

        # Add Code Edit QTextEdit
        self.code_edit = QtWidgets.QTextEdit()
        self.edit_grp_layout.addWidget(self.code_edit)

        # Add Rename Group (part of the Edit Layout)

        self.rename_grp = QtWidgets.QGroupBox()
        self.rename_grp_layout = QtWidgets.QVBoxLayout()
        self.rename_grp_layout.setAlignment(QtCore.Qt.AlignTop)
        self.rename_grp.setLayout(self.rename_grp_layout)
        self.edit_grp_layout.addWidget(self.rename_grp)

        # Add New Variable Name QLine

        self.new_name_line = QtWidgets.QLineEdit()
        self.new_name_line.setPlaceholderText('Rename to:')
        self.rename_grp_layout.addWidget(self.new_name_line)

        # Add Rename All QCheckBox

        self.rename_all_check = QtWidgets.QCheckBox("Rename all")
        self.rename_grp_layout.addWidget(self.rename_all_check)

        # Add Rename Button QPushButton

        self.rename_btn = QtWidgets.QPushButton('Rename')
        self.rename_grp_layout.addWidget(self.rename_btn)

        # DEBUG SECTION
        self.test = QtWidgets.QPushButton('Debug')
        self.central_layout.addWidget(self.test)
        # END OF DEBUG SECTION

        # Buttons connection
        self.test.clicked.connect(self.get_current_context)
        self.search_btn.clicked.connect(self.on_search_btn_executed)
        self.search_result_list.itemSelectionChanged.connect(self.on_list_item_changed)

        self.setLayout(self.central_layout)

        self.var_occurrences_map = {}

        # ADD STYLE SHEET
        script_dir = os.path.dirname(__file__)
        resources_path = os.path.join(script_dir, "..", "resources")

        resources_path = os.path.normpath(resources_path)

        with open(os.path.join(resources_path, "style_hou.qss"), 'r') as f:
            self.setStyleSheet(f.read())

    # CONTEXT LINE FUNCTIONS
    #  Context line completer
    def set_completer(self):
        allowed = ('subnet', 'geo')
        nodes = sorted([x.path() for x in hou.node('/').allSubChildren(True, False)
                        if x.type().name() in allowed])
        completer = QtWidgets.QCompleter(list(nodes))
        completer.popup().setObjectName('completer')
        self.context_line.setCompleter(completer)

    #   Return currently selected houdini context
    def get_current_context(self):  # Do this function needed or it could be sources directly from _houdini.py
        return _houdini.get_hou_search_context(self.context_line.text())

    def on_search_btn_executed(self):
        self.search_result_list.clear()
        self.var_occurrences_map = {}
        self.populate_search_result_list()
        self.search_result_list.item(0).setSelected(True)
        self.populate_code_editor()

    def populate_search_result_list(self) -> None:
        """
        This function populates the search output list widget.
        """
        self.search_result_list.clear()
        current_context = _houdini.get_hou_search_context(self.context_line.text())
        self.var_occurrences_map = _houdini.find_variable_occurrences(current_context, self.search_line.text())

        # Populate the list widget
        for item, snippet in self.var_occurrences_map.items():
            list_item = QtWidgets.QListWidgetItem(item.path())
            list_item.setData(QtCore.Qt.UserRole, snippet)
            self.search_result_list.addItem(list_item)

        # Debug
        """if self.search_result_list.count() > 0:
            first_item = self.search_result_list.item(0)
            print(first_item.data(QtCore.Qt.UserRole))"""

    def get_selection(self, widget):
        """
        Get the currently selected QListWidgetItem from the widget.
        """
        selected = widget.selectedItems()
        return selected[0] if selected else None

    def populate_code_editor(self):
        """
        Populate the code editor with the snippet data from the selected list item.
        """
        selected_item = self.get_selection(self.search_result_list)
        if selected_item:

            current_code = selected_item.data(QtCore.Qt.UserRole)

            self.code_edit.setPlainText(current_code)
        else:

            self.code_edit.setPlainText("")

    def on_list_item_changed(self):
        self.populate_code_editor()


dialog = None


def show_houdini():
    import hou
    global dialog
    dialog = Assembler(parent=hou.qt.mainWindow())
    dialog.show()
    return dialog
