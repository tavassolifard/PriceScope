from pathlib import Path

from PySide6.QtCore import (
    Qt, QSize, QPropertyAnimation, QEasingCurve
)
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QFrame, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QCheckBox
)


BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets" / "icons"
TRASH_ICON = ASSETS_DIR / "trash.svg"


STORES = {
    "Digikala": ("digikala", "digikala.png"),
    "Torob": ("torob", "torob.png"),
    "TechnoLife": ("technolife", "technolife.png"),
}


class ProductCard(QFrame):
    def __init__(
        self,
        name,
        active=True,
        config_id=None,
        urls=None,
        on_dirty=None,
        on_delete=None,
        parent=None
    ):
        super().__init__(parent)

        self.name = name
        self.config_id = str(config_id)
        self.on_delete = on_delete

        self.setObjectName("ProductCard")

        self.store_widgets = {}

        self.build_card(
            name=name,
            active=active,
            urls=urls or {},
            on_dirty=on_dirty
        )

    def build_card(self, name, active, urls, on_dirty):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(17, 13, 17, 15)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Product header
        header = QHBoxLayout()

        self.active_check = QCheckBox()
        self.active_check.setChecked(active)

        self.name_label = QLabel(name)
        self.name_label.setStyleSheet(
            "font-size: 14px; font-weight: 650;"
        )

        self.delete_button = QPushButton()
        self.delete_button.setIcon(QIcon(str(TRASH_ICON)))
        self.delete_button.setIconSize(QSize(20, 20))
        self.delete_button.setFixedSize(34, 34)
        self.delete_button.setObjectName("IconButton")

        self.expand_button = QPushButton()
        self.expand_button.setObjectName("IconButton")
        self.expand_button.setToolTip("Expand product")
        self.expand_button.setIcon(QIcon("config_builder/assets/icons/down_arrow.png"))
        self.expand_button.setIconSize(QSize(16, 16))

        header.addWidget(self.active_check)
        header.addWidget(self.name_label)
        header.addStretch()
        header.addWidget(self.delete_button)
        header.addWidget(self.expand_button)

        layout.addLayout(header)

        # Store sections
        self.stores_container = QWidget()

        stores_layout = QVBoxLayout(self.stores_container)
        stores_layout.setContentsMargins(0, 0, 0, 0)
        stores_layout.setSpacing(12)

        for store_name, (store_key, logo) in STORES.items():
            self.create_store_card(
                stores_layout,
                store_name,
                store_key,
                logo,
                urls,
                on_dirty
            )

        layout.addWidget(self.stores_container)

        self.stores_container.setMaximumHeight(16777215)

        self.setup_expand_animation()

        if on_dirty:
            self.active_check.toggled.connect(on_dirty)

        if self.on_delete:
            self.delete_button.clicked.connect(
                lambda checked=False: self.on_delete(self)
            )

    def create_store_card(
        self,
        stores_layout,
        store_name,
        store_key,
        logo,
        urls,
        on_dirty
    ):
        store_card = QFrame()
        store_card.setObjectName("StoreCard")

        store_layout = QVBoxLayout(store_card)
        store_layout.setContentsMargins(13, 12, 13, 12)
        store_layout.setSpacing(10)

        store_header = QHBoxLayout()

        logo_label = QLabel()
        pixmap = QPixmap(str(ASSETS_DIR / logo))

        logo_label.setPixmap(
            pixmap.scaled(
                QSize(50, 50),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

        logo_label.setFixedSize(50, 50)

        store_title = QLabel(store_name)
        store_title.setStyleSheet("font-weight: 650;")

        ai_check = QCheckBox("Use AI to find URL")

        url = urls.get(f"{store_key}_url")
        use_ai = url is None

        ai_check.setChecked(use_ai)

        store_header.addWidget(logo_label)
        store_header.addWidget(store_title)
        store_header.addStretch()
        store_header.addWidget(ai_check)

        url_input = QLineEdit()
        url_input.setPlaceholderText(
            "Paste product URL here..."
        )

        if url is not None:
            url_input.setText(str(url))

        url_input.setEnabled(not use_ai)

        ai_check.toggled.connect(
            lambda checked, field=url_input:
                field.setEnabled(not checked)
        )

        store_layout.addLayout(store_header)
        store_layout.addWidget(url_input)

        stores_layout.addWidget(store_card)

        self.store_widgets[store_key] = {
            "ai_check": ai_check,
            "url_input": url_input
        }

        if on_dirty:
            ai_check.toggled.connect(on_dirty)
            url_input.textChanged.connect(on_dirty)

    def setup_expand_animation(self):
        self.stores_container.setVisible(False)
        self.stores_container.setMaximumHeight(0)

        self.expand_animation = QPropertyAnimation(
            self.stores_container,
            b"maximumHeight",
            self
        )

        self.expand_animation.setDuration(300)
        self.expand_animation.setEasingCurve(
            QEasingCurve.Type.InOutCubic
        )

        self.expand_animation.finished.connect(
            lambda: self.stores_container.setVisible(False)
            if self.stores_container.maximumHeight() == 0
            else None
        )

        self.expand_button.clicked.connect(
            self.toggle_expand
        )

    def toggle_expand(self):
        animation = self.expand_animation
        container = self.stores_container

        animation.stop()

        if not container.isVisible():
            container.setVisible(True)

        start_height = container.maximumHeight()

        end_height = (
            container.sizeHint().height()
            if start_height == 0
            else 0
        )

        animation.setStartValue(start_height)
        animation.setEndValue(end_height)

        if end_height == 0:
            self.expand_button.setIcon(
                QIcon("config_builder/assets/icons/down_arrow.png")
            )
        else:
            self.expand_button.setIcon(
                QIcon("config_builder/assets/icons/up_arrow.png")
            )

        animation.start()

    def get_data(self):
        return {
            "config_id": self.config_id,
            "card": self,
            "name": self.name,
            "active_check": self.active_check,
            "name_label": self.name_label,
            "store_widgets": self.store_widgets,
        }