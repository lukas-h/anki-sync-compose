"""Flashcard generator using Anthropic API."""
import json
import logging
from typing import List, Dict, Any
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class FlashcardGenerator:
    """Generates flashcards from conversation text using Claude."""

    def __init__(self, api_key: str):
        """Initialize flashcard generator.

        Args:
            api_key: Anthropic API key
        """
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"

    def generate_flashcards(
        self,
        content: str,
        available_decks: List[str],
        context: str = "",
        max_cards: int = 10
    ) -> List[Dict[str, Any]]:
        """Generate flashcards from conversation content.

        Args:
            content: The text/conversation to extract flashcards from
            available_decks: List of existing deck names for categorization
            context: Optional additional context about the conversation
            max_cards: Maximum number of flashcards to generate

        Returns:
            List of flashcard dicts with keys: front, back, deck_name, tags
        """
        prompt = self._build_prompt(content, available_decks, context, max_cards)

        try:
            logger.info("Generating flashcards with Anthropic API...")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract text from response
            response_text = response.content[0].text

            # Parse JSON response
            flashcards = self._parse_flashcards(response_text)

            logger.info(f"Generated {len(flashcards)} flashcards")
            return flashcards

        except Exception as e:
            logger.error(f"Error generating flashcards: {e}")
            raise

    def _build_prompt(
        self,
        content: str,
        available_decks: List[str],
        context: str,
        max_cards: int
    ) -> str:
        """Build the prompt for flashcard generation."""
        decks_list = ", ".join([f'"{deck}"' for deck in available_decks])

        prompt = f"""You are a flashcard creation expert. Your task is to extract key learning points from the provided content and create high-quality Anki flashcards.

**Available Anki Decks:** {decks_list}

**Content to process:**
{content}

{f"**Additional Context:** {context}" if context else ""}

**Instructions:**
1. Identify the most important concepts, facts, definitions, formulas, algorithms, or terms worth memorizing
2. Create clear, concise flashcards (max {max_cards} cards)
3. Follow these flashcard best practices:
   - Front: Clear question or prompt (avoid yes/no questions)
   - Back: Concise answer with key information
   - One concept per card (atomic)
   - Use simple, precise language
   - Include examples where helpful
4. Categorize each card into the most appropriate existing deck from the list above
5. If none of the existing decks fit well, suggest a new deck name that represents the topic
6. Add relevant tags for better organization (e.g., "formula", "definition", "algorithm", "concept")

**Important formatting rules:**
- For mathematical formulas, use LaTeX notation wrapped in \\(...\\) for inline or \\[...\\] for display
- For code snippets, use markdown code blocks with language specification
- Keep cards focused and avoid unnecessary complexity

**Output format:**
Return a JSON array of flashcard objects. Each object must have:
- "front": The question/prompt (string)
- "back": The answer/explanation (string)
- "deck_name": The target deck name (string) - use existing deck or suggest new one
- "tags": Array of relevant tag strings

Example output:
```json
[
  {{
    "front": "What is the time complexity of binary search?",
    "back": "O(log n) - because the search space is halved with each comparison",
    "deck_name": "Algorithms",
    "tags": ["algorithm", "complexity", "searching"]
  }},
  {{
    "front": "What does MCP stand for in the context of AI?",
    "back": "Model Context Protocol - a standardized protocol for providing context to Large Language Models",
    "deck_name": "Programming",
    "tags": ["ai", "protocol", "definition"]
  }}
]
```

**Return only the JSON array, no additional text or explanation.**
"""
        return prompt

    def _parse_flashcards(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse flashcards from API response.

        Args:
            response_text: Raw text response from API

        Returns:
            List of flashcard dicts
        """
        # Extract JSON from response (handle markdown code blocks)
        response_text = response_text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            # Remove first and last lines (``` markers)
            response_text = "\n".join(lines[1:-1])
            # Remove json language tag if present
            if response_text.startswith("json"):
                response_text = response_text[4:].strip()

        try:
            flashcards = json.loads(response_text)

            # Validate structure
            if not isinstance(flashcards, list):
                raise ValueError("Response must be a JSON array")

            validated_cards = []
            for card in flashcards:
                if not isinstance(card, dict):
                    logger.warning(f"Skipping invalid card (not a dict): {card}")
                    continue

                if "front" not in card or "back" not in card:
                    logger.warning(f"Skipping card missing front/back: {card}")
                    continue

                # Ensure required fields
                validated_card = {
                    "front": str(card["front"]),
                    "back": str(card["back"]),
                    "deck_name": str(card.get("deck_name", "Default")),
                    "tags": card.get("tags", [])
                }

                # Ensure tags is a list
                if not isinstance(validated_card["tags"], list):
                    validated_card["tags"] = []

                validated_cards.append(validated_card)

            return validated_cards

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON response from API: {e}")
