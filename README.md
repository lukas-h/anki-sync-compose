# Anki Sync Server + MCP Flashcard Generator

Self-hosted Anki sync server with an MCP (Model Context Protocol) server that automatically generates flashcards from your AI conversations using Claude.

## Features

### 🚀 Anki Sync Server
- Self-hosted sync server for Anki desktop and mobile apps
- Supports up to 5 users
- Persistent data storage

### 🤖 MCP Flashcard Generator
- **Automatic flashcard creation** from AI conversations
- Uses **Claude Sonnet** to intelligently extract key concepts
- **Proactive mode**: Auto-generates cards during educational discussions
- **Manual mode**: Create cards on-demand
- **Smart deck organization**: Reads existing decks for proper categorization
- **MCP Protocol**: Works with Claude, Claude Code, and other MCP-compatible AI tools

## Architecture

```
AI Chat (Claude/etc)
    ↓ MCP Protocol
MCP Flashcard Server
    ↓ Anthropic API
Claude (generates cards)
    ↓
Anki Collection
    ↓
Anki Sync Server
```

## Environment Variables

Configure these in the Coolify environment variables tab or in a `.env` file:

### Required Variables (Both Services)

- `SYNC_USER1` - First sync user credentials in format `username:password` (required)
- `ANTHROPIC_API_KEY` - Your Anthropic API key (required for MCP server)

### Optional Variables

**Sync Server:**
- `SYNC_USER2` through `SYNC_USER5` - Additional user credentials
- `SYNC_BASE` - Base path for sync data (default: `/syncserver`)
- `DATA_PATH` - Host path for data storage (default: `./syncserver`)
- `ANKI_VERSION` - Anki version to install (default: `24.06.3`)
- `ANKI_PACKAGE` - Anki package name (default: `anki-24.06.3-linux-qt6`)

**MCP Flashcard Server:**
- `AUTO_GENERATE` - Enable proactive flashcard generation (default: `true`)
  - `true` = AI automatically creates cards during educational conversations
  - `false` = Cards only created when explicitly requested
- `MCP_PORT` - HTTP/SSE port for MCP server (default: `3000`)

## Quick Start

### 1. Set Environment Variables

Create a `.env` file or set environment variables:

```bash
SYNC_USER1=myusername:mypassword
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
AUTO_GENERATE=true
```

### 2. Build and Run

```bash
# Build both services
docker compose build

# Start both services
docker compose up -d

# Check logs
docker compose logs -f mcp-flashcard-server
```

### 3. Connect Your AI Client

The MCP server runs on **stdio** by default, which works with:
- Claude Desktop
- Claude Code
- Goose
- Other MCP-compatible clients

#### Example: Claude Desktop Configuration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac):

```json
{
  "mcpServers": {
    "anki-flashcards": {
      "command": "docker",
      "args": ["exec", "-i", "anki-sync-compose-mcp-flashcard-server-1", "python", "/app/server.py"]
    }
  }
}
```

### 4. Use It!

**Proactive Mode (AUTO_GENERATE=true):**
Just have a conversation with your AI assistant about any topic:

```
You: "What is a binary search tree?"
Claude: "A binary search tree (BST) is..."
        [Automatically creates flashcard in your Anki deck]
Claude: "✅ I've added this to your Data Structures deck!"
```

**Manual Mode (AUTO_GENERATE=false):**
Explicitly request flashcard creation:

```
You: "Explain quicksort"
Claude: "Quicksort is..."
You: "Create flashcards for that"
Claude: [Creates flashcards]
```

## Coolify Deployment

### Step-by-Step Guide

1. **Create New Service** in Coolify
   - Click "Add New Resource" → "Service"
   - Select "Docker Compose" as the build pack

2. **Connect Repository**
   - Point to this repository: `https://github.com/lukas-h/anki-sync-compose`
   - Select branch: `main` (or your preferred branch)

3. **Configure Environment Variables** (CRITICAL!)

   Go to the **Environment Variables** tab and add these **required** variables:

   ```
   SYNC_USER1=myusername:mypassword
   ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxx
   ```

   **Optional variables** (recommended):
   ```
   AUTO_GENERATE=true
   MCP_PORT=3000
   DATA_PATH=/data/anki-sync
   ```

   ⚠️ **Important**: Both `SYNC_USER1` and `ANTHROPIC_API_KEY` are **required**. The deployment will fail without them.

4. **Configure Ports** (if needed)
   - MCP Server: Port `3000` (currently uses stdio, HTTP/SSE for future use)
   - Sync Server: Port `8080` (used by Anki clients)

5. **Deploy**
   - Click "Deploy"
   - Monitor build logs for any errors
   - First build will take 3-5 minutes

6. **Verify Deployment**
   ```bash
   # Check MCP server logs
   docker logs <container-name> | grep "Anki MCP Server"

   # Should see: "Initialized Anki MCP Server for user: myusername"
   ```

### Coolify Environment Variables Reference

| Variable | Required | Example | Purpose |
|----------|----------|---------|---------|
| `SYNC_USER1` | ✅ Yes | `john:secretpass123` | Anki sync credentials |
| `ANTHROPIC_API_KEY` | ✅ Yes | `sk-ant-api03-xxx...` | Claude API access |
| `AUTO_GENERATE` | No | `true` | Enable proactive flashcard mode |
| `MCP_PORT` | No | `3000` | MCP server port |
| `DATA_PATH` | No | `/data/anki-sync` | Persistent storage path |

