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

        #Context Line creation
        self.context_line= QtWidgets.QLineEdit()
        self.context_line.setPlaceholderText(
            "Write parent node here: '/obj/my_geometry'")

        self.central_layout.addWidget(self.context_line)
        #Set completer to context line
        self.set_completer()



        self.test = QtWidgets.QPushButton('test')
        self.central_layout.addWidget(self.test)
        self.test.clicked.connect(self.get_current_context)


        self.setLayout(self.central_layout)

        # ADD STYLE SHEET
        # Build a relative path from src to resources
        script_dir = os.path.dirname(__file__)  # Directory where the script is located
        resources_path = os.path.join(script_dir, "..", "resources")

        # Normalize the path to remove ".."
        resources_path = os.path.normpath(resources_path)

        with open(os.path.join(resources_path, "style_hou.qss"), 'r') as f:
            self.setStyleSheet(f.read())

    #CONTEXT LINE FUNCTIONS

    #  Context line completer
    def set_completer(self):
        allowed = ('subnet', 'geo')
        nodes = sorted([x.path() for x in hou.node('/').allSubChildren(True, False)
                        if x.type().name() in allowed])

        completer = QtWidgets.QCompleter(list(nodes))
        completer.popup().setObjectName('completer')
        #completer.popup().setStyleSheet(self.style)
        self.context_line.setCompleter(completer)

    #   Return currently selected houdini context
    def get_current_context(self):

        ## TODO Currently selected context should be a list
        # TODO: Add functionality to clear the selected context when a '*' is used in the context definition,
        # allowing multiple contexts to be added and cleared appropriately.
        print(_houdini.get_hou_search_context(self.context_line.text()))
        return hou.node(self.context_line.text())


dialog = None
def show_houdini():
    import hou
    global dialog
    dialog = Assembler(parent=hou.qt.mainWindow())
    dialog.show()
    return dialog