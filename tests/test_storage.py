import sqlite3
import tempfile
import unittest
from pathlib import Path

from splittrip.storage import connect, initialize_database


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.db_path = Path(self.directory.name) / "test.db"
        initialize_database(self.db_path)

    def test_saved_trip_survives_reinitialization(self):
        connection = connect(self.db_path)
        try:
            with connection:
                connection.execute(
                    """
                    INSERT INTO trips
                        (name, destination, start_date, end_date)
                    VALUES (?, ?, ?, ?)
                    """,
                    ("Weekend", "Plovdiv", "2026-10-20", "2026-10-22"),
                )
        finally:
            connection.close()

        initialize_database(self.db_path)

        connection = connect(self.db_path)
        try:
            rows = connection.execute(
                "SELECT name, destination FROM trips"
            ).fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["name"], "Weekend")
            self.assertEqual(rows[0]["destination"], "Plovdiv")
        finally:
            connection.close()

    def test_participant_cannot_reference_missing_trip(self):
        connection = connect(self.db_path)
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                with connection:
                    connection.execute(
                        """
                        INSERT INTO participants (trip_id, name)
                        VALUES (?, ?)
                        """,
                        (999, "Martin"),
                    )
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()