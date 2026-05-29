# Contributing to the Talent Intelligence Agent

First off, thank you for considering contributing! The Talent Intelligence Agent is an open-source project dedicated to autonomously detecting engineer burnout, identifying "Silent Heroes", and preventing talent turnover using cross-platform data and AI.

## 🚀 Core Features You Can Contribute To
The project is divided into several distinct architectural domains. When contributing, you will likely work in one of these areas:

1. **The Connectors Layer (`src/connectors/`)**
   - **Current Feature:** Fetches REST API data from GitHub, Slack, and Google Calendar.
   - **How to Contribute:** You can build new Python connectors inheriting from `BaseConnector` (e.g., adding a Jira connector, a Linear connector, or a GitLab connector).

2. **The Coral Engine (`src/coral/`)**
   - **Current Feature:** Uses DuckDB to mount flat `.jsonl` files into a virtual, in-memory SQL database for instantaneous cross-platform joins without a heavy data warehouse.
   - **How to Contribute:** You can write more complex analytical queries in `src/queries/` to discover new behavioral anomalies (e.g., correlating meeting times with late-night commit frequency).

3. **Gemini AI Interventions (`src/actions/`)**
   - **Current Feature:** Uses Google's `gemini-2.5-flash` LLM to draft highly contextual, empathetic emails for managers based on the mathematical risk scores.
   - **How to Contribute:** You can refine our system prompts, implement multi-shot prompting, or add support for localized languages in the manager email drafts.

4. **The Zero-Latency Dashboard (`webapp/`)**
   - **Current Feature:** A FastAPI server serving a Glassmorphism Jinja2 template using a "Pre-computed Agent State" for 0.0ms load times.
   - **How to Contribute:** Add new UI charts, improve the CSS animations, or create new views for the manager dashboard.

## 🛠️ Local Development Setup

We highly recommend using a virtual environment to prevent dependency conflicts.
1. Make sure you have Python 3.11+ installed.
2. Run `python3.11 -m venv venv` and activate it.
3. Install dependencies: `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and configure your API keys (or leave `USE_MOCK_DATA="true"` to bypass the need for API keys).

## 🧑‍💻 Code Style & Linting

We enforce clean, readable code. Please adhere to the following standards before submitting a PR:
- **Black**: We use `black` for formatting. Run `black .` before committing.
- **Type Hints**: All new Python functions must use explicit type hints (e.g., `def calculate_burnout(score: float) -> str:`).
- **Docstrings**: Provide clear Google-style docstrings for any new analytical functions.

## 🤝 The Pull Request Process

1. **Fork & Branch:** Create a branch with a descriptive name (e.g., `feat/jira-connector` or `fix/duckdb-memory-leak`).
2. **Implement:** Write your code, ensuring it doesn't break the pre-computed state architecture.
3. **Test:** Run the FastAPI server locally. Verify that the dashboard still loads instantly.
4. **Submit:** Open a Pull Request on GitHub. Fill out our custom Pull Request Template checklist.

Once you open a PR, one of our maintainers will review your code. Thank you for making the engineering world a healthier place!
