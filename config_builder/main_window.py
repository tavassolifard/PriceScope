import ctypes
import sys
from pathlib import Path

from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QTimer, QEvent
)
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea,
    QFileDialog, QMessageBox, QGraphicsOpacityEffect
)

from .product_card import ProductCard, STORES
from .config_manager import (
    build_config,
    load_config as read_config,
    save_config as write_config
)
from .styles import get_stylesheet


BASE_DIR = Path(__file__).resolve().parent.parent
icon_path = Path(__file__).parent / "assets" / "icons" / "icon.png"


class SmoothScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )

        scrollbar = self.verticalScrollBar()
        scrollbar.setMouseTracking(True)
        scrollbar.installEventFilter(self)

        self.opacity_effect = QGraphicsOpacityEffect(scrollbar)
        self.opacity_effect.setOpacity(0)
        scrollbar.setGraphicsEffect(self.opacity_effect)

        self.scrollbar_animation = QPropertyAnimation(
            self.opacity_effect, b"opacity", self
        )
        self.scrollbar_animation.setDuration(180)

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.setInterval(1000)
        self.hide_timer.timeout.connect(self.hide_scrollbar)

        scrollbar.valueChanged.connect(self.show_scrollbar)
        scrollbar.rangeChanged.connect(self.on_range_changed)

        self.animation = None

    def show_scrollbar(self, *args):
        if self.verticalScrollBar().maximum() <= 0:
            return

        self.scrollbar_animation.stop()
        self.scrollbar_animation.setStartValue(
            self.opacity_effect.opacity()
        )
        self.scrollbar_animation.setEndValue(1)
        self.scrollbar_animation.start()

        self.hide_timer.start()

    def hide_scrollbar(self):
        self.scrollbar_animation.stop()
        self.scrollbar_animation.setStartValue(
            self.opacity_effect.opacity()
        )
        self.scrollbar_animation.setEndValue(0)
        self.scrollbar_animation.start()

    def on_range_changed(self, minimum, maximum):
        if maximum > 0:
            self.show_scrollbar()
        else:
            self.hide_timer.stop()
            self.hide_scrollbar()

    def wheelEvent(self, event):
        self.show_scrollbar()

        scrollbar = self.verticalScrollBar()
        delta = event.angleDelta().y()
        target = scrollbar.value() - delta

        if self.animation:
            self.animation.stop()

        self.animation = QPropertyAnimation(
            scrollbar, b"value", self
        )
        self.animation.setDuration(350)
        self.animation.setStartValue(scrollbar.value())
        self.animation.setEndValue(
            max(
                scrollbar.minimum(),
                min(target, scrollbar.maximum())
            )
        )
        self.animation.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )
        self.animation.start()

        event.accept()

    def eventFilter(self, watched, event):
        if watched == self.verticalScrollBar():
            if event.type() in (
                QEvent.Type.Enter,
                QEvent.Type.MouseMove
            ):
                self.show_scrollbar()

            elif event.type() == QEvent.Type.Leave:
                self.hide_timer.start()

        return super().eventFilter(watched, event)


class DarkMessageBox(QMessageBox):
    def showEvent(self, event):
        super().showEvent(event)
        if sys.platform == "win32":
            hwnd = int(self.winId())
            value = ctypes.c_int(1)

            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                20,
                ctypes.byref(value),
                ctypes.sizeof(value)
            )


