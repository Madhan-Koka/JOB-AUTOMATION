"""
logger.py - Direct integration with Notion API via asynchronous HTTP requests.
"""

import httpx
from parser import ApplicationPayload

NOTION_VERSION = "2022-06-28"


class NotionLogger:
    def __init__(self, api_key: str, database_id: str):
        self.api_key = api_key
        self.database_id = database_id
        self.endpoint = "https://api.notion.com/v1/pages"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }

    async def log_application(self, payload: ApplicationPayload) -> bool:
        """
        Pushes a new page entry to the designated Notion database.
        Database schema expected:
          - Role (Title)
          - Company (Rich Text)
          - Status (Select)
          - URL (URL)
          - Notes (Rich Text)
        """
        if not self.api_key or not self.database_id:
            print("[Logger] Notion credentials not configured. Skipping remote log.")
            return False

        data = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Role": {
                    "title": [
                        {"type": "text", "text": {"content": payload.job.title[:100]}}
                    ]
                },
                "Company": {
                    "rich_text": [
                        {"type": "text", "text": {"content": payload.job.company[:100]}}
                    ]
                },
                "Status": {
                    "select": {
                        "name": payload.status
                    }
                },
                "URL": {
                    "url": payload.job.url if payload.job.url.startswith("http") else "https://example.com"
                },
                "Notes": {
                    "rich_text": [
                        {"type": "text", "text": {"content": (payload.notes or "")[:2000]}}
                    ]
                }
            }
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(self.endpoint, headers=self.headers, json=data)
                if response.status_code in [200, 201]:
                    print(f"[Logger] Successfully logged {payload.job.title} at {payload.job.company} to Notion.")
                    return True
                else:
                    print(f"[Logger] Failed to log to Notion. HTTP {response.status_code}: {response.text}")
                    return False
            except httpx.RequestError as exc:
                print(f"[Logger] Network error occurred while connecting to Notion: {exc}")
                return False