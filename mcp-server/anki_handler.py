"""Anki collection handler for reading and writing flashcards."""
import os
import sqlite3
import time
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AnkiHandler:
    """Handler for Anki collection operations."""

    def __init__(self, collection_path: str):
        """Initialize Anki handler.

        Args:
            collection_path: Path to the Anki collection database
        """
        self.collection_path = collection_path
        self.ensure_collection_exists()

    def ensure_collection_exists(self) -> None:
        """Ensure the collection directory and database exist."""
        collection_dir = os.path.dirname(self.collection_path)
        os.makedirs(collection_dir, exist_ok=True)

        if not os.path.exists(self.collection_path):
            logger.info(f"Creating new Anki collection at {self.collection_path}")
            self._create_empty_collection()

    def _create_empty_collection(self) -> None:
        """Create an empty Anki collection database."""
        conn = sqlite3.connect(self.collection_path)
        cursor = conn.cursor()

        # Create necessary tables (simplified Anki schema)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS col (
                id INTEGER PRIMARY KEY,
                crt INTEGER NOT NULL,
                mod INTEGER NOT NULL,
                scm INTEGER NOT NULL,
                ver INTEGER NOT NULL,
                dty INTEGER NOT NULL,
                usn INTEGER NOT NULL,
                ls INTEGER NOT NULL,
                conf TEXT NOT NULL,
                models TEXT NOT NULL,
                decks TEXT NOT NULL,
                dconf TEXT NOT NULL,
                tags TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY,
                guid TEXT NOT NULL UNIQUE,
                mid INTEGER NOT NULL,
                mod INTEGER NOT NULL,
                usn INTEGER NOT NULL,
                tags TEXT NOT NULL,
                flds TEXT NOT NULL,
                sfld TEXT NOT NULL,
                csum INTEGER NOT NULL,
                flags INTEGER NOT NULL,
                data TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY,
                nid INTEGER NOT NULL,
                did INTEGER NOT NULL,
                ord INTEGER NOT NULL,
                mod INTEGER NOT NULL,
                usn INTEGER NOT NULL,
                type INTEGER NOT NULL,
                queue INTEGER NOT NULL,
                due INTEGER NOT NULL,
                ivl INTEGER NOT NULL,
                factor INTEGER NOT NULL,
                reps INTEGER NOT NULL,
                lapses INTEGER NOT NULL,
                left INTEGER NOT NULL,
                odue INTEGER NOT NULL,
                odid INTEGER NOT NULL,
                flags INTEGER NOT NULL,
                data TEXT NOT NULL
            )
        """)

        # Initialize collection with default data
        import json
        now = int(time.time() * 1000)

        default_model = {
            "1": {
                "id": 1,
                "name": "Basic",
                "type": 0,
                "flds": [
                    {"name": "Front", "ord": 0},
                    {"name": "Back", "ord": 1}
                ],
                "tmpls": [
                    {
                        "name": "Card 1",
                        "qfmt": "{{Front}}",
                        "afmt": "{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}",
                        "ord": 0
                    }
                ],
                "css": ".card { font-family: arial; font-size: 20px; text-align: center; color: black; background-color: white; }"
            }
        }

        default_decks = {
            "1": {"id": 1, "name": "Default", "mod": now}
        }

        cursor.execute("""
            INSERT INTO col (id, crt, mod, scm, ver, dty, usn, ls, conf, models, decks, dconf, tags)
            VALUES (1, ?, ?, 0, 11, 0, 0, 0, '{}', ?, ?, '{}', '{}')
        """, (now, now, json.dumps(default_model), json.dumps(default_decks)))

        conn.commit()
        conn.close()

    def get_decks(self) -> List[str]:
        """Get list of all deck names.

        Returns:
            List of deck names
        """
        try:
            conn = sqlite3.connect(self.collection_path)
            cursor = conn.cursor()

            cursor.execute("SELECT decks FROM col WHERE id = 1")
            result = cursor.fetchone()
            conn.close()

            if not result:
                return ["Default"]

            import json
            decks_data = json.loads(result[0])

            # Extract deck names
            deck_names = [deck["name"] for deck in decks_data.values()]
            return sorted(deck_names)

        except Exception as e:
            logger.error(f"Error reading decks: {e}")
            return ["Default"]

    def create_deck(self, deck_name: str) -> int:
        """Create a new deck.

        Args:
            deck_name: Name of the deck to create

        Returns:
            Deck ID
        """
        try:
            conn = sqlite3.connect(self.collection_path)
            cursor = conn.cursor()

            # Get current decks
            cursor.execute("SELECT decks, mod FROM col WHERE id = 1")
            result = cursor.fetchone()

            import json
            decks_data = json.loads(result[0])
            current_mod = result[1]

            # Check if deck already exists
            for deck_id, deck in decks_data.items():
                if deck["name"] == deck_name:
                    conn.close()
                    return int(deck_id)

            # Create new deck
            new_deck_id = max([int(did) for did in decks_data.keys()]) + 1
            now = int(time.time() * 1000)

            decks_data[str(new_deck_id)] = {
                "id": new_deck_id,
                "name": deck_name,
                "mod": now
            }

            # Update database
            cursor.execute(
                "UPDATE col SET decks = ?, mod = ? WHERE id = 1",
                (json.dumps(decks_data), now)
            )

            conn.commit()
            conn.close()

            logger.info(f"Created deck '{deck_name}' with ID {new_deck_id}")
            return new_deck_id

        except Exception as e:
            logger.error(f"Error creating deck: {e}")
            raise

    def add_note(
        self,
        front: str,
        back: str,
        deck_name: str = "Default",
        tags: Optional[List[str]] = None
    ) -> int:
        """Add a note (flashcard) to the collection.

        Args:
            front: Front of the card
            back: Back of the card
            deck_name: Name of the deck to add to
            tags: Optional list of tags

        Returns:
            Note ID
        """
        try:
            # Ensure deck exists
            deck_id = self.create_deck(deck_name)

            conn = sqlite3.connect(self.collection_path)
            cursor = conn.cursor()

            # Generate IDs
            import random
            import hashlib

            note_id = int(time.time() * 1000) + random.randint(0, 999)
            card_id = note_id + 1
            guid = hashlib.sha256(f"{note_id}{front}{back}".encode()).hexdigest()[:8]

            # Prepare data
            fields = f"{front}\x1f{back}"
            tags_str = " " + " ".join(tags or []) + " "
            now = int(time.time() * 1000)

            # Calculate checksum
            sfld = front[:64] if len(front) > 64 else front
            csum = int(hashlib.sha1(sfld.encode()).hexdigest()[:8], 16)

            # Insert note
            cursor.execute("""
                INSERT INTO notes (id, guid, mid, mod, usn, tags, flds, sfld, csum, flags, data)
                VALUES (?, ?, 1, ?, 0, ?, ?, ?, ?, 0, '')
            """, (note_id, guid, now, tags_str, fields, sfld, csum))

            # Insert card
            cursor.execute("""
                INSERT INTO cards (id, nid, did, ord, mod, usn, type, queue, due, ivl, factor, reps, lapses, left, odue, odid, flags, data)
                VALUES (?, ?, ?, 0, ?, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '')
            """, (card_id, note_id, deck_id, now))

            # Update collection modified time
            cursor.execute("UPDATE col SET mod = ? WHERE id = 1", (now,))

            conn.commit()
            conn.close()

            logger.info(f"Added note to deck '{deck_name}': {front[:50]}...")
            return note_id

        except Exception as e:
            logger.error(f"Error adding note: {e}")
            raise

    def add_notes_batch(self, notes: List[Dict[str, Any]]) -> List[int]:
        """Add multiple notes at once.

        Args:
            notes: List of dicts with keys: front, back, deck_name, tags

        Returns:
            List of note IDs
        """
        note_ids = []
        for note in notes:
            note_id = self.add_note(
                front=note["front"],
                back=note["back"],
                deck_name=note.get("deck_name", "Default"),
                tags=note.get("tags")
            )
            note_ids.append(note_id)

        return note_ids