class ConfigBuilder(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Config Builder")
        self.setWindowIcon(QIcon(str(icon_path)))
        self.setMinimumSize(850, 700)
        self.resize(1050, 850)

        self.config_path = None
        self.products = []
        self.next_config_id = 1
        self.dirty = False

        self.setStyleSheet(get_stylesheet())

        self.build_ui()

    # --------------------------------------------------
    # ID MANAGEMENT
    # --------------------------------------------------

    def allocate_config_id(self):
        config_id = str(self.next_config_id)
        self.next_config_id += 1
        return config_id

    # --------------------------------------------------
    # UI
    # --------------------------------------------------


    def show_message(
            self,
            icon,
            title,
            text,
            buttons=QMessageBox.StandardButton.Ok,
            default_button=QMessageBox.StandardButton.NoButton
    ):
        msg = DarkMessageBox(self)
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(buttons)

        if default_button != QMessageBox.StandardButton.NoButton:
            msg.setDefaultButton(default_button)

        return msg.exec()


    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(32, 26, 32, 24)
        main_layout.setSpacing(22)

        # Header
        header = QHBoxLayout()
        title_area = QVBoxLayout()

        title = QLabel("Config Builder")
        title.setStyleSheet("font-size: 26px; font-weight: 750;")

        subtitle = QLabel(
            "Manage your product tracking configuration"
        )
        subtitle.setObjectName("Muted")

        title_area.addWidget(title)
        title_area.addWidget(subtitle)

        self.load_button = QPushButton("＋   Load Config")
        self.load_button.setMinimumHeight(40)
        self.load_button.clicked.connect(self.load_config)

        header.addLayout(title_area)
        header.addStretch()
        header.addWidget(self.load_button)

        main_layout.addLayout(header)

        # Products heading
        products_header = QHBoxLayout()

        products_title = QLabel("Products")
        products_title.setObjectName("SectionTitle")

        self.count_label = QLabel("00 products")
        self.count_label.setObjectName("Muted")

        products_header.addWidget(products_title)
        products_header.addStretch()
        products_header.addWidget(self.count_label)

        main_layout.addLayout(products_header)

        # Scrollable product list
        self.scroll_area = SmoothScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAutoFillBackground(True)
        self.scroll_area.viewport().setAutoFillBackground(True)

        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )

        self.scroll_area.setStyleSheet(
            "QScrollArea { background-color: #000000; }"
        )

        self.scroll_area.viewport().setStyleSheet(
            "background-color: #000000;"
        )

        scroll_content = QWidget()
        scroll_content.setObjectName("ScrollContent")

        self.products_layout = QVBoxLayout(scroll_content)
        self.products_layout.setContentsMargins(2, 2, 8, 2)
        self.products_layout.setSpacing(12)

        self.empty_state = QLabel(
            "No Configuration Loaded\n\n"
            "Load an existing configuration or add products "
            "to create a new one."
        )

        self.empty_state.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.empty_state.setMinimumHeight(350)
        self.empty_state.setStyleSheet("""
            color: #777777;
            font-size: 15px;
            line-height: 1.5;
        """)

        self.products_layout.addWidget(self.empty_state)
        self.products_layout.addStretch()

        self.scroll_area.setWidget(scroll_content)
        main_layout.addWidget(self.scroll_area, 1)

        # Add product row
        add_row = QHBoxLayout()

        self.product_input = QLineEdit()
        self.product_input.setPlaceholderText(
            "Enter product name..."
        )
        self.product_input.setMinimumHeight(42)
        self.product_input.returnPressed.connect(self.add_product)

        add_button = QPushButton("＋  Add Product")
        add_button.setObjectName("AccentButton")
        add_button.setMinimumHeight(42)
        add_button.clicked.connect(self.add_product)

        add_row.addWidget(self.product_input, 1)
        add_row.addWidget(add_button)

        main_layout.addLayout(add_row)

        # Bottom actions
        footer = QHBoxLayout()
        footer.addStretch()

        self.save_as_button = QPushButton("Save As")
        self.save_as_button.setMinimumWidth(110)
        self.save_as_button.clicked.connect(self.save_as)

        self.save_button = QPushButton("Save")
        self.save_button.setObjectName("AccentButton")
        self.save_button.setMinimumWidth(110)
        self.save_button.clicked.connect(self.save_config)

        footer.addWidget(self.save_as_button)
        footer.addWidget(self.save_button)

        main_layout.addLayout(footer)

        self.update_product_count()
        self.dirty = False

    # --------------------------------------------------
    # PRODUCT MANAGEMENT
    # --------------------------------------------------

    def add_product(self):
        name = self.product_input.text().strip()

        if not name:
            self.show_message(
                QMessageBox.Icon.Warning,
                "Missing product name",
                "Please enter a product name."
            )
            return

        self.add_product_card(
            name,
            config_id=self.allocate_config_id()
        )

        self.product_input.clear()
        self.mark_dirty()

    def add_product_card(
        self,
        name,
        active=True,
        config_id=None,
        urls=None
    ):
        if config_id is None:
            config_id = self.allocate_config_id()

        card = ProductCard(
            name=name,
            active=active,
            config_id=config_id,
            urls=urls,
            on_dirty=self.mark_dirty,
            on_delete=self.delete_product
        )

        self.products_layout.insertWidget(
            self.products_layout.count() - 1,
            card
        )

        self.products.append(card.get_data())

        self.update_product_count()

    def delete_product(self, card):
        product = next(
            (
                item for item in self.products
                if item["card"] is card
            ),
            None
        )

        if product is None:
            return

        answer = self.show_message(
            QMessageBox.Icon.Question,
            "Delete Product",
            f"Remove '{product['name']}' from this configuration?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.products.remove(product)

        self.products_layout.removeWidget(product["card"])
        product["card"].deleteLater()

        self.update_product_count()
        self.mark_dirty()

    def update_product_count(self):
        count = len(self.products)

        self.count_label.setText(
            f"{count:02d} products"
        )

        self.empty_state.setVisible(count == 0)

    # --------------------------------------------------
    # LOAD CONFIG
    # --------------------------------------------------

    def load_config(self):
        if not self.confirm_discard_changes():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Config",
            str(BASE_DIR),
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            products, loaded_next_id = read_config(file_path)

        except (OSError, ValueError, TypeError) as error:
            self.show_message(
                QMessageBox.Icon.Critical,
                "Load Error",
                str(error)
            )
            return

        # Remove current cards
        for product in self.products:
            self.products_layout.removeWidget(product["card"])
            product["card"].deleteLater()

        self.products.clear()

        # Keep IDs globally increasing
        self.next_config_id = loaded_next_id

        # Rebuild cards
        for product in products:
            urls = {
                f"{store_key}_url": product.get(
                    f"{store_key}_url"
                )
                for store_key, _ in STORES.values()
            }

            self.add_product_card(
                name=product["name"],
                active=product.get("active", True),
                config_id=str(product["config_id"]),
                urls=urls
            )

        self.config_path = Path(file_path)
        self.dirty = False
        self.update_product_count()

        self.show_message(
            QMessageBox.Icon.Information,
            "Config Loaded",
            "Configuration loaded successfully."
        )

    # --------------------------------------------------
    # SAVE CONFIG
    # --------------------------------------------------

    def save_config(self):
        if self.config_path is None:
            self.save_as()
            return

        self.write_config(self.config_path)

    def save_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Config As",
            str(BASE_DIR / "config.json"),
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        path = Path(file_path)

        if path.suffix.lower() != ".json":
            path = path.with_suffix(".json")

        self.write_config(path)

    def write_config(self, path):
        try:
            config = build_config(
                self.products,
                self.next_config_id
            )

            write_config(path, config)

        except (OSError, ValueError) as error:
            self.show_message(
                QMessageBox.Icon.Critical,
                "Save Error",
                str(error)
            )
            return

        self.config_path = path
        self.dirty = False

        self.show_message(
            QMessageBox.Icon.Information,
            "Saved",
            "Configuration saved successfully."
        )

    # --------------------------------------------------
    # UNSAVED CHANGES
    # --------------------------------------------------

    def mark_dirty(self, *args):
        self.dirty = True

    def confirm_discard_changes(self):
        if not self.dirty:
            return True

        answer = self.show_message(
            QMessageBox.Icon.Question,
            "Unsaved Changes",
            "You have unsaved changes. Continue without saving?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        return answer == QMessageBox.StandardButton.Yes

    def closeEvent(self, event):
        if self.confirm_discard_changes():
            event.accept()
        else:
            event.ignore()

    # --------------------------------------------------
    # WINDOW EFFECTS
    # --------------------------------------------------

    def showEvent(self, event):
        super().showEvent(event)
        if sys.platform == "win32":
            hwnd = int(self.winId())
            value = ctypes.c_int(1)

            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                20,
                ctypes.byref(value),
                ctypes.sizeof(value)
            )