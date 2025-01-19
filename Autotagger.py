import sys
import json
import os
import threading
import platform
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QComboBox,
    QLineEdit, QColorDialog, QMessageBox, QCheckBox, QFileDialog, QGroupBox, QProgressBar,
    QListWidget, QPlainTextEdit, QListWidgetItem, QMenu
)
from PyQt5.QtCore import Qt, QRect, QTimer, QThreadPool, QRunnable, pyqtSlot, pyqtSignal, QObject, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QImage, QFont, QColor, QFontDatabase, QMouseEvent, QTextCursor

class WorkerSignals(QObject):
    progress = pyqtSignal(int, int)  # current, total
    status_update = pyqtSignal(str, str)  # file_path, status

class ImageProcessorRunnable(QRunnable):
    def __init__(self, file_path, parent):
        super().__init__()
        self.file_path = file_path
        self.parent = parent
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            self.signals.status_update.emit(self.file_path, 'processing')
            image = QImage(self.file_path)
            if image.isNull():
                raise Exception("Failed to load image.")

            if self.parent.downsizeCheckBox.isChecked():
                image = self.parent.downsizeImageToSmallestSide(image)
            modifiedImage = self.parent.applyTextToImage(image)

            output_folder = os.path.join(os.path.dirname(self.file_path), "tagged")
            os.makedirs(output_folder, exist_ok=True)
            output_path = os.path.join(output_folder, os.path.basename(self.file_path))
            modifiedImage.save(output_path)

            self.signals.status_update.emit(self.file_path, 'success')
        except Exception:
            self.signals.status_update.emit(self.file_path, 'failed')
        finally:
            with self.parent.lock:
                self.parent.completed_tasks += 1
                self.signals.progress.emit(self.parent.completed_tasks, self.parent.total_files)

