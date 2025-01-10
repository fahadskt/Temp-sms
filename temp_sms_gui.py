import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QComboBox, QLabel, QPushButton, 
                           QListWidget, QTextEdit, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qt_material import apply_stylesheet
import json
from tempsms import (fetch_countries, fetch_numbers, fetch_sms, 
                    fetch_authkey, decrypt_key, copy_clipboard)

class Worker(QThread):
    """Worker thread for async operations"""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class TempSMSApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Temp SMS Receiver")
        self.setMinimumSize(800, 600)
        
        # Initialize main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create top section for country selection
        top_section = QHBoxLayout()
        self.country_combo = QComboBox()
        self.country_combo.setMinimumWidth(200)
        self.refresh_countries_btn = QPushButton("Refresh Countries")
        top_section.addWidget(QLabel("Select Country:"))
        top_section.addWidget(self.country_combo)
        top_section.addWidget(self.refresh_countries_btn)
        top_section.addStretch()
        layout.addLayout(top_section)
        
        # Create middle section for numbers
        middle_section = QHBoxLayout()
        
        # Numbers list
        numbers_layout = QVBoxLayout()
        numbers_header = QHBoxLayout()
        numbers_header.addWidget(QLabel("Available Numbers"))
        self.refresh_numbers_btn = QPushButton("Refresh Numbers")
        numbers_header.addWidget(self.refresh_numbers_btn)
        numbers_layout.addLayout(numbers_header)
        
        self.numbers_list = QListWidget()
        self.numbers_list.setMinimumWidth(300)
        numbers_layout.addWidget(self.numbers_list)
        middle_section.addLayout(numbers_layout)
        
        # SMS Messages
        messages_layout = QVBoxLayout()
        messages_layout.addWidget(QLabel("SMS Messages"))
        self.messages_area = QTextEdit()
        self.messages_area.setReadOnly(True)
        messages_layout.addWidget(self.messages_area)
        middle_section.addLayout(messages_layout)
        
        layout.addLayout(middle_section)
        
        # Create bottom section for status and actions
        bottom_section = QHBoxLayout()
        self.status_bar = QProgressBar()
        self.status_bar.setTextVisible(True)
        self.status_bar.setFormat("Ready")
        self.status_bar.setValue(0)
        self.copy_btn = QPushButton("Copy Number")
        bottom_section.addWidget(self.status_bar)
        bottom_section.addWidget(self.copy_btn)
        layout.addLayout(bottom_section)
        
        # Connect signals
        self.refresh_countries_btn.clicked.connect(self.load_countries)
        self.refresh_numbers_btn.clicked.connect(self.load_numbers)
        self.country_combo.currentIndexChanged.connect(self.on_country_changed)
        self.numbers_list.currentItemChanged.connect(self.on_number_selected)
        self.copy_btn.clicked.connect(self.copy_selected_number)
        
        # Initial load
        self.load_countries()
        
        # Apply material theme
        apply_stylesheet(self, theme='dark_teal.xml')
    
    def load_countries(self):
        self.status_bar.setFormat("Loading countries...")
        self.status_bar.setRange(0, 0)
        
        def on_finished(countries):
            self.country_combo.clear()
            for country in countries:
                self.country_combo.addItem(
                    f"{country['country_code']} - {country['Country_Name']}", 
                    country['Country_Name']
                )
            self.status_bar.setRange(0, 100)
            self.status_bar.setValue(100)
            self.status_bar.setFormat("Countries loaded")
        
        def on_error(error_msg):
            self.status_bar.setRange(0, 100)
            self.status_bar.setValue(0)
            self.status_bar.setFormat("Error loading countries")
            QMessageBox.critical(self, "Error", f"Failed to load countries: {error_msg}")
        
        worker = Worker(fetch_countries)
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        worker.start()
    
    def load_numbers(self):
        country = self.country_combo.currentData()
        if not country:
            return
        
        self.status_bar.setFormat("Loading numbers...")
        self.status_bar.setRange(0, 0)
        self.numbers_list.clear()
        
        def on_finished(data):
            numbers = data.get("Available_numbers", [])
            self.numbers_list.clear()
            for number in numbers:
                number_display = (number.get("E.164") or 
                                number.get("number") or 
                                number.get("phone_number", "Unknown"))
                self.numbers_list.addItem(number_display)
            self.status_bar.setRange(0, 100)
            self.status_bar.setValue(100)
            self.status_bar.setFormat("Numbers loaded")
        
        def on_error(error_msg):
            self.status_bar.setRange(0, 100)
            self.status_bar.setValue(0)
            self.status_bar.setFormat("Error loading numbers")
            QMessageBox.critical(self, "Error", f"Failed to load numbers: {error_msg}")
        
        worker = Worker(fetch_numbers, country, 1)
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        worker.start()
    
    def on_country_changed(self, index):
        if index >= 0:
            self.load_numbers()
    
    def on_number_selected(self, current, previous):
        if not current:
            return
            
        number = current.text()
        self.status_bar.setFormat("Loading messages...")
        self.status_bar.setRange(0, 0)
        
        def on_finished(messages):
            self.messages_area.clear()
            for msg in messages:
                self.messages_area.append(
                    f"From: {msg['FromNumber']}\n"
                    f"Time: {msg['message_time']}\n"
                    f"Message: {msg['Messagebody']}\n"
                    f"{'-' * 50}\n"
                )
            self.status_bar.setRange(0, 100)
            self.status_bar.setValue(100)
            self.status_bar.setFormat("Messages loaded")
        
        def on_error(error_msg):
            self.status_bar.setRange(0, 100)
            self.status_bar.setValue(0)
            self.status_bar.setFormat("Error loading messages")
            QMessageBox.critical(self, "Error", f"Failed to load messages: {error_msg}")
        
        worker = Worker(fetch_sms, number)
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        worker.start()
    
    def copy_selected_number(self):
        current = self.numbers_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Warning", "Please select a number first")
            return
            
        number = current.text()
        result = copy_clipboard(number)
        if result[0]:
            self.status_bar.setFormat("Number copied to clipboard")
        else:
            QMessageBox.warning(self, "Warning", result[1])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TempSMSApp()
    window.show()
    sys.exit(app.exec()) 