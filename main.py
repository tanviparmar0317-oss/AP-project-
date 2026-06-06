import sys
from PySide6.QtWidgets import QApplication
from views.main_view import MainView


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainView()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
