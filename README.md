# InDesign MCP Server

A Model Context Protocol (MCP) server for interacting with Adobe InDesign through ExtendScript API. Enables text manipulation in InDesign documents via Claude Desktop.

## Features

- **Add Text**: Insert text at start, end, or after selection
- **Update Text**: Find and replace text with support for all occurrences
- **Remove Text**: Delete specific text from documents
- **Get Document Text**: Retrieve all text content from active document

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure Claude Desktop by adding to your `claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "indesign": {
         "command": "python3",
         "args": ["/Users/honeycomb/indesign_mcp/server.py"],
         "env": {}
       }
     }
   }
   ```

3. Ensure Adobe InDesign is installed and running

## Usage

The server provides four tools accessible through Claude Desktop:

### add_text
- `text`: Text to add
- `position`: "start", "end", or "after_selection" (default: "end")

### update_text  
- `find_text`: Text to find
- `replace_text`: Replacement text
- `all_occurrences`: Replace all instances (default: false)

### remove_text
- `text`: Text to remove
- `all_occurrences`: Remove all instances (default: false)

### get_document_text
Returns all text content from the active InDesign document.

## Requirements

- Python 3.7+
- Adobe InDesign (tested with 2025)
- macOS (uses osascript for InDesign communication)
- Active InDesign document

## How it Works

The server communicates with InDesign via ExtendScript through macOS osascript, executing JavaScript code within InDesign's environment for text manipulation operations.