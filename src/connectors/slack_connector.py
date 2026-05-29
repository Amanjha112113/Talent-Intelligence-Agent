"""Slack Connector — SRP: only knows how to fetch Slack data."""
from src.connectors.base import BaseConnector


class SlackConnector(BaseConnector):
    @property
    def source_name(self) -> str:
        return "slack"

    def _table_map(self) -> dict[str, str]:
        return {
            "messages": "slack_messages.jsonl",
        }

    def _fetch_live(self, table: str, filters: dict) -> list[dict]:
        """Fetch real data from Slack."""
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError
        import datetime
        import uuid
        import time

        if table != "messages":
            return []

        token = self._settings.slack_bot_token
        if not token or not token.startswith("xoxb"):
            print("Skipping Slack live fetch: invalid or missing SLACK_BOT_TOKEN.")
            return []
            
        client = WebClient(token=token)
        messages_data = []
        
        # We need the list of valid slack_ids to filter messages
        engineers_path = self._mock_dir / "engineers.jsonl"
        valid_slack_ids = set()
        if engineers_path.exists():
            import json
            with open(engineers_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        record = json.loads(line)
                        if record.get("slack_id"):
                            valid_slack_ids.add(record["slack_id"])
        
        try:
            # Get channels the bot is in
            result = client.conversations_list(types="public_channel", exclude_archived=True, limit=10)
            channels = result.get("channels", [])
            
            # Fetch last 30 days of messages
            oldest_ts = str(time.time() - (30 * 24 * 60 * 60))
            
            complaint_keywords = ["frustrated", "blocked", "tired", "broken", "failing", "annoying", "hate", "slow"]
            
            for channel in channels:
                channel_id = channel["id"]
                try:
                    history = client.conversations_history(
                        channel=channel_id,
                        oldest=oldest_ts,
                        limit=100
                    )
                    
                    for msg in history.get("messages", []):
                        user = msg.get("user")
                        if user in valid_slack_ids:
                            text = msg.get("text", "").lower()
                            is_complaint = any(kw in text for kw in complaint_keywords)
                            
                            messages_data.append({
                                "id": f"msg_{uuid.uuid4().hex[:8]}",
                                "slack_id": user,
                                "channel": channel.get("name", "unknown"),
                                "sent_at": datetime.datetime.fromtimestamp(float(msg.get("ts", 0))).isoformat() + "Z",
                                "message_length": len(text),
                                "is_reply": "thread_ts" in msg,
                                "response_latency_minutes": 5 if "thread_ts" in msg else 0, # Mapped arbitrarily for prototype
                                "sentiment": "negative" if is_complaint else "neutral",
                                "is_complaint": is_complaint
                            })
                except SlackApiError as e:
                    if e.response["error"] == "not_in_channel":
                        pass # Ignore channels the bot isn't in
                    else:
                        print(f"Slack API error reading history for {channel_id}: {e}")
                        
        except SlackApiError as e:
            print(f"Slack API error fetching channels: {e}")
            
        return messages_data

    def _check_live_connection(self) -> bool:
        return bool(self._settings.slack_bot_token)
