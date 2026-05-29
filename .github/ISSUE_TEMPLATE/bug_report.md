---
name: Bug Report
about: Create a detailed report to help us improve the Talent Intelligence Agent
title: '[BUG] <Brief description of the issue>'
labels: bug, triage-needed
assignees: ''

---

## 🐛 Bug Description
<!-- Provide a clear and concise description of what the bug is. Please include whether this is a UI bug, a backend API failure, or a DuckDB/Coral query error. -->

## 🔍 Steps To Reproduce
<!-- Provide a detailed list of steps to reproduce the behavior. -->
1. Go to the project root directory.
2. Check the `.env` file and note if `USE_MOCK_DATA` is set to `"true"` or `"false"`.
3. Start the FastAPI server using `uvicorn webapp.server:app --reload`.
4. Open the browser and navigate to `http://localhost:8000`.
5. Perform action: [e.g., Clicked on 'Generate AI Intervention' for user X]
6. Observe error: [e.g., The loading spinner hangs forever, or a 500 Internal Server Error appears in the terminal].

## 🎯 Expected Behavior
<!-- A clear and concise description of what you expected to happen instead of the bug. -->

## 📸 Screenshots or Terminal Output
<!-- If applicable, add screenshots of the UI. If it is a backend error, PLEASE copy and paste the terminal traceback error here inside a code block. -->
```text
(Paste terminal error logs here)
```

## 🖥️ Environment Details
<!-- Please complete the following information to help us debug: -->
- **Operating System:** [e.g., macOS Sonoma, Ubuntu 22.04, Windows 11]
- **Python Version:** [e.g., Python 3.11.4]
- **Browser:** [e.g., Chrome 120, Safari 17]
- **Using Mock Data?**: [Yes / No]

## 🧠 Additional Context
<!-- Add any other context about the problem here. For example, did you hit a GitHub/Slack API rate limit? Did you change the engineers.jsonl roster file? -->
