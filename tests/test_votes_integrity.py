import sqlite3
import unittest

from splittrip.storage import SCHEMA, connect


class VoteIntegrityTests(unittest.TestCase):
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

            INSERT INTO activities (id, trip_id, author_id, title)
            VALUES (1, 1, 1, 'Museum'), (2, 2, 2, 'Park');
        """)

    def test_same_trip_vote_is_allowed(self):
        self.db.execute(
            "INSERT INTO votes (activity_id, participant_id) VALUES (1, 1)"
        )
        count = self.db.execute("SELECT COUNT(*) FROM votes").fetchone()[0]
        self.assertEqual(count, 1)

    def test_cross_trip_vote_is_rejected(self):
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "Vote participant"
        ):
            self.db.execute(
                "INSERT INTO votes (activity_id, participant_id) VALUES (1, 2)"
            )
        count = self.db.execute("SELECT COUNT(*) FROM votes").fetchone()[0]
        self.assertEqual(count, 0)

    def test_changing_voter_to_another_trip_is_rejected(self):
        self.db.execute(
            "INSERT INTO votes (activity_id, participant_id) VALUES (1, 1)"
        )
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "Vote participant"
        ):
            self.db.execute(
                "UPDATE votes SET participant_id = 2 WHERE activity_id = 1"
            )
        voter = self.db.execute(
            "SELECT participant_id FROM votes WHERE activity_id = 1"
        ).fetchone()[0]
        self.assertEqual(voter, 1)

    def test_changing_activity_to_another_trip_is_rejected(self):
        self.db.execute(
            "INSERT INTO votes (activity_id, participant_id) VALUES (1, 1)"
        )
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "Vote participant"
        ):
            self.db.execute(
                "UPDATE votes SET activity_id = 2 WHERE participant_id = 1"
            )
        activity = self.db.execute(
            "SELECT activity_id FROM votes WHERE participant_id = 1"
        ).fetchone()[0]
        self.assertEqual(activity, 1)


if __name__ == "__main__":
    unittest.main()