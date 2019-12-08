from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, 
    QSplitter, QStyleFactory, QApplication, QMessageBox, QLabel, 
    QComboBox, QLineEdit, QPushButton, QCheckBox, QSlider, QLCDNumber,
    QPlainTextEdit, QMenuBar, QMainWindow, QFileDialog, QGraphicsDropShadowEffect,
    QAbstractButton, QProgressBar, QInputDialog, QDialog, QCompleter)
from PyQt5.QtCore import Qt, QSize, QCoreApplication
from PyQt5.QtGui import QIcon, QImage, QPalette, QBrush, QColor, QPixmap, QPainter

import re
import sys
import decoder
import winreg
import webbrowser
import subprocess

class GUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.buttons = {}
        self.decoder = None

        self.pattern = r"(.*)\(&([A-Z])\)"

        self.init_ui()

    def pick_lang(self):
        text = str(QFileDialog.getOpenFileName(self, "Select tree file", self.path_rotwk)[0])
        if text != "":
            self.lang.setText(text)

    def display_shortcut(self, text):
        if text in self.buttons:
            try:
                shortcut = re.findall(self.pattern, self.buttons[text])
                self.shortcut.setText(shortcut[0][1])
                self.has_shortcut = True
            except IndexError:
                self.shortcut.setText("")
                self.has_shortcut = False
            finally:
                self.shortcut.setEnabled(True)
        else:
            self.shortcut.setText("")
            self.shortcut.setEnabled(False)

    def set_new_shortcut(self):
        if not self.has_shortcut:
            self.buttons[self.search_box.text()] += f" (&{self.shortcut.text().upper()})"
            new_string = self.buttons[self.search_box.text()]
            self.has_shortcut = True
        else:
            new_string = re.sub(self.pattern, rf"\1(&{self.shortcut.text().upper()})", self.buttons[self.search_box.text()]) 
            self.buttons[self.search_box.text()] = new_string

        QMessageBox.information(self, "Success", f"Successfully set <b>{self.search_box.text()}</b> to <b>{self.shortcut.text().upper()}</b>", QMessageBox.Ok, QMessageBox.Ok)

    def save_changes(self):
        name = ""
        for line in self.lines:
            if not line.lower().startswith(("controlbar", '"', "end")):
                continue

            if line.startswith("CONTROLBAR"):
                name = line.split(":")[1]
            elif line.startswith('"') and name is not None:
                self.lines[self.lines.index(line)] = f'"{self.buttons[name]}"'    
            elif line.lower().startswith("end"):
                name = None

        string = "\n".join(self.lines).encode("latin-1")
        with open("data/lotr.str", "wb") as f:
            f.write(string)

        QMessageBox.information(self, "Success", "Successfully saved changes please drag the data folder created into the file that is about to open. Once you've dragged it make sure to press save before closing.", QMessageBox.Ok, QMessageBox.Ok)
        subprocess.call(["FinalBIG.exe", self.lang.text()])
        QMessageBox.information(self, "Success", "Given that you have properly pressed saved all your shortcuts have been saved. Thank you for using this system")
        self.close()

    def encode_change(self):
        pass

    def stage_one_enable(self, value):
        self.lang.setEnabled(value)
        self.pick_lang_btn.setEnabled(value)
        self.edit_btn.setEnabled(value)

    def stage_two_enable(self, value):
        self.search_box.setEnabled(value)
        self.shortcut.setEnabled(value)
        self.new_shortcut_btn.setEnabled(value)

    def decode(self):
        self.stage_one_enable(False)
        try:
            self.decoder = decoder.Decoder(self.lang.text())
            self.lines = self.decoder.get_strings().splitlines()
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok, QMessageBox.Ok)
            self.stage_one_enable(True)
            return
        except IndexError:
            QMessageBox.critical(self, "Error", "Could not find a lotr.str in the file", QMessageBox.Ok, QMessageBox.Ok)

        self.decoder.file.close()

        name = ""
        for line in self.lines:
            if not line.lower().startswith(("controlbar", '"', "end")):
                continue

            if line.startswith("CONTROLBAR"):
                name = line.split(":")[1]
            elif line.startswith('"') and name is not None:
                self.buttons[name] = line[1:-2]
            elif line.lower().startswith("end"):
                name = None

        QMessageBox.information(self, "Done", "Done decoding, you may now begin editing shortcuts below", QMessageBox.Ok, QMessageBox.Ok)
        self.stage_two_enable(True)
        self.search_box.setCompleter(QCompleter(self.buttons.keys()))

    def init_ui(self):
        try:
            reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            key = winreg.OpenKey(reg, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\lotrbfme2ep1.exe")
            self.path_rotwk = winreg.EnumValue(key, 5)[1]
        except FileNotFoundError:
            self.path_rotwk = "C:\\Users\\Admin\\Desktop\\Mini-Libs\\custom_shortcuts"
            # QMessageBox.critical(self, "Error", "Could not locate ROTWK installation. Make sure ROTWK is installed", QMessageBox.Ok, QMessageBox.Ok)
            # self.close()

        label = QLabel("Select your lang file:", self)
        label.move(25, 55)
        label.adjustSize()

        self.lang = QLineEdit(self)
        self.lang.resize(600, 30)
        self.lang.move(25, 80)

        self.pick_lang_btn = QPushButton("...", self)
        self.pick_lang_btn.resize(25, 25)
        self.pick_lang_btn.move(635, 85)
        self.pick_lang_btn.clicked.connect(self.pick_lang)

        self.edit_btn = QPushButton("Edit Shortcuts", self)
        self.edit_btn.resize(150, 50)
        self.edit_btn.move(275, 125)
        self.edit_btn.clicked.connect(self.decode)        

        label = QLabel("Search by name:", self)
        label.move(25, 200)
        label.adjustSize()

        self.search_box = QLineEdit(self)
        self.search_box.resize(300, 30)
        self.search_box.move(25, 225)
        self.search_box.textChanged.connect(self.display_shortcut)

        label = QLabel("Shortcut:", self)
        label.move(350, 200)
        label.adjustSize()

        self.shortcut = QLineEdit(self)
        self.shortcut.resize(60, 30)
        self.shortcut.move(350, 225)
        self.shortcut.setMaxLength(1)

        self.new_shortcut_btn = QPushButton("Set Shortcut", self)
        self.new_shortcut_btn.resize(120, 30)
        self.new_shortcut_btn.move(450, 225)
        self.new_shortcut_btn.clicked.connect(self.set_new_shortcut)

        self.save_btn = QPushButton("Save Changes", self)
        self.save_btn.resize(150, 50)
        self.save_btn.move(275, 275)
        self.save_btn.clicked.connect(self.save_changes)

        self.stage_two_enable(False)
        self.setFixedSize(700, 400)
        self.setWindowTitle('Hotkey Customizer')
        self.show()

        # self.lang.setText("C:\\Users\\Admin\\Desktop\\Mini-Libs\\custom_shortcuts\\_a999_EDAIN.big")
        # self.decode()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    gui = GUI()
    app.exec_()

