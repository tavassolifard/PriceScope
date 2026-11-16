from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CHECK_ICON = BASE_DIR / "assets" / "icons" / "check.svg"
def get_stylesheet():
    stylesheet =  """
        QScrollArea {
            border: none;
            background-color: #000000;
        }

        QScrollArea QWidget#qt_scrollarea_viewport {
            background-color: #000000;
        }

        QWidget#ScrollContent {
            background-color: #000000;
        }

        QMainWindow {
            background-color: #000000;
        }

        QWidget {
            color: #DDDDDD;
            font-family: "Segoe UI";
            font-size: 13px;
        }

        QFrame#ProductCard {
            background-color: #111111;
            border: 1px solid #292929;
            border-radius: 12px;
        }

        QFrame#StoreCard {
            background-color: #191919;
            border: 1px solid #303030;
            border-radius: 9px;
        }

        QLabel#SectionTitle {
            font-size: 19px;
            font-weight: 700;
            color: #DDDDDD;
        }

        QLabel#Muted {
            color: #777777;
        }

        QPushButton {
            background-color: #202020;
            border: 1px solid #333333;
            border-radius: 8px;
            padding: 9px 15px;
            color: #DDDDDD;
            outline: none;
        }

        QPushButton:hover {
            background-color: #303030;
            border-color: #CB2957;
        }

        QPushButton#AccentButton {
            background-color: #CB2957;
            border: none;
            color: white;
            font-weight: 600;
        }

        QPushButton#AccentButton:hover {
            background-color: #E03968;
        }

        QPushButton#IconButton {
            background: transparent;
            border: none;
            padding: 5px;
            color: #888888;
            font-size: 17px;
        }

        QPushButton#IconButton:hover {
            color: #CB2957;
            background-color: #252525;
        }

        QLineEdit {
            background-color: #191919;
            border: 1px solid #333333;
            border-radius: 8px;
            padding: 10px;
            color: #DDDDDD;
            selection-background-color: #CB2957;
        }

        QLineEdit:focus {
            border: 1px solid #CB2957;
        }

        QCheckBox {
            spacing: 8px;
            color: #BBBBBB;
        }

        QCheckBox::indicator {
            width: 15px;
            height: 15px;
            border-radius: 4px;
            background-color: #222222;
            border: 1px solid #555555;
        }

        QCheckBox::indicator:checked {
            background-color: #CB2957;
            border: 1px solid #CB2957;
            image: url(assets/icons/check.svg);
        }

        QScrollArea {
            border: none;
            background: transparent;
        }

        QScrollBar:vertical {
            background: #000000;
            width: 9px;
            margin: 2px;
            border: none;
        }

        QScrollBar::handle:vertical {
            background: #393939;
            border-radius: 4px;
            min-height: 30px;
        }

        QScrollBar::handle:vertical:hover {
            background: #CB2957;
        }

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
        }

        QScrollBar::groove:vertical {
            background: #000000;
        }

        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {
            background: #000000;
        }
        
        QMessageBox {
        background-color: #1E1E1E;
        }
        
        QMessageBox QLabel {
            color: white;
            background-color: transparent;
        }
        
        QMessageBox QPushButton {
            background-color: #CB2957;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 6px 16px;
            min-width: 70px;
        }
        
        QMessageBox QPushButton:hover {
            background-color: #E13B6B;
        }
        
        QMessageBox QPushButton:pressed {
            background-color: #A91F47;
        }
        
        QPushButton#IconButton:hover {
    background-color: #252525;
    border: 1px solid #CB2957;
    border-radius: 6px;
}
    """
    stylesheet = stylesheet.replace(
        "assets/icons/check.svg",
        CHECK_ICON.as_posix()
    )

    return stylesheet
