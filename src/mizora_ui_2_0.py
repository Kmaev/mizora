from idlelib.searchengine import get_selection
from importlib import reload
from PySide2 import QtWidgets, QtCore, QtGui
import os
import hou
import _houdini

reload(_houdini)

class Assembler(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Assembler, self).__init__(parent=parent)
        self.resize(1300, 700)
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
        font = QtGui.QFont("Menlo", 14, QtGui.QFont.Bold)  # Font: Arial, Size: 14, Bold and Italic
        self.code_edit.setCurrentFont(font)
        self.edit_grp_layout.addWidget(self.code_edit)
        self.highlighter = PythonSyntaxHighlighter(self.code_edit.document())

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

        # Buttons connection
        # self.test.clicked.connect(self.get_current_context)
        self.search_btn.clicked.connect(self.on_search_btn_executed)
        self.search_result_list.itemSelectionChanged.connect(self.on_list_item_changed)
        self.rename_btn.clicked.connect(self.on_rename_btn_executed)
        self.apply_btn.clicked.connect(self.apply_all)

        self.setLayout(self.central_layout)

        self.var_occurrences_map = {}
        self.prev_selected = None

        # ADD STYLE SHEET
        script_dir = os.path.dirname(__file__)
        resources_path = os.path.join(script_dir, "..", "resources")
        resources_path = os.path.normpath(resources_path)

        with open(os.path.join(resources_path, "style_hou.qss"), 'r') as f:
            self.setStyleSheet(f.read())

        # CONTEXT LINE FUNCTIONS
        # Context line completer

    def set_completer(self):
        """
        Sets up an auto-completer for the context line widget.

        This function populates a QCompleter with paths of Houdini nodes
        of specific types (`subnet` and `geo`) located within the root node ('/').
        The completer is then attached to the `context_line` widget, enabling
        auto-completion for valid node paths.
        """

        allowed = ('subnet', 'geo')
        nodes = sorted([x.path() for x in hou.node('/').allSubChildren(True, False)
                        if x.type().name() in allowed])
        completer = QtWidgets.QCompleter(list(nodes))
        completer.popup().setObjectName('completer')
        self.context_line.setCompleter(completer)

        # Return currently selected houdini context

    def get_current_context(self) -> list:
        """
        Retrieves the current search context based on the input in the context line.
        """
        return _houdini.get_hou_search_context(self.context_line.text())

    def on_search_btn_executed(self):
        """
        Executes the search operation when the search button is clicked.

        If the search field is not empty, it populates the search results list and updates related components.
        Otherwise, it displays an error message and raises a ValueError.
        """
        self.search_result_list.clear()
        self.code_edit.clear()
        if self.search_line.text() != '':
            self.var_occurrences_map = {}
            self.populate_search_result_list()
            if self.search_result_list.count() > 0:
                self.search_result_list.item(0).setSelected(True)
                self.search_result_list.setCurrentRow(0)
                self.populate_code_editor()
                self.prev_selected = self.get_current_key()
        else:
            hou.ui.displayMessage(
                text=f"Search field cannot be empty. Please enter a variable to search.",
                buttons=('OK',),
                title="Error",
                severity=hou.severityType.Error
            )
            raise ValueError("Search field is empty")

    def populate_search_result_list(self) -> None:
        """
        This function populates the search output list widget.
        """
        self.search_result_list.clear()
        current_context = _houdini.get_hou_search_context(self.context_line.text())

        self.var_occurrences_map = _houdini.find_variable_occurrences(current_context, self.search_line.text())
        if self.var_occurrences_map:
            # Populate the list widget
            for item, snippet in self.var_occurrences_map.items():
                list_item = QtWidgets.QListWidgetItem(item.path())
                list_item.setData(QtCore.Qt.UserRole, snippet)
                self.search_result_list.addItem(list_item)
        else:
            hou.ui.displayMessage(
                text=f"Variable Not Found\nThe variable '{self.search_line.text()}' does not exist or is not defined. "
                     f"Please ensure you have entered the correct name and try again.",
                buttons=('OK',),
                title="Error",
                severity=hou.severityType.Error
            )
            raise ValueError("Variable Not Found")

    def get_selection(self, widget: object) -> object:
        """
        Get the currently selected QListWidgetItem from the widget.
        """
        selected = widget.selectedItems()
        return selected[0] if selected else None

    def get_current_key(self) -> str:
        """
        Retrieves the key from `self.var_occurrences_map` corresponding to the currently selected item
        in the search results list widget.

        - Uses the `get_selection` method to obtain the selected item.
        - Matches the selected item's text with the `path()` of keys in `self.var_occurrences_map`.
        - If no match is found, prints an error message and returns None.

        """
        selected_item = self.get_selection(self.search_result_list)
        if selected_item:

            # current_code = selected_item.data(QtCore.Qt.UserRole)
            try:
                node_key = next(key for key in self.var_occurrences_map if key.path() == selected_item.text())
            except StopIteration:
                raise ValueError("No matching key found in var_occurrences_map for the selected item.")

            if not node_key:
                print("Error: Selected node not found in var_occurrences_map")
                return
        return node_key

    def get_current_code(self) -> str:
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
        """
        editted_code = self.code_edit.toPlainText()

        # print(editted_code)

        self.populate_code_editor()
        self.var_occurrences_map[self.prev_selected] = editted_code
        if self.get_selection(self.search_result_list):
            self.prev_selected = self.get_current_key()

    def on_rename_btn_executed(self):
        """
        Handles the logic when the rename button is executed.

        - Updates the variable occurrences dictionary with the new code after replacing
        the old variable name with the new one.
        - Updates the list widget and code editor to reflect the changes.
        - If 'Rename All' is checked, applies renaming to all occurrences. Otherwise, moves
        the selection to the next occurrence in the list.
        """
        new_name = self.new_name_line.text()
        searched_name = self.search_line.text()

        node_key = self.get_current_key()

        current_code = self.get_current_code()
        new_code = _houdini.parse_variable(current_code, searched_name, new_name)

        # Update the dictionary
        self.var_occurrences_map[node_key] = new_code

        self.populate_code_editor()

        current_index = self.search_result_list.currentRow()
        if self.rename_all_check.isChecked():
            self.rename_all()
            hou.ui.displayMessage(
                text=f"'{self.search_line.text()}' has been renamed to '{self.new_name_line.text()}'",
                buttons=('OK',),
                severity=hou.severityType.Message
            )
        else:
            # if current_index < len(self.var_occurrences_map.keys()) - 1:
            if current_index < self.search_result_list.count() - 1:
                self.search_result_list.setCurrentRow(current_index + 1)
                self.search_result_list.item(current_index + 1).setSelected(True)
            else:
                self.search_result_list.setCurrentRow(0)
                self.search_result_list.item(0).setSelected(True)


        # print(f"{self.var_occurrences_map} - On rename executed")

    def rename_all(self):
        """
        Renames all occurrences of a variable across the entire dictionary.

        - Iterates through each key-value pair in the variable occurrences map.
        - Replaces the old variable name with the new one in the code.
        - Updates the dictionary with the modified code for each node.
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

        editted_code = self.code_edit.toPlainText()

        self.var_occurrences_map[self.get_current_key()] = editted_code
        for node_key, current_code in self.var_occurrences_map.items():
            if node_key:
                try:
                    node_key.parm('snippet').set(current_code)
                except hou.PermissionError:
                    print(f"[Skipped] {node_key.path()} due to permission error.")
                    continue

        self.new_name_line.clear()
        self.rename_all_check.setChecked(False)
        self.search_line.clear()


class PythonSyntaxHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        keyword_format = QtGui.QTextCharFormat()
        keyword_format.setForeground(QtGui.QColor(137, 198, 219))  # Blue-ish
        keyword_format.setFontWeight(QtGui.QFont.Bold)

        at_keyword_format = QtGui.QTextCharFormat()
        at_keyword_format.setForeground(QtGui.QColor(211, 207, 156))  # Yellow-ish
        at_keyword_format.setFontWeight(QtGui.QFont.Bold)

        string_format = QtGui.QTextCharFormat()
        string_format.setForeground(QtGui.QColor(121, 169, 120))  # Green

        comment_format = QtGui.QTextCharFormat()
        comment_format.setForeground(QtGui.QColor(122, 126, 132))  # Gray
        # comment_format.setFontItalic(True)

        operator_format = QtGui.QTextCharFormat()
        operator_format.setForeground(QtGui.QColor(99, 148, 185))  # Blue
        operator_format.setFontWeight(QtGui.QFont.Bold)

        function_format = QtGui.QTextCharFormat()
        function_format.setForeground(QtGui.QColor(131, 131, 185))  # Purple
        function_format.setFontWeight(QtGui.QFont.Bold)

        keywords = [
            "int\s", "float\s", "string\s", "vector\s", "None",
            "break", "continue", "pass"
        ]

        operators = [
            "if", "for", "while", "foreach",
            "else", "else if"
        ]

        at_keywords = [
            "@[a-zA-Z0-9_]+", "[a-zA-Z]@[a-zA-Z0-9_]+", "[a-zA-Z]\[\]@[a-zA-Z0-9_]+"
        ]

        vex_functions = [
            "(?<!\\w)([a-zA-Z_][a-zA-Z0-9_]*)\\s*(?=\\()"
        ]

        for function in vex_functions:
            self.highlighting_rules.append((QtCore.QRegularExpression(function), function_format))

        for operator in operators:
            self.highlighting_rules.append((QtCore.QRegularExpression(operator), operator_format))

        for at_keyword in at_keywords:
            self.highlighting_rules.append((QtCore.QRegularExpression(at_keyword), at_keyword_format))

        for keyword in keywords:
            self.highlighting_rules.append((QtCore.QRegularExpression(keyword), keyword_format))

        self.highlighting_rules.append((QtCore.QRegularExpression("\".*\""), string_format))
        self.highlighting_rules.append((QtCore.QRegularExpression("'.*'"), string_format))
        self.highlighting_rules.append((QtCore.QRegularExpression("//[^\n]*"), comment_format))

    def highlightBlock(self, text):
        for pattern, text_format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, text_format)


dialog = None


def show_houdini():
    import hou
    global dialog
    dialog = Assembler(parent=hou.qt.mainWindow())
    dialog.show()
    return dialog
