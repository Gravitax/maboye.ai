"""
Web tools

Provides tools for fetching and processing web content.
"""

from tools.tool_base import Tool, ToolMetadata, ToolParameter
from tools import web_ops

class FetchUrlTool(Tool):
    """Tool for retrieving web content"""
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="fetch_url",
            description="Fetch text content from a URL (documentation, raw files)",
            parameters=[
                ToolParameter(name="url", type=str, description="URL to fetch", required=True)
            ],
            category="web"
        )

    def execute(self, url: str) -> str:
        return web_ops.fetch_url(url)
