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

        # Add Apply Button QPushButton

        self.apply_btn = QtWidgets.QPushButton('Apply')
        self.rename_grp_layout.addWidget(self.apply_btn)

        # DEBUG SECTION
        self.test = QtWidgets.QPushButton('Debug')
        self.central_layout.addWidget(self.test)
        # END OF DEBUG SECTION

        # Buttons connection
        self.test.clicked.connect(self.get_current_context)
        self.search_btn.clicked.connect(self.on_search_btn_executed)
        self.search_result_list.itemSelectionChanged.connect(self.on_list_item_changed)
        self.rename_btn.clicked.connect(self.on_rename_btn_executed)
        self.apply_btn.clicked.connect(self.apply_all)

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
        self.search_result_list.setCurrentRow(0)
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

    def get_current_key(self):
        """
        Retrieves the key from `self.var_occurrences_map` corresponding to the currently selected item
        in the search results list widget.

        - Uses the `get_selection` method to obtain the selected item.
        - Matches the selected item's text with the `path()` of keys in `self.var_occurrences_map`.
        - If no match is found, prints an error message and returns None.

        :return: The matching key (`node_key`) or None if not found.
        """
        selected_item = self.get_selection(self.search_result_list)
        if selected_item:

            # current_code = selected_item.data(QtCore.Qt.UserRole)
            node_key = next((key for key in self.var_occurrences_map if key.path() == selected_item.text()), None)
            if not node_key:
                print("Error: Selected node not found in var_occurrences_map")
                return
        return node_key

    def get_current_code(self):
        """
        Retrieves the current code associated with the currently selected item in the list widget.
        :return: The current code as a string.
        """
        node_key = self.get_current_key()

        current_code = self.var_occurrences_map[node_key]

        return current_code

    def populate_code_editor(self):
        """
        Populate the code editor with the snippet data from the selected list item.
        :return: None
        """

        current_code = self.get_current_code()
        if current_code:
            self.code_edit.setPlainText(current_code)
        else:

            self.code_edit.setPlainText("")

    def on_list_item_changed(self):
        """
        Populates the code editor when the selection in the search results list changes.
        :return: None
        """
        self.populate_code_editor()

    def on_rename_btn_executed(self):
        """
        Handles the logic when the rename button is executed.

        - Updates the variable occurrences dictionary with the new code after replacing
        the old variable name with the new one.
        - Updates the list widget and code editor to reflect the changes.
        - If 'Rename All' is checked, applies renaming to all occurrences. Otherwise, moves
        the selection to the next occurrence in the list.
        :return: None
        """
        new_name = self.new_name_line.text()
        searched_name = self.search_line.text()

        node_key = self.get_current_key()

        current_code = self.get_current_code()
        new_code = _houdini.parse_variable(current_code, searched_name, new_name)

        # Update the dictionary
        self.var_occurrences_map[node_key] = new_code
        # print(f"Updated Code: {self.var_occurrences_map[node_key]}")

        self.populate_code_editor()

        current_index = self.search_result_list.currentRow()
        if self.rename_all_check.isChecked():
            self.rename_all()
        else:
            if current_index < len(self.var_occurrences_map.keys()) - 1:
                print(current_index)
                self.search_result_list.setCurrentRow(current_index + 1)
                self.search_result_list.item(current_index + 1).setSelected(True)
            else:
                self.search_result_list.setCurrentRow(0)
                self.search_result_list.item(0).setSelected(True)

    def rename_all(self):
        """
        Renames all occurrences of a variable across the entire dictionary.

        - Iterates through each key-value pair in the variable occurrences map.
        - Replaces the old variable name with the new one in the code.
        - Updates the dictionary with the modified code for each node.

        :return: None
        """
        new_name = self.new_name_line.text()
        searched_name = self.search_line.text()
        for node_key, current_code in self.var_occurrences_map.items():
            new_code = _houdini.parse_variable(current_code, searched_name, new_name)

            # Update the dictionary and debug
            self.var_occurrences_map[node_key] = new_code

    def apply_all(self):
        """
        Saves all edited code into the corresponding Wrangle nodes.
        :return: None
        """
        for node_key, current_code in self.var_occurrences_map.items():
            node_key.parm('snippet').set(current_code)

        self.new_name_line.clear()
        self.rename_all_check.setChecked(False)
        self.search_line.clear()


dialog = None


def show_houdini():
    import hou
    global dialog
    dialog = Assembler(parent=hou.qt.mainWindow())
    dialog.show()
    return dialog
