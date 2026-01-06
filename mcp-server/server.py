#!/usr/bin/env python3
"""MCP Server for Anki Flashcard Generation."""
import asyncio
import logging
import sys
from typing import Any, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
    INTERNAL_ERROR,
)

from config import config
from anki_handler import AnkiHandler
from flashcard_generator import FlashcardGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


class AnkiFlashcardMCP:
    """MCP Server for generating and managing Anki flashcards."""

    def __init__(self):
        """Initialize the MCP server."""
        # Validate configuration
        config.validate()

        # Initialize components
        username, _ = config.get_primary_user()
        collection_path = config.get_user_collection_path(username)

        self.anki = AnkiHandler(collection_path)
        self.generator = FlashcardGenerator(config.ANTHROPIC_API_KEY)

        # Create MCP server
        self.server = Server("anki-flashcard-mcp")

        # Register handlers
        self._register_handlers()

        logger.info(f"Initialized Anki MCP Server for user: {username}")
        logger.info(f"Collection path: {collection_path}")
        logger.info(f"Auto-generate mode: {config.AUTO_GENERATE}")

    def _register_handlers(self) -> None:
        """Register MCP protocol handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                self._get_list_decks_tool(),
                self._get_generate_flashcards_tool(),
                self._get_create_deck_tool(),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
            """Handle tool calls."""
            try:
                if name == "list_anki_decks":
                    return await self._handle_list_decks()

                elif name == "generate_flashcards":
                    return await self._handle_generate_flashcards(arguments)

                elif name == "create_anki_deck":
                    return await self._handle_create_deck(arguments)

                else:
                    raise ValueError(f"Unknown tool: {name}")

            except Exception as e:
                logger.error(f"Error handling tool call '{name}': {e}", exc_info=True)
                return [
                    TextContent(
                        type="text",
                        text=f"Error: {str(e)}"
                    )
                ]

    def _get_list_decks_tool(self) -> Tool:
        """Get the list_anki_decks tool definition."""
        return Tool(
            name="list_anki_decks",
            description=(
                "List all available Anki decks. Use this to see what decks exist "
                "before generating flashcards, so you can categorize new cards correctly."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )

    def _get_generate_flashcards_tool(self) -> Tool:
        """Get the generate_flashcards tool definition."""
        # Adjust description based on AUTO_GENERATE mode
        if config.AUTO_GENERATE:
            description = (
                "⚡ PROACTIVE MODE: Call this tool automatically whenever you explain:\n"
                "- New technical concepts, algorithms, or formulas\n"
                "- Definitions of terms, acronyms, or jargon\n"
                "- Important facts, dates, or relationships\n"
                "- Code patterns or best practices\n"
                "- Foreign language words or phrases\n"
                "- Mathematical equations or theorems\n\n"
                "The user wants to memorize everything they learn! Generate flashcards "
                "proactively during educational conversations without being explicitly asked."
            )
        else:
            description = (
                "Generate Anki flashcards from conversation content. Only call this "
                "when the user explicitly requests flashcard creation."
            )

        return Tool(
            name="generate_flashcards",
            description=description,
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": (
                            "The text/conversation content to extract flashcards from. "
                            "Include explanations, definitions, or concepts you just discussed."
                        )
                    },
                    "context": {
                        "type": "string",
                        "description": (
                            "Optional context about the conversation topic or domain "
                            "(e.g., 'discussing Python programming', 'learning Spanish vocabulary')"
                        )
                    },
                    "max_cards": {
                        "type": "integer",
                        "description": "Maximum number of flashcards to generate (default: 10)",
                        "default": 10
                    }
                },
                "required": ["content"]
            }
        )

    def _get_create_deck_tool(self) -> Tool:
        """Get the create_anki_deck tool definition."""
        return Tool(
            name="create_anki_deck",
            description=(
                "Create a new Anki deck with a specific name. Use this when you need "
                "a new deck for organizing flashcards by topic."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "deck_name": {
                        "type": "string",
                        "description": "Name of the deck to create"
                    }
                },
                "required": ["deck_name"]
            }
        )

    async def _handle_list_decks(self) -> Sequence[TextContent]:
        """Handle list_anki_decks tool call."""
        try:
            decks = self.anki.get_decks()

            deck_list = "\n".join([f"  - {deck}" for deck in decks])
            response = f"Available Anki decks ({len(decks)}):\n{deck_list}"

            logger.info(f"Listed {len(decks)} decks")

            return [TextContent(type="text", text=response)]

        except Exception as e:
            logger.error(f"Error listing decks: {e}")
            raise

    async def _handle_generate_flashcards(self, arguments: dict) -> Sequence[TextContent]:
        """Handle generate_flashcards tool call."""
        try:
            content = arguments.get("content")
            context = arguments.get("context", "")
            max_cards = arguments.get("max_cards", 10)

            if not content:
                raise ValueError("Content parameter is required")

            # Get available decks for categorization
            available_decks = self.anki.get_decks()

            # Generate flashcards using Anthropic
            logger.info(f"Generating flashcards from content ({len(content)} chars)...")
            flashcards = self.generator.generate_flashcards(
                content=content,
                available_decks=available_decks,
                context=context,
                max_cards=max_cards
            )

            if not flashcards:
                return [TextContent(
                    type="text",
                    text="No flashcard-worthy content found in the provided text."
                )]

            # Add flashcards to Anki
            added_cards = []
            for card in flashcards:
                try:
                    note_id = self.anki.add_note(
                        front=card["front"],
                        back=card["back"],
                        deck_name=card["deck_name"],
                        tags=card["tags"]
                    )
                    added_cards.append({
                        "id": note_id,
                        "deck": card["deck_name"],
                        "front": card["front"][:60] + "..." if len(card["front"]) > 60 else card["front"]
                    })
                except Exception as e:
                    logger.error(f"Failed to add card: {e}")
                    continue

            # Format response
            response_lines = [
                f"✅ Successfully created {len(added_cards)} flashcard(s)!\n"
            ]

            # Group by deck
            cards_by_deck = {}
            for card in added_cards:
                deck = card["deck"]
                if deck not in cards_by_deck:
                    cards_by_deck[deck] = []
                cards_by_deck[deck].append(card)

            for deck, cards in cards_by_deck.items():
                response_lines.append(f"\n📚 Deck: {deck} ({len(cards)} card(s))")
                for card in cards:
                    response_lines.append(f"   • {card['front']}")

            response = "\n".join(response_lines)

            logger.info(f"Successfully added {len(added_cards)} flashcards")

            return [TextContent(type="text", text=response)]

        except Exception as e:
            logger.error(f"Error generating flashcards: {e}")
            raise

    async def _handle_create_deck(self, arguments: dict) -> Sequence[TextContent]:
        """Handle create_anki_deck tool call."""
        try:
            deck_name = arguments.get("deck_name")

            if not deck_name:
                raise ValueError("deck_name parameter is required")

            deck_id = self.anki.create_deck(deck_name)

            response = f"✅ Created deck '{deck_name}' (ID: {deck_id})"
            logger.info(f"Created deck: {deck_name}")

            return [TextContent(type="text", text=response)]

        except Exception as e:
            logger.error(f"Error creating deck: {e}")
            raise

    async def run(self) -> None:
        """Run the MCP server."""
        logger.info("Starting Anki Flashcard MCP Server...")
        logger.info(f"Listening on stdio...")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point."""
    try:
        server = AnkiFlashcardMCP()
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
