import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, QTreeView, QListView,
                             QFileSystemModel, QLineEdit, QLabel, QSpinBox, QFileDialog,
                             QPushButton, QPlainTextEdit, QGroupBox, QSpacerItem)
from PyQt5.QtCore import (QDir, Qt)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("File explorer")
        self.layout = QVBoxLayout(self)


class MplToolbar(NavigationToolbar):
    def __init__(self, figure_canvas, parent=None):
        self.toolitems = (
                            ('Home', 'Reset original view', 'home', 'home'),
                            ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
                            ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
                            ('Save','Save the figure', 'filesave', 'save_figure'),
                         )
        NavigationToolbar.__init__(self, figure_canvas, parent=None)


class Canvas(QWidget):
    def __init__(self, explorer, width=5, height=3, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.sc = FigureCanvasQTAgg(self.fig)
        self.sc.axes = self.fig.add_subplot(111)
        self.sc.axes.format_coord = lambda x, y : '(x, y) = ({:.2f}, {:.2f})'.format(x, y)
        self.fig.patch.set_facecolor('None')
        self.toolbar = MplToolbar(self.sc)
        self.toolbar.setStyleSheet('QToolBar { border: 0px }')
        # self.layout = QVBoxLayout()
        # self.layout.addWidget(self.toolbar)
        # self.layout.addWidget(self.sc)
        self.sc.setStyleSheet('background-color:transparent;')

    def update_plot(self, explorer):
        self.sc.axes.cla()
        self.sc.axes.plot(explorer.xcol, explorer.ycol, c='k')
        self.sc.draw()


class Explorer(QWidget):
    def __init__(self, rootdir=QDir.rootPath()):
        QWidget.__init__(self)
        self.treeview = QTreeView()
        self.listview = QListView()
        self.path = rootdir
        self.filename = ''
        self.filepath = rootdir
        self.canvas = None
        self.col_selector = None

        self.header = ''
        self.xcol = [1]
        self.ycol = [1]
        self.ncols = 0

        self.dirModel = QFileSystemModel()
        self.dirModel.setRootPath(self.path)
        self.dirModel.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs)

        self.fileModel = QFileSystemModel()
        self.fileModel.setRootPath(self.filepath)
        self.fileModel.setFilter(QDir.NoDotAndDotDot | QDir.Files)
        self.fileModel.setNameFilters(['*.txt'])
        self.fileModel.setNameFilterDisables(0)

        self.treeview.setModel(self.dirModel)
        self.listview.setModel(self.fileModel)
        for i in [1, 2, 3]: self.treeview.setColumnHidden(i, True)
        self.treeview.setHeaderHidden(True)

        self.treeview.setRootIndex(self.dirModel.index(self.path))
        self.listview.setRootIndex(self.fileModel.index(self.path))

        self.treeview.clicked.connect(self.on_clicked)
        self.listview.selectionModel().currentChanged.connect(self.file_selected)
        self.listview.selectionModel().currentChanged.connect(lambda: self.canvas.update_plot(self))
        self.listview.selectionModel().currentChanged.connect(lambda: self.col_selector.update_range(self.ncols))

    def on_clicked(self, index):
        self.path = self.dirModel.fileInfo(index).absoluteFilePath()
        self.listview.setRootIndex(self.fileModel.setRootPath(self.path))

    def file_selected(self, index):
        self.filename = self.fileModel.fileName(index)
        self.filepath = self.fileModel.filePath(index)
        self.load_file()

    def load_file(self):
        try:
            if self.filepath.endswith('.txt'):
                with open(self.filepath, 'r') as file:
                        self.header, self.xcol, self.ycol = '', [], []
                        for ln in file:
                            if ln.startswith('#'):
                                self.header += ln[2:]
                            else:
                                cols = ln.split('\t')
                                self.xcol.append(float(cols[0]))
                                self.ycol.append(float(cols[self.col_selector.sp.value()]))
                        self.ncols = len(cols)
                        self.col_selector.update_range(self.ncols)
        except:
            self.header, self.xcol, self.ycol = '', [0], [0]

    def update_rootdir(self, rootdir):
        self.path = rootdir
        self.treeview.setRootIndex(self.dirModel.index(self.path))
        self.listview.setRootIndex(self.fileModel.index(self.path))