class AutoTagger(QWidget):
    def __init__(self):
        super().__init__()
        self.threadPool = QThreadPool()
        self.threadCount = 10

        # Determine config path based on platform
        if platform.system() == 'Windows':
            self.configPath = os.path.join(os.getenv('APPDATA'), 'AutoTagger', 'config.json')
        else:
            self.configPath = os.path.join(os.path.expanduser('~'), '.config', 'AutoTagger', 'config.json')
        
        self.selectedFolders = []
        self.completed_tasks = 0
        self.total_files = 0
        self.lock = threading.Lock()
        self.file_status = {}

        self.loadConfig()
        self.lastImage = None
        self.initUI()
        self.initTimer()
        self.offset = None

    def initUI(self):
        self.setWindowTitle('Auto Tagger')
        self.setGeometry(100, 100, 800, 600)

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #f0f0f0;
                border-radius: 10px;
            }
            QGroupBox {
                background-color: #3a3a3a;
                border: 1px solid #505050;
                border-radius: 10px;
                margin-top: 20px;
            }
            QLabel {
                font-size: 14px;
            }
            QPushButton {
                background-color: #3a8dde;
                border: none;
                border-radius: 10px;
                color: white;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #559edb;
            }
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: #3a3a3a;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #87cefa;
                border: 1px solid #87cefa;
                width: 18px;
                margin: -2px 0;
                border-radius: 4px;
            }
            QLineEdit {
                background-color: #3a3a3a;
                border: 1px solid #505050;
                color: #f0f0f0;
                padding: 5px;
                border-radius: 10px;
            }
            QComboBox {
                background-color: #3a3a3a;
                border: 1px solid #505050;
                color: #f0f0f0;
                padding: 5px;
                border-radius: 10px;
            }
            QCheckBox {
                background-color: #3a3a3a;
                border: none;
                color: #f0f0f0;
            }
            QPlainTextEdit {
                background-color: #3a3a3a;
                border: 1px solid #505050;
                color: #f0f0f0;
                padding: 5px;
                border-radius: 10px;
            }
            QListWidget {
                background-color: #3a3a3a;
                border: 1px solid #505050;
                color: #f0f0f0;
                padding: 5px;
                border-radius: 10px;
            }
        """)

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(10, 10, 10, 10)
        mainLayout.setSpacing(10)

        titleBar = QHBoxLayout()
        titleBar.setContentsMargins(0, 0, 0, 0)
        titleBar.setSpacing(5)

        titleLabel = QLabel("Auto Tagger")
        titleLabel.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        titleBar.addWidget(titleLabel)
        titleBar.addStretch()

        minButton = QPushButton("—")
        minButton.setFixedSize(30, 30)
        minButton.setStyleSheet("background-color: #2b2b2b; color: white; border-radius: 10px;")
        minButton.clicked.connect(self.showMinimized)
        titleBar.addWidget(minButton)

        maxButton = QPushButton("□")
        maxButton.setFixedSize(30, 30)
        maxButton.setStyleSheet("background-color: #2b2b2b; color: white; border-radius: 10px;")
        maxButton.clicked.connect(self.toggleMaximized)
        titleBar.addWidget(maxButton)

        closeButton = QPushButton("✕")
        closeButton.setFixedSize(30, 30)
        closeButton.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 10px;")
        closeButton.clicked.connect(self.close)
        titleBar.addWidget(closeButton)

        mainLayout.addLayout(titleBar)

        self.imageLabel = QLabel(self)
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.imageLabel.setStyleSheet("border: 1px solid #505050; border-radius: 10px; background-color: #2b2b2b;")
        mainLayout.addWidget(self.imageLabel)

        self.textInput = QLineEdit(self)
        self.textInput.setPlaceholderText("Enter your text here...")
        self.textInput.setText(self.customText)
        self.textInput.textChanged.connect(self.updateCustomText)
        mainLayout.addWidget(self.textInput)

        fontControlsLayout = QHBoxLayout()
        self.colorPickerButton = QPushButton('Pick Text Color', self)
        self.colorPickerButton.clicked.connect(self.pickTextColor)
        fontControlsLayout.addWidget(self.colorPickerButton)

        self.fontComboBox = QComboBox(self)
        self.fontComboBox.addItems(QFontDatabase().families())
        self.fontComboBox.setCurrentText(self.fontFamily)
        self.fontComboBox.currentTextChanged.connect(self.updateFontFamily)
        fontControlsLayout.addWidget(self.fontComboBox)

        mainLayout.addLayout(fontControlsLayout)

        fontSizeLayout = QHBoxLayout()
        fontSizeLayout.addWidget(QLabel('Font Size:'))
        self.fontSizeSlider = QSlider(Qt.Horizontal, self)
        self.fontSizeSlider.setRange(10, 100)
        self.fontSizeSlider.setValue(self.fontSize)
        self.fontSizeSlider.setTickInterval(5)
        self.fontSizeSlider.setTickPosition(QSlider.TicksBelow)
        self.fontSizeSlider.valueChanged.connect(self.updateFontSize)
        fontSizeLayout.addWidget(self.fontSizeSlider)
        mainLayout.addLayout(fontSizeLayout)

        textYOffsetLayout = QHBoxLayout()
        textYOffsetLayout.addWidget(QLabel('Text Vertical Offset:'))
        self.textYOffsetSlider = QSlider(Qt.Horizontal, self)
        self.textYOffsetSlider.setRange(0, 100)
        self.textYOffsetSlider.setValue(int(self.textYOffsetRatio * 100))
        self.textYOffsetSlider.setTickInterval(5)
        self.textYOffsetSlider.setTickPosition(QSlider.TicksBelow)
        self.textYOffsetSlider.valueChanged.connect(self.updateTextYOffset)
        textYOffsetLayout.addWidget(self.textYOffsetSlider)
        mainLayout.addLayout(textYOffsetLayout)

        self.downsizeCheckBox = QCheckBox("Downsize Image", self)
        self.downsizeCheckBox.setChecked(self.downsizeImage)
        self.downsizeCheckBox.stateChanged.connect(self.updateDownsizeImage)
        mainLayout.addWidget(self.downsizeCheckBox)

        self.sizeInput = QLineEdit(self)
        self.sizeInput.setPlaceholderText("Enter smallest side size...")
        self.sizeInput.setText(str(self.downsizeValue))
        self.sizeInput.textChanged.connect(self.updateDownsizeValue)
        mainLayout.addWidget(self.sizeInput)

        threadSliderLayout = QHBoxLayout()
        threadSliderLayout.addWidget(QLabel('Threads (max 20):'))
        self.threadCountSlider = QSlider(Qt.Horizontal, self)
        self.threadCountSlider.setRange(1, 20)
        self.threadCountSlider.setValue(self.threadCount)
        self.threadCountSlider.setTickInterval(1)
        self.threadCountSlider.setTickPosition(QSlider.TicksBelow)
        self.threadCountSlider.valueChanged.connect(self.updateThreadCount)
        threadSliderLayout.addWidget(self.threadCountSlider)
        mainLayout.addLayout(threadSliderLayout)

        self.toggleProcessingButton = QPushButton('Toggle Folder and File Processing', self)
        self.toggleProcessingButton.setCheckable(True)
        self.toggleProcessingButton.setChecked(True)
        self.toggleProcessingButton.toggled.connect(self.toggleProcessingViews)
        mainLayout.addWidget(self.toggleProcessingButton)

        folderGroupBox = QGroupBox("Folder Processing")
        folderGroupBox.setStyleSheet("QGroupBox { background-color: #3a3a3a; border: 1px solid #3a8dde; padding: 10px; border-radius: 10px; }")
        folderLayout = QVBoxLayout()
        folderLayout.setContentsMargins(10, 10, 10, 10)
        folderLayout.setSpacing(5)

        self.folderListWidget = QListWidget(self)
        self.folderListWidget.setSelectionMode(QListWidget.ExtendedSelection)
        self.folderListWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.folderListWidget.customContextMenuRequested.connect(self.showFolderListContextMenu)
        folderLayout.addWidget(self.folderListWidget)

        folderButtonsLayout = QHBoxLayout()
        self.selectFolderButton = QPushButton('Select Folder', self)
        self.selectFolderButton.clicked.connect(self.selectFolders)
        folderButtonsLayout.addWidget(self.selectFolderButton)

        self.removeFolderButton = QPushButton('Remove Selected', self)
        self.removeFolderButton.clicked.connect(self.removeSelectedFolders)
        folderButtonsLayout.addWidget(self.removeFolderButton)

        self.removeAllFoldersButton = QPushButton('Remove All', self)
        self.removeAllFoldersButton.clicked.connect(self.removeAllFolders)
        folderButtonsLayout.addWidget(self.removeAllFoldersButton)

        folderLayout.addLayout(folderButtonsLayout)
        self.includeSubfoldersCheckBox = QCheckBox("Include Subfolders", self)
        folderLayout.addWidget(self.includeSubfoldersCheckBox)

        self.processFoldersButton = QPushButton('Process Folders', self)
        self.processFoldersButton.clicked.connect(self.startFolderProcessing)
        folderLayout.addWidget(self.processFoldersButton)

        folderGroupBox.setLayout(folderLayout)
        mainLayout.addWidget(folderGroupBox)

        self.processingFilesTextBox = QPlainTextEdit(self)
        self.processingFilesTextBox.setReadOnly(True)
        mainLayout.addWidget(self.processingFilesTextBox)

        self.processClipboardButton = QPushButton('Process Clipboard Image', self)
        self.processClipboardButton.setStyleSheet("background-color: #559edb; color: white; font-weight: bold; padding: 10px; border-radius: 10px;")
        self.processClipboardButton.clicked.connect(self.processClipboardImage)
        mainLayout.addWidget(self.processClipboardButton)

        progressLayout = QHBoxLayout()
        self.progressBar = QProgressBar(self)
        self.progressBar.setValue(0)
        progressLayout.addWidget(self.progressBar)

        self.progressLabel = QLabel("0/0")
        progressLayout.addWidget(self.progressLabel)
        mainLayout.addLayout(progressLayout)

        self.setLayout(mainLayout)
        self.loadSavedFolders()

    def initTimer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.displayImage)
        self.timer.start(1000)

    def toggleMaximized(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def updateFontFamily(self, fontFamily):
        self.fontFamily = fontFamily
        self.saveConfig()
        self.displayImage()

    def updateCustomText(self, text):
        self.customText = text
        self.saveConfig()
        self.displayImage()

    def updateFontSize(self, value):
        self.fontSize = value
        self.saveConfig()
        self.displayImage()

    def updateTextYOffset(self, value):
        self.textYOffsetRatio = value / 100.0
        self.saveConfig()
        self.displayImage()

    def updateDownsizeImage(self, state):
        self.downsizeImage = state == Qt.Checked
        self.saveConfig()

    def updateDownsizeValue(self, value):
        try:
            self.downsizeValue = int(value)
        except ValueError:
            self.downsizeValue = 800
        self.saveConfig()

    def updateThreadCount(self, value):
        self.threadCount = value
        self.threadPool.setMaxThreadCount(self.threadCount)
        self.saveConfig()

    def toggleProcessingViews(self, checked):
        self.folderListWidget.setVisible(checked)
        self.processingFilesTextBox.setVisible(checked)
        self.selectFolderButton.setVisible(checked)
        self.removeFolderButton.setVisible(checked)
        self.removeAllFoldersButton.setVisible(checked)
        self.includeSubfoldersCheckBox.setVisible(checked)
        self.processFoldersButton.setVisible(checked)

    def processClipboardImage(self):
        clipboard = QApplication.clipboard()
        clipboardImage = clipboard.image()
        if not clipboardImage.isNull():
            self.lastImage = clipboardImage
            if self.downsizeCheckBox.isChecked():
                clipboardImage = self.downsizeImageToSmallestSide(clipboardImage)
            modifiedImage = self.applyTextToImage(clipboardImage)
            clipboard.setImage(modifiedImage)
            self.showMessage("Success", "Image processed and updated on the clipboard.")
            self.displayImage(modifiedImage)
        elif self.lastImage is not None:
            clipboard.setImage(self.lastImage)
            self.showMessage("Info", "Restored the last image as no image was found on the clipboard.")
            self.displayImage(self.lastImage)
        else:
            self.showMessage("Error", "No image found on the clipboard.")

    def selectFolders(self):
        selected_folder = QFileDialog.getExistingDirectory(self, "Select Folder", "", QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if selected_folder:
            subfolders = [os.path.join(selected_folder, f) for f in os.listdir(selected_folder) if os.path.isdir(os.path.join(selected_folder, f))]
            for folder in subfolders:
                if folder not in self.selectedFolders:
                    self.selectedFolders.append(folder)
                    item = QListWidgetItem(folder)
                    self.folderListWidget.addItem(item)
            self.saveSelectedFolders()

    def removeSelectedFolders(self):
        selected_items = self.folderListWidget.selectedItems()
        for item in selected_items:
            folder = item.text()
            if folder in self.selectedFolders:
                self.selectedFolders.remove(folder)
            self.folderListWidget.takeItem(self.folderListWidget.row(item))
        self.saveSelectedFolders()

    def removeAllFolders(self):
        self.selectedFolders.clear()
        self.folderListWidget.clear()
        self.saveSelectedFolders()

    def showFolderListContextMenu(self, position):
        menu = QMenu()
        removeAction = menu.addAction("Remove Selected")
        action = menu.exec_(self.folderListWidget.viewport().mapToGlobal(position))
        if action == removeAction:
            self.removeSelectedFolders()

    def startFolderProcessing(self):
        self.processFolders()

    def processFolders(self):
        if not self.selectedFolders:
            self.showMessage("Error", "No subfolders selected.")
            return

        self.completed_tasks = 0
        self.total_files = 0
        self.progressBar.setValue(0)
        self.progressLabel.setText("0/0")
        self.file_status.clear()

        image_files = []
        for folder in self.selectedFolders:
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                        file_path = os.path.join(root, file)
                        image_files.append(file_path)
                        self.file_status[file_path] = 'pending'
                if not self.includeSubfoldersCheckBox.isChecked():
                    break

        self.total_files = len(image_files)
        self.progressBar.setMaximum(self.total_files)
        self.updateProgress(0, self.total_files)

        if self.total_files == 0:
            self.showMessage("Info", "No image files found in the selected subfolders.")
            return

        for file_path in image_files:
            runnable = ImageProcessorRunnable(file_path, self)
            runnable.signals.progress.connect(self.updateProgress)
            runnable.signals.status_update.connect(self.updateFileStatus)
            self.threadPool.start(runnable)

        self.refreshProcessingList()

    def updateProgress(self, completed, total):
        self.progressBar.setValue(completed)
        self.progressLabel.setText(f"{completed}/{total}")

    def updateFileStatus(self, file_path, status):
        self.file_status[file_path] = status
        QTimer.singleShot(0, self.refreshProcessingList)

    def refreshProcessingList(self):
        self.processingFilesTextBox.clear()
        for file_path, status in self.file_status.items():
            color = self.getStatusColor(status)
            text = f"{file_path} - {status.capitalize()}"
            self.appendTextWithColor(self.processingFilesTextBox, text, color)

    def getStatusColor(self, status):
        if status == 'pending':
            return QColor(255, 255, 255)
        elif status == 'processing':
            return QColor(255, 255, 224)
        elif status == 'success':
            return QColor(144, 238, 144)
        elif status == 'failed':
            return QColor(255, 102, 102)
        else:
            return QColor(255, 255, 255)

    def appendTextWithColor(self, textbox, text, color):
        cursor = textbox.textCursor()
        cursor.movePosition(QTextCursor.End)
        format_ = cursor.charFormat()
        format_.setForeground(color)
        cursor.insertText(text + '\n', format_)
        textbox.setTextCursor(cursor)
        textbox.ensureCursorVisible()

    def downsizeImageToSmallestSide(self, image):
        width = image.width()
        height = image.height()
        smallest_side = min(width, height)
        if smallest_side > self.downsizeValue:
            scaling_factor = self.downsizeValue / smallest_side
            new_width = int(width * scaling_factor)
            new_height = int(height * scaling_factor)
            return image.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return image

    def applyTextToImage(self, image):
        pixmap = QPixmap.fromImage(image)
        painter = QPainter(pixmap)

        shortest_side = min(pixmap.width(), pixmap.height())
        relative_font_size = int(self.fontSize * (shortest_side / 1000))
        painter.setFont(QFont(self.fontFamily, relative_font_size))
        painter.setPen(self.textColor)

        textRect = QRect(0, int((1 - self.textYOffsetRatio) * pixmap.height()), pixmap.width(), int(self.textYOffsetRatio * pixmap.height()))
        painter.drawText(textRect, Qt.AlignCenter, self.customText)
        painter.end()

        return pixmap.toImage()

    def pickTextColor(self):
        color = QColorDialog.getColor(self.textColor, self)
        if color.isValid():
            self.textColor = color
            self.saveConfig()
            self.displayImage()

    def loadConfig(self):
        try:
            with open(self.configPath, 'r') as f:
                config = json.load(f)
                self.fontFamily = config.get('fontFamily', 'Arial')
                self.fontSize = config.get('fontSize', 30)
                self.customText = config.get('customText', 'Sample Text')
                self.textColor = QColor(config.get('textColor', '#FFFFFF'))
                self.textYOffsetRatio = config.get('textYOffsetRatio', 0.1)
                self.downsizeImage = config.get('downsizeImage', False)
                self.downsizeValue = config.get('downsizeValue', 800)
                self.threadCount = config.get('threadCount', 10)
                self.savedFolders = config.get('selectedFolders', [])
        except Exception:
            self.fontFamily = 'Arial'
            self.fontSize = 30
            self.customText = 'Sample Text'
            self.textColor = QColor(255, 255, 255)
            self.textYOffsetRatio = 0.1
            self.downsizeImage = False
            self.downsizeValue = 800
            self.threadCount = 10
            self.savedFolders = []

        self.threadPool.setMaxThreadCount(self.threadCount)

    def saveConfig(self):
        config = {
            'fontFamily': self.fontFamily,
            'fontSize': self.fontSize,
            'customText': self.customText,
            'textColor': self.textColor.name(),
            'textYOffsetRatio': self.textYOffsetRatio,
            'downsizeImage': self.downsizeImage,
            'downsizeValue': self.downsizeValue,
            'threadCount': self.threadCount,
            'selectedFolders': self.selectedFolders
        }
        os.makedirs(os.path.dirname(self.configPath), exist_ok=True)
        with open(self.configPath, 'w') as f:
            json.dump(config, f)

    def saveSelectedFolders(self):
        self.saveConfig()

    def loadSavedFolders(self):
        for folder in self.savedFolders:
            if os.path.isdir(folder):
                self.selectedFolders.append(folder)
                item = QListWidgetItem(folder)
                self.folderListWidget.addItem(item)

    def closeEvent(self, event):
        self.saveConfig()
        event.accept()

    def displayImage(self, image=None):
        if threading.current_thread() != threading.main_thread():
            QTimer.singleShot(0, lambda: self.displayImage(image))
            return

        if isinstance(image, QImage):
            pixmap = QPixmap.fromImage(image)
        else:
            clipboard = QApplication.clipboard()
            clipboardImage = clipboard.image()
            if not clipboardImage.isNull():
                pixmap = QPixmap.fromImage(clipboardImage)
            else:
                self.imageLabel.clear()
                return

        max_height = 500
        if pixmap.height() > max_height:
            pixmap = pixmap.scaledToHeight(max_height, Qt.SmoothTransformation)

        self.imageLabel.setFixedHeight(pixmap.height())

        painter = QPainter(pixmap)
        shortest_side = min(pixmap.width(), pixmap.height())
        relative_font_size = int(self.fontSize * (shortest_side / 1000))
        painter.setFont(QFont(self.fontFamily, relative_font_size))
        painter.setPen(self.textColor)

        textRect = QRect(0, int((1 - self.textYOffsetRatio) * pixmap.height()), pixmap.width(), int(self.textYOffsetRatio * pixmap.height()))
        painter.drawText(textRect, Qt.AlignCenter, self.customText)
        painter.end()

        self.imageLabel.setPixmap(pixmap)

    def showMessage(self, title, message):
        QMessageBox.information(self, title, message)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.offset = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.offset is not None:
            self.move(self.pos() + event.pos() - self.offset)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.offset = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AutoTagger()
    ex.show()
    sys.exit(app.exec_())
