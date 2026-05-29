"""GitHub Connector — SRP: only knows how to fetch GitHub data."""
from src.connectors.base import BaseConnector


class GitHubConnector(BaseConnector):
    @property
    def source_name(self) -> str:
        return "github"

    def _table_map(self) -> dict[str, str]:
        return {
            "commits": "github_commits.jsonl",
            "engineers": "engineers.jsonl",
        }

    def _fetch_live(self, table: str, filters: dict) -> list[dict]:
        """Fetch real data from GitHub."""
        import requests
        from datetime import datetime
        import uuid
        
        if table == "engineers":
            # For engineers, we still rely on the local mock/config file
            # as it acts as our master source of truth for the roster.
            return self._load_from_file(table)
            
        if table != "commits":
            return []

        # Get engineers to know whose commits to fetch
        engineers = self._load_from_file("engineers")
        handles = [e.get("github_handle") for e in engineers if e.get("github_handle")]
        
        token = self._settings.github_token
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"

        commits_data = []
        for handle in handles:
            url = f"https://api.github.com/users/{handle}/events/public?per_page=100"
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    events = response.json()
                    for event in events:
                        if event.get("type") == "PushEvent":
                            repo_name = event.get("repo", {}).get("name", "unknown")
                            created_at = event.get("created_at")
                            if created_at:
                                dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                                if (datetime.utcnow() - dt).days > 30:
                                    continue
                                
                                hour = dt.hour
                                is_after_hours = hour < 9 or hour >= 21
                                
                                # PushEvent payload can have multiple commits
                                payload_commits = event.get("payload", {}).get("commits", [])
                                if payload_commits:
                                    for commit in payload_commits:
                                        commits_data.append({
                                            "id": f"c_{uuid.uuid4().hex[:8]}",
                                            "author": handle,
                                            "repo": repo_name,
                                            "committed_at": created_at,
                                            "hour": hour,
                                            "is_after_hours": is_after_hours,
                                            "additions": 0, # Not provided in event payload
                                            "deletions": 0, # Not provided in event payload
                                            "pr_id": ""
                                        })
                                else:
                                    # Fallback: Record the push event itself if commits array is missing
                                    commits_data.append({
                                        "id": f"c_{uuid.uuid4().hex[:8]}",
                                        "author": handle,
                                        "repo": repo_name,
                                        "committed_at": created_at,
                                        "hour": hour,
                                        "is_after_hours": is_after_hours,
                                        "additions": 0,
                                        "deletions": 0,
                                        "pr_id": ""
                                    })
            except Exception as e:
                print(f"Failed to fetch GitHub commits for {handle}: {e}")
                
        return commits_data

    def _check_live_connection(self) -> bool:
        return bool(self._settings.github_token)
