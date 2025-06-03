#!/usr/bin/env /Users/honeycomb/indesign_mcp/venv/bin/python
"""
InDesign MCP Server
Provides tools for text manipulation in Adobe InDesign via ExtendScript
"""

import asyncio
import subprocess
import json
import os
from typing import Any, Dict
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types


app = Server("indesign-mcp")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available InDesign text manipulation tools"""
    return [
        types.Tool(
            name="add_text",
            description="Add text to an InDesign document",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to add to the document"
                    },
                    "position": {
                        "type": "string",
                        "description": "Position to add text (start, end, or after_selection)",
                        "enum": ["start", "end", "after_selection"],
                        "default": "end"
                    }
                },
                "required": ["text"]
            }
        ),
        types.Tool(
            name="update_text",
            description="Update existing text in an InDesign document",
            inputSchema={
                "type": "object",
                "properties": {
                    "find_text": {
                        "type": "string",
                        "description": "Text to find and replace"
                    },
                    "replace_text": {
                        "type": "string",
                        "description": "Text to replace with"
                    },
                    "all_occurrences": {
                        "type": "boolean",
                        "description": "Replace all occurrences or just the first",
                        "default": False
                    }
                },
                "required": ["find_text", "replace_text"]
            }
        ),
        types.Tool(
            name="remove_text",
            description="Remove text from an InDesign document",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to remove from the document"
                    },
                    "all_occurrences": {
                        "type": "boolean",
                        "description": "Remove all occurrences or just the first",
                        "default": False
                    }
                },
                "required": ["text"]
            }
        ),
        types.Tool(
            name="get_document_text",
            description="Get all text content from the active InDesign document",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="indesign_status",
            description="Check InDesign application status and document information",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


async def execute_extendscript(script: str) -> Dict[str, Any]:
    """Execute ExtendScript in InDesign and return the result"""
    try:
        # Create a temporary script file
        script_path = "/tmp/indesign_script.jsx"
        with open(script_path, "w") as f:
            f.write(script)
        
        # Try different InDesign application names
        indesign_apps = [
            "Adobe InDesign 2025",
            "Adobe InDesign 2024",
            "Adobe InDesign 2023", 
            "Adobe InDesign CC 2024",
            "Adobe InDesign CC 2023",
            "Adobe InDesign"
        ]
        
        result = None
        for app_name in indesign_apps:
            try:
                cmd = [
                    "osascript", "-e", 
                    f'tell application "{app_name}" to do script alias POSIX file "{script_path}" language javascript'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    break
                    
            except subprocess.TimeoutExpired:
                continue
            except Exception:
                continue
        
        # Clean up the temporary file
        os.unlink(script_path)
        
        if result and result.returncode == 0:
            return {"success": True, "result": result.stdout.strip()}
        else:
            error_msg = result.stderr.strip() if result else "Could not find InDesign application"
            return {"success": False, "error": error_msg}
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Script execution timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[types.TextContent]:
    """Handle tool calls for InDesign text manipulation"""
    
    if name == "add_text":
        text = arguments["text"]
        position = arguments.get("position", "end")
        
        script = f'''
        try {{
            // Check if InDesign is running and has documents
            if (app.documents.length === 0) {{
                throw new Error("No documents are open in InDesign. Please open a document first.");
            }}
            
            var doc = app.activeDocument;
            if (!doc) {{
                throw new Error("No active document found. Please make sure a document is active.");
            }}
            
            // Check if document has text stories
            if (doc.stories.length === 0) {{
                throw new Error("Document has no text stories. Please add a text frame first.");
            }}
            
            var story = doc.stories[0];
            
            var insertionPoint;
            if ("{position}" === "start") {{
                insertionPoint = story.insertionPoints[0];
            }} else if ("{position}" === "end") {{
                insertionPoint = story.insertionPoints[-1];
            }} else {{
                insertionPoint = story.insertionPoints[-1];
            }}
            
            insertionPoint.contents = "{text}";
            "Text added successfully to " + doc.name;
        }} catch (e) {{
            "Error: " + e.message;
        }}
        '''
        
        result = await execute_extendscript(script)
        
        if result["success"]:
            return [types.TextContent(type="text", text=f"Successfully added text: '{text}'")]
        else:
            return [types.TextContent(type="text", text=f"Error adding text: {result['error']}")]
    
    elif name == "update_text":
        find_text = arguments["find_text"]
        replace_text = arguments["replace_text"]
        all_occurrences = arguments.get("all_occurrences", False)
        
        script = f'''
        try {{
            if (app.documents.length === 0) {{
                throw new Error("No documents are open in InDesign. Please open a document first.");
            }}
            
            var doc = app.activeDocument;
            if (!doc) {{
                throw new Error("No active document found.");
            }}
            
            app.findGrepPreferences = NothingEnum.nothing;
            app.changeGrepPreferences = NothingEnum.nothing;
            
            app.findGrepPreferences.findWhat = "{find_text}";
            app.changeGrepPreferences.changeTo = "{replace_text}";
            
            var found = doc.changeGrep({"true" if all_occurrences else "false"});
            
            app.findGrepPreferences = NothingEnum.nothing;
            app.changeGrepPreferences = NothingEnum.nothing;
            
            "Replaced " + found.length + " occurrence(s) in " + doc.name;
        }} catch (e) {{
            "Error: " + e.message;
        }}
        '''
        
        result = await execute_extendscript(script)
        
        if result["success"]:
            return [types.TextContent(type="text", text=f"Successfully updated text: {result['result']}")]
        else:
            return [types.TextContent(type="text", text=f"Error updating text: {result['error']}")]
    
    elif name == "remove_text":
        text = arguments["text"]
        all_occurrences = arguments.get("all_occurrences", False)
        
        script = f'''
        try {{
            if (app.documents.length === 0) {{
                throw new Error("No documents are open in InDesign. Please open a document first.");
            }}
            
            var doc = app.activeDocument;
            if (!doc) {{
                throw new Error("No active document found.");
            }}
            
            app.findGrepPreferences = NothingEnum.nothing;
            app.changeGrepPreferences = NothingEnum.nothing;
            
            app.findGrepPreferences.findWhat = "{text}";
            app.changeGrepPreferences.changeTo = "";
            
            var found = doc.changeGrep({"true" if all_occurrences else "false"});
            
            app.findGrepPreferences = NothingEnum.nothing;
            app.changeGrepPreferences = NothingEnum.nothing;
            
            "Removed " + found.length + " occurrence(s) from " + doc.name;
        }} catch (e) {{
            "Error: " + e.message;
        }}
        '''
        
        result = await execute_extendscript(script)
        
        if result["success"]:
            return [types.TextContent(type="text", text=f"Successfully removed text: {result['result']}")]
        else:
            return [types.TextContent(type="text", text=f"Error removing text: {result['error']}")]
    
    elif name == "get_document_text":
        script = '''
        try {
            if (app.documents.length === 0) {
                throw new Error("No documents are open in InDesign. Please open a document first.");
            }
            
            var doc = app.activeDocument;
            if (!doc) {
                throw new Error("No active document found.");
            }
            
            if (doc.stories.length === 0) {
                return "Document '" + doc.name + "' has no text content.";
            }
            
            var allText = "=== Content from '" + doc.name + "' ===\\n\\n";
            for (var i = 0; i < doc.stories.length; i++) {
                allText += "Story " + (i + 1) + ":\\n";
                allText += doc.stories[i].contents + "\\n\\n";
            }
            
            allText;
        } catch (e) {
            "Error: " + e.message;
        }
        '''
        
        result = await execute_extendscript(script)
        
        if result["success"]:
            return [types.TextContent(type="text", text=f"Document text content:\\n{result['result']}")]
        else:
            return [types.TextContent(type="text", text=f"Error getting document text: {result['error']}")]
    
    elif name == "indesign_status":
        script = '''
        try {
            var status = "=== InDesign Status ===\\n";
            status += "Application: " + app.name + " " + app.version + "\\n";
            status += "Documents open: " + app.documents.length + "\\n";
            
            if (app.documents.length > 0) {
                var doc = app.activeDocument;
                status += "Active document: " + doc.name + "\\n";
                status += "Document stories: " + doc.stories.length + "\\n";
                status += "Document pages: " + doc.pages.length + "\\n";
                
                if (doc.stories.length > 0) {
                    status += "\\nFirst story preview: " + doc.stories[0].contents.substring(0, 100) + "...\\n";
                }
            } else {
                status += "\\nNo documents are currently open.\\n";
                status += "Please open or create a document in InDesign.\\n";
            }
            
            status;
        } catch (e) {
            "Error checking InDesign status: " + e.message;
        }
        '''
        
        result = await execute_extendscript(script)
        
        if result["success"]:
            return [types.TextContent(type="text", text=result['result'])]
        else:
            return [types.TextContent(type="text", text=f"Error checking InDesign status: {result['error']}")]
    
    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as streams:
        await app.run(
            streams[0], streams[1], app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())