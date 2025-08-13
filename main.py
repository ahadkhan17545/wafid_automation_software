import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont
# from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QVBoxLayout, QLabel
from automation_worker import WafidAutomation

class WafidApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wafid Automation Tool")
        self.setGeometry(150, 150, 900, 500)
        self.layout = QVBoxLayout()

        self.label = QLabel("Upload Passport CSV")
        self.layout.addWidget(self.label)

        self.upload_btn = QPushButton("Select CSV")
        self.upload_btn.clicked.connect(self.select_file)
        self.layout.addWidget(self.upload_btn)

        self.start_btn = QPushButton("Start Automation")
        self.start_btn.clicked.connect(self.start_automation)
        self.layout.addWidget(self.start_btn)

        self.setLayout(self.layout)
        self.csv_path = None

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV Files (*.csv)")
        if file_path:
            self.csv_path = file_path
            self.label.setText(f"Selected: {file_path}")

    def start_automation(self):
        if self.csv_path:
            worker = WafidAutomation(self.csv_path)
            worker.run()
            self.label.setText("✅ Automation Completed")
        else:
            self.label.setText("⚠ Please select a CSV file first")


# def main():
#     app = QApplication(sys.argv)
#     window = QWidget()
#     window.setGeometry()
#     window.setWindowTitle("Wafid automation tool")
    

#     label = QLabel(window)
#     label.setText("hello world")
#     label.setFont(QFont("Aerial", 18))


#     window.show()
#     app.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WafidApp()
    window.show()
    sys.exit(app.exec_())
