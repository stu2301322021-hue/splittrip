import sqlite3
import unittest

from splittrip.storage import SCHEMA, connect


class ExpenseIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.db = connect(":memory:")
        self.addCleanup(self.db.close)
        self.db.executescript(SCHEMA)
        self.db.executescript("""
            INSERT INTO trips
                (id, name, destination, start_date, end_date)
            VALUES
                (1, 'Trip A', 'Sofia', '2026-10-14', '2026-10-15'),
                (2, 'Trip B', 'Plovdiv', '2026-10-14', '2026-10-15');

            INSERT INTO participants (id, trip_id, name)
            VALUES (1, 1, 'Ivan'), (2, 2, 'Maria');
        """)

    def add_valid_expense(self):
        self.db.execute("""
            INSERT INTO expenses
                (id, trip_id, payer_id, description, amount_cents)
            VALUES (1, 1, 1, 'Tickets', 1000)
        """)

    def test_same_trip_payer_is_allowed(self):
        self.add_valid_expense()
        count = self.db.execute(
            "SELECT COUNT(*) FROM expenses"
        ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_cross_trip_payer_is_rejected(self):
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "Payer must belong"
        ):
            self.db.execute("""
                INSERT INTO expenses
                    (trip_id, payer_id, description, amount_cents)
                VALUES (1, 2, 'Tickets', 1000)
            """)
        count = self.db.execute(
            "SELECT COUNT(*) FROM expenses"
        ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_changing_payer_to_another_trip_is_rejected(self):
        self.add_valid_expense()
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "Payer must belong"
        ):
            self.db.execute(
                "UPDATE expenses SET payer_id = 2 WHERE id = 1"
            )
        payer = self.db.execute(
            "SELECT payer_id FROM expenses WHERE id = 1"
        ).fetchone()[0]
        self.assertEqual(payer, 1)

    def test_changing_expense_trip_is_rejected(self):
        self.add_valid_expense()
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "Payer must belong"
        ):
            self.db.execute(
                "UPDATE expenses SET trip_id = 2 WHERE id = 1"
            )
        trip = self.db.execute(
            "SELECT trip_id FROM expenses WHERE id = 1"
        ).fetchone()[0]
        self.assertEqual(trip, 1)


if __name__ == "__main__":
    unittest.main()