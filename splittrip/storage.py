import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "splittrip.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    destination TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id),
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id),
    author_id INTEGER NOT NULL REFERENCES participants(id),
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    scheduled_date TEXT,
    scheduled_time TEXT
);

CREATE TABLE IF NOT EXISTS votes (
    activity_id INTEGER NOT NULL REFERENCES activities(id),
    participant_id INTEGER NOT NULL REFERENCES participants(id),
    PRIMARY KEY (activity_id, participant_id)
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id),
    payer_id INTEGER NOT NULL REFERENCES participants(id),
    description TEXT NOT NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0)
);

CREATE TABLE IF NOT EXISTS expense_shares (
    expense_id INTEGER NOT NULL REFERENCES expenses(id),
    participant_id INTEGER NOT NULL REFERENCES participants(id),
    amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
    PRIMARY KEY (expense_id, participant_id)
);

CREATE TABLE IF NOT EXISTS settlements (
    id INTEGER PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id),
    sender_id INTEGER NOT NULL REFERENCES participants(id),
    receiver_id INTEGER NOT NULL REFERENCES participants(id),
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    CHECK (sender_id != receiver_id)
);

CREATE TRIGGER IF NOT EXISTS votes_same_trip_insert
BEFORE INSERT ON votes
FOR EACH ROW
WHEN NOT EXISTS (
    SELECT 1
    FROM activities a
    JOIN participants p ON p.trip_id = a.trip_id
    WHERE a.id = NEW.activity_id
      AND p.id = NEW.participant_id
)
BEGIN
    SELECT RAISE(ABORT, 'Vote participant must belong to activity trip');
END;

CREATE TRIGGER IF NOT EXISTS votes_same_trip_update
BEFORE UPDATE OF activity_id, participant_id ON votes
FOR EACH ROW
WHEN NOT EXISTS (
    SELECT 1
    FROM activities a
    JOIN participants p ON p.trip_id = a.trip_id
    WHERE a.id = NEW.activity_id
      AND p.id = NEW.participant_id
)
BEGIN
    SELECT RAISE(ABORT, 'Vote participant must belong to activity trip');
END;

CREATE TRIGGER IF NOT EXISTS expenses_same_trip_insert
BEFORE INSERT ON expenses
FOR EACH ROW
WHEN NOT EXISTS (
    SELECT 1 FROM participants
    WHERE id = NEW.payer_id
      AND trip_id = NEW.trip_id
)
BEGIN
    SELECT RAISE(ABORT, 'Payer must belong to expense trip');
END;

CREATE TRIGGER IF NOT EXISTS expenses_same_trip_update
BEFORE UPDATE OF trip_id, payer_id ON expenses
FOR EACH ROW
WHEN NOT EXISTS (
    SELECT 1 FROM participants
    WHERE id = NEW.payer_id
      AND trip_id = NEW.trip_id
)
BEGIN
    SELECT RAISE(ABORT, 'Payer must belong to expense trip');
END;
"""


def connect(db_path=DB_PATH):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(db_path=DB_PATH):
    connection = connect(db_path)
    try:
        with connection:
            connection.executescript(SCHEMA)
    finally:
        connection.close()