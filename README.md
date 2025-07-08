# Social MCP

A Model Context Protocol (MCP) server for social media integration, specifically Instagram transcript extraction using AssemblyAI.

## Prerequisites

### Install uv

**On Mac:**

```bash
brew install uv
```

**On Windows:**

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After installation on Windows, add uv to your PATH:

```cmd
set Path=C:\Users\nntra\.local\bin;%Path%
```

### Environment Setup

1. **Create a `.env` file** in the project root with your AssemblyAI API key:

```bash
# Get your API key from: https://www.assemblyai.com/
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
```

2. **Get your AssemblyAI API key**:
   - Sign up at [AssemblyAI](https://www.assemblyai.com/)
   - Go to your dashboard and copy your API key
   - Add it to the `.env` file

## Claude Desktop Integration

To use this MCP server with Claude Desktop, you need to add it to your Claude Desktop configuration.

1. Open your Claude Desktop configuration file:

   - **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the following configuration to your `mcpServers` section (replace `/path/to/your/social-mcp` with the actual path to this project folder):

```json
{
  "mcpServers": {
    "social": {
      "command": "/Users/your-username/.local/bin/uv",
      "args": ["--directory", "/path/to/your/social-mcp", "run", "main.py"]
    }
  },
  "globalShortcut": ""
}
```

**Important:** Make sure to replace:

- `/path/to/your/social-mcp` with the actual path to where you cloned/downloaded this project
- `/Users/your-username/.local/bin/uv` with the correct path to your uv installation (on Windows this would typically be `C:\Users\your-username\.local\bin\uv.exe`)

3. Save the file and restart Claude Desktop

## Usage

Once configured, the Social MCP server will be available in Claude Desktop. You can use it to:

- **Extract transcripts from Instagram videos/reels** by providing Instagram URLs
- Get timestamped transcriptions with speaker labels
- Process various Instagram URL formats (posts, reels, IGTV)

### Example

```
Extract transcript from: https://instagram.com/reel/ABC123/
```

The server will:

1. Extract the video URL from the Instagram post
2. Use AssemblyAI to transcribe the audio
3. Return a formatted transcript with timestamps and speaker labels

## Development

This project uses uv for dependency management. The dependencies are defined in `pyproject.toml` and the lockfile is `uv.lock`.

To run the server locally:

```bash
uv run main.py
```

## Features

- ✅ Instagram URL validation and processing
- ✅ Direct video URL extraction using instaloader
- ✅ AssemblyAI transcription with speaker labels
- ✅ Timestamp formatting
- ✅ Environment variable configuration
- ✅ Comprehensive error handling
