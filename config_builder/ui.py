import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from .main_window import ConfigBuilder


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    window = ConfigBuilder()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()