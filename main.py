import sys
from PySide6.QtWidgets import QApplication
from views.main_view import MainView

STYLESHEET = """
QMainWindow {
    background-color: #f8f9fa;
}
QWidget {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
    color: #2d3748;
}
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #cbd5e0;
    border-radius: 6px;
    padding: 5px 8px;
}
QLineEdit:focus {
    border: 1px solid #3182ce;
}
QPushButton {
    background-color: #edf2f7;
    border: 1px solid #cbd5e0;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #e2e8f0;
}
QPushButton:pressed {
    background-color: #cbd5e0;
}
QPushButton:disabled {
    background-color: #f7fafc;
    color: #a0aec0;
    border-color: #edf2f7;
}
#connect_btn {
    background-color: #3182ce;
    color: white;
    border: 1px solid #2b6cb0;
}
#connect_btn:hover {
    background-color: #2b6cb0;
}
#connect_btn:pressed {
    background-color: #2c5282;
}
#connect_btn:disabled {
    background-color: #a0aec0;
    border-color: #a0aec0;
}
#disconnect_btn {
    background-color: #e53e3e;
    color: white;
    border: 1px solid #c53030;
}
#disconnect_btn:hover {
    background-color: #c53030;
}
#disconnect_btn:pressed {
    background-color: #9b2c2c;
}
#disconnect_btn:disabled {
    background-color: #feb2b2;
    border-color: #feb2b2;
}
QComboBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e0;
    border-radius: 6px;
    padding: 5px 24px 5px 12px;
}
QComboBox:hover {
    border-color: #a0aec0;
}
QRadioButton {
    spacing: 6px;
}
QRadioButton::indicator {
    width: 14px;
    height: 14px;
}
QLabel {
    font-weight: 500;
}
"""


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = MainView()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
