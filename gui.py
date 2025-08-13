import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont
import random
from automation_worker import WafidComWorker, get_proxy_list

class WafidApp(QWidget):
    def __init__(self):
        super(WafidApp, self).__init__()
        self.setWindowTitle("Wafid Automation Tool")
        self.setGeometry(100, 100, 500, 300)

        # Apply global style
        self.setStyleSheet("""
            QWidget {
                background-color: #f4f5f6;
                font-family: Arial, sans-serif;
                font-size: 14px;
                color: #333;
            }
            QLineEdit {
                border: 1px solid #333333;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #333333;
                background-color: #ffffff;
            }
            QPushButton#actionBtn {
                background-color: #656E77;
                color: white;
                border: none;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
                margin-top: 10px;           
            }
            QPushButton#actionBtn:hover {
                background-color: #000000;
            }
            QPushButton#actionBtn:pressed {
                background-color: #656E77;
            }
            QTabWidget::pane {
                border: 1px solid #ccc;
                background: white;
                border-radius: 6px;
                padding: 5px;
            }
            QTabBar::tab {
                background: #e0e0e0;
                border: 1px solid #ccc;
                width: 110px;
                text-align: center;
                padding: 8px 15px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #0078d7;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background: #d0d0d0;
            }
        """)

        self.center_window()

        # Main layout
        main_layout = QVBoxLayout()

        # Create tab widget
        self.tabs = QTabWidget()

        # Add pages
        self.tabs.addTab(self.create_automation_tab(), "Automation")
        self.tabs.addTab(self.create_settings_tab(), "Settings")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
        self.csv_path = None

    def create_automation_tab(self):
        """Create the first tab for automation setup"""
        tab = QWidget()
        layout = QVBoxLayout()

        self.display_label = QLabel("Upload Passport CSV")
        layout.addWidget(self.display_label)
        
        self.target_input_field = QLineEdit()
        self.target_input_field.setPlaceholderText("Enter the target medical center")
        layout.addWidget(self.target_input_field)

        self.upload_btn = QPushButton("Select CSV")
        self.upload_btn.clicked.connect(self.select_file)
        self.upload_btn.setObjectName("actionBtn")
        layout.addWidget(self.upload_btn)

        self.start_btn = QPushButton("Start Automation")
        self.start_btn.clicked.connect(self.start_automation)
        self.start_btn.setObjectName("actionBtn")
        layout.addWidget(self.start_btn)

        tab.setLayout(layout)
        return tab

    def create_settings_tab(self):
        """Create the second tab for settings"""
        tab = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Settings Page"))
        layout.addWidget(QLabel("Here you can add configuration options."))

        tab.setLayout(layout)
        return tab

    def center_window(self):
        qtRecangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRecangle.moveCenter(centerPoint)
        self.move(qtRecangle.topLeft())
    
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV Files (*.csv)")
        if file_path:
            self.csv_path = file_path
            self.display_label.setText(f"Selected: {file_path}")

    def start_automation(self):
        proxies = get_proxy_list()
        proxy = random.choice(proxies)
        if self.csv_path:
            target_center = self.target_input_field.text()
            if not target_center:
                QMessageBox.warning(self, "Warning", "Enter the target center to continue")
                return    
            worker = WafidComWorker(self.csv_path, target_center, headless=False)
            worker.run()
            self.display_label.setText("✅ Automation Completed")
        else:
            self.display_label.setText("⚠ Please select a CSV file first")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WafidApp()
    window.show()
    sys.exit(app.exec_())