class Textbox(QWidget):
    def __init__(self, string=''):
        super().__init__()
        self.textbox = QLineEdit(self)
        self.textbox.setPlaceholderText('asdf')
        self.textbox.move(20, 20)
        self.textbox.resize(280, 40)
        self.string = string
        self.textbox.setText(self.string)
        self.textbox.setReadOnly(True)

    def update_name(self, new_string):
        self.string = new_string
        self.textbox.setText(self.string)


class ColumnSelector(QWidget):
    def __init__(self, canvas, explorer):
        super(ColumnSelector, self).__init__()
        self.label = QLabel()
        self.label.setText('Data column')
        self.label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.sp = QSpinBox()
        self.canvas = canvas
        self.explorer = explorer
        try:
            self.sp.setRange(1, len(self.canvas.df.columns)-1)
        except:
            self.sp.setRange(1, 1)
        self.sp.valueChanged.connect(self.value_changed)

    def value_changed(self):
        self.explorer.load_file()
        self.canvas.update_plot(self.explorer)

    def update_range(self, n):
        self.sp.setRange(0, n-1)


class DirectoryDialog(QWidget):
    def __init__(self):
        self.startingDir = QDir.rootPath()
        self.dialog = QFileDialog()
        self.dialog.setFileMode(QFileDialog.FileMode())
        #self.rootdir = self.dialog.getExistingDirectory(None, 'Choose directory', self.startingDir)
        self.rootdir = QDir.rootPath()
        super(DirectoryDialog, self).__init__()

    def update_rootdir(self, explorer):
        self.rootdir = self.dialog.getExistingDirectory(None, 'Choose directory', explorer.path)
        explorer.update_rootdir(self.rootdir)


if __name__ == '__main__':
    app = QApplication([])
    app.setStyle('Fusion')

    dirbrowse = DirectoryDialog()

    rootdir_display = Textbox(dirbrowse.rootdir)
    explorer = Explorer(rootdir=dirbrowse.rootdir)
    canvas = Canvas(explorer)
    colsel = ColumnSelector(canvas, explorer)
    explorer.canvas = canvas
    explorer.col_selector = colsel
    main_window = MainWindow()


    # Root directory dialog button
    opendialog = QPushButton()
    opendialog.setText('Change directory')
    opendialog.clicked.connect(lambda: dirbrowse.update_rootdir(explorer))

    # Directory explorer
    dir_layout = QVBoxLayout()
    dir_layout.addWidget(QLabel('Directory of data folder(s)'))
    dir_layout.addWidget(rootdir_display.textbox)
    dir_layout.addWidget(opendialog)
    dir_layout.addWidget(explorer.treeview)

    # File list
    files_layout = QVBoxLayout()
    files_layout.addWidget(QLabel('Filenames (*.txt)'))
    files_layout.addWidget(explorer.listview)

    # Combine directory explorer and file list 
    browser_layout = QHBoxLayout()
    browser_layout.addLayout(dir_layout)
    browser_layout.addLayout(files_layout)

    # Text box showing .txt-file header
    header_display = QPlainTextEdit()
    header_display.setReadOnly(True)
    update_header = lambda: header_display.setPlainText(explorer.header)
    explorer.listview.selectionModel().currentChanged.connect(update_header)
    header_panel = QVBoxLayout()
    header_panel.addWidget(QLabel('File header (# ... )'))
    header_panel.addWidget(header_display)

    # Combine explorer and header box
    left_panel = QVBoxLayout()
    left_panel.addLayout(browser_layout, 2)
    left_panel.addLayout(header_panel, 1)
    main_window.layout.addLayout(left_panel, 2)

    # Plot panel
    plot_layout = QVBoxLayout()
    plot_layout.addWidget(canvas.sc, 3)

    # Column selector
    colsel_layout = QHBoxLayout()
    colsel_layout.addWidget(canvas.toolbar)
    colsel_layout.addItem(QSpacerItem(100, 1))
    colsel_layout.addWidget(colsel.label)
    colsel_layout.addWidget(colsel.sp)
    plot_layout.addLayout(colsel_layout)
    plot_layout.setAlignment(colsel.sp, Qt.AlignRight)
    plot_layout.setAlignment(canvas.toolbar, Qt.AlignLeft)

    plotbox = QGroupBox()
    plotbox.setLayout(plot_layout)

    main_window.layout.addWidget(plotbox, 2)

    main_window.show()
    sys.exit(app.exec_())