### Troubleshooting Coolify Deployment

**Build fails with "exit code 8" or wget error:**
- This was an issue with Anki 25.09.2 - now fixed to use 24.06.3
- If you still see errors, check network connectivity in build container

**"Please set SYNC_USER1" error:**
- Go to Environment Variables tab in Coolify
- Add `SYNC_USER1` in format `username:password`
- Redeploy

**"Please set ANTHROPIC_API_KEY" error:**
- Get API key from: https://console.anthropic.com/
- Add to Coolify Environment Variables
- Format: `sk-ant-api03-...` (starts with `sk-ant-`)

**MCP server not starting:**
```bash
# Check logs in Coolify dashboard
docker logs mcp-flashcard-server

# Common issues:
# - Missing environment variables
# - Invalid API key format
# - Sync server not ready (wait 30 seconds and restart)
```

The MCP server will be available on port 3000 for future HTTP/SSE access (currently uses stdio).

## MCP Tools Available

The MCP server exposes three tools to AI assistants:

### 1. `list_anki_decks`
Lists all available Anki decks for proper categorization.

### 2. `generate_flashcards`
Generates flashcards from conversation content:
- Extracts key concepts, definitions, formulas
- Categorizes into appropriate decks
- Adds relevant tags
- Creates cards in Anki collection

**Parameters:**
- `content` (required): Text to extract flashcards from
- `context` (optional): Additional context about the topic
- `max_cards` (optional): Maximum cards to generate (default: 10)

### 3. `create_anki_deck`
Creates a new Anki deck with a specific name.

**Parameters:**
- `deck_name` (required): Name of the deck to create

## How It Works

1. **AI Conversation**: You discuss a topic with your AI assistant
2. **Content Detection**: The MCP server (via AI) identifies flashcard-worthy content
3. **Smart Generation**: Content is sent to Claude Sonnet with:
   - Available deck names for categorization
   - Best practices for flashcard creation
   - Instructions to extract key concepts
4. **Card Creation**: Generated flashcards are added to your Anki collection
5. **Sync**: Cards are immediately available for sync via the Anki sync server

## Advanced Configuration

### Custom Anki Collection Path

The MCP server automatically uses the primary user's collection from `SYNC_USER1`.

### Multiple Users

Set `SYNC_USER2` through `SYNC_USER5` for additional users. The MCP server uses the first user by default.

### Proactive vs Manual Mode

**Proactive Mode (`AUTO_GENERATE=true`):**
- Best for: Learning new topics, studying, educational conversations
- AI automatically creates flashcards during explanations
- Maximizes retention without explicit requests

**Manual Mode (`AUTO_GENERATE=false`):**
- Best for: General conversations where you want control
- Only creates cards when you explicitly ask
- Reduces unwanted card generation

## Local Development

### Build images

```bash
SYNC_USER1=user:pass ANTHROPIC_API_KEY=sk-ant-xxx docker compose build
```

### Run containers

```bash
SYNC_USER1=user:pass ANTHROPIC_API_KEY=sk-ant-xxx docker compose up -d
```

### View logs

```bash
# MCP server logs
docker compose logs -f mcp-flashcard-server

# Sync server logs
docker compose logs -f anki-sync-server
```

### Test MCP server manually

```bash
# Enter the container
docker compose exec mcp-flashcard-server bash

# Run Python interactively
python
>>> from anki_handler import AnkiHandler
>>> handler = AnkiHandler("/syncserver/myuser/collection.anki2")
>>> handler.get_decks()
```

## Troubleshooting

### MCP server not starting

Check logs:
```bash
docker compose logs mcp-flashcard-server
```

Common issues:
- Missing `ANTHROPIC_API_KEY` - Set your API key
- Missing `SYNC_USER1` - Set user credentials
- Invalid credentials format - Use `username:password`

### Flashcards not being created

1. Check AUTO_GENERATE setting
2. Verify Anthropic API key is valid
3. Check MCP server logs for errors
4. Ensure AI client is properly configured to use the MCP server

### Can't sync Anki desktop/mobile

1. Configure Anki to use your self-hosted sync server:
   - Go to Tools → Preferences → Syncing
   - Set sync server URL
   - Enter your `SYNC_USER1` credentials
2. Check sync server logs: `docker compose logs anki-sync-server`

### Collection database errors

If you see SQLite errors:
```bash
# Stop services
docker compose down

# Backup data
cp -r ./syncserver ./syncserver.backup

# Remove and recreate
rm -rf ./syncserver
docker compose up -d
```

## Performance Tips

- **Proactive Mode**: May generate many cards - review regularly in Anki
- **Rate Limits**: Anthropic API has rate limits - adjust `max_cards` if needed
- **Deck Organization**: Create topic-specific decks before starting to help AI categorize correctly

## Contributing

This project combines:
- [Anki](https://apps.ankiweb.net/) - Spaced repetition software
- [MCP](https://modelcontextprotocol.io/) - Model Context Protocol by Anthropic
- [Claude](https://anthropic.com/claude) - AI assistant for flashcard generation

## See Also

- [Anki Sync Server Documentation](https://docs.ankiweb.net/sync-server.html)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Anthropic API Documentation](https://docs.anthropic.com/)

## License

MIT
