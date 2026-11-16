import sqlite3
from pathlib import Path

class Database:

    def __init__(self, db_path=None):
        if db_path is None:
            db_path = Path(__file__).resolve().parent / "price_monitoring.db"

        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_id TEXT NOT NULL,
                digikala_price INTEGER,
                torob_price INTEGER,
                technolife_price INTEGER,
                recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.connection.commit()

    def add_price_history(
        self,
        config_id,
        digikala_price=None,
        torob_price=None,
        technolife_price=None,
    ):
        self.cursor.execute("""
            INSERT INTO price_history (
                config_id,
                digikala_price,
                torob_price,
                technolife_price
            )
            VALUES (?, ?, ?, ?)
        """, (
            config_id,
            digikala_price,
            torob_price,
            technolife_price,
        ))

        self.connection.commit()
        return self.cursor.lastrowid

    def close(self):
        self.connection.close()
