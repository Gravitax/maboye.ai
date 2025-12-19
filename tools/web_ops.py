"""
Web operations for agent system.
"""

import requests
from bs4 import BeautifulSoup

def fetch_url(url: str, timeout: int = 10) -> str:
    """
    Fetches the textual content of a URL.
    
    Args:
        url: The URL to fetch.
        timeout: Request timeout in seconds.
        
    Returns:
        Cleaned text content or error message.
    """
    try:
        headers = {'User-Agent': 'DevAgent/1.0'}
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Basic cleaning to avoid context saturation
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text()
        
        # Clean multiple empty lines
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return clean_text[:8000] # Security limit
    except Exception as e:
        return f"Error fetching URL: {str(e)}"
