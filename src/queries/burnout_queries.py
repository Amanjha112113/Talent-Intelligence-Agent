"""
BurnoutQueries — SRP: this module only contains SQL query definitions.
All queries use Coral's cross-source JOIN capability via DuckDB.
Table names follow the pattern: {source_name}_{table_name}
"""


class BurnoutQueries:
    """
    All Coral SQL queries for burnout detection.
    Each query demonstrates a different cross-source JOIN pattern.
    """

    # ── Master Query: The Coral Magic Moment ─────────────────────────────────
    # Joins 3 sources in a single SQL query — impossible without Coral.

    MASTER_BURNOUT_QUERY = """
    SELECT
        e.name                                          AS engineer_name,
        e.email                                         AS email,
        e.github_handle                                 AS github_handle,
        e.slack_id                                      AS slack_id,
        e.team                                          AS team,
        e.manager_email                                 AS manager_email,

        -- ── Overwork Signals (GitHub) ────────────────────────────────────────
        COALESCE(commits.late_commits, 0)               AS late_night_commits,
        COALESCE(commits.total_commits, 0)              AS total_commits,

        -- ── Engagement Signals (Slack) ──────────────────────────────────────
        COALESCE(slack.total_messages, 0)               AS slack_messages_30d,
        COALESCE(slack.complaints, 0)                   AS slack_complaints,
        COALESCE(slack.avg_response_mins, 0.0)          AS avg_slack_response_mins,

        -- ── Meeting Overload Signals (Calendar) ────────────────────────────
        COALESCE(calendar.total_meeting_hours, 0.0)     AS weekly_meeting_hours,
        COALESCE(calendar.declined_meetings, 0)         AS declined_meetings,



        -- ── Burnout Risk Score (0-100) ──────────────────────────────────────
        LEAST(100.0, ROUND(
            (COALESCE(commits.late_commits, 0)          * 3.5) +
            (COALESCE(calendar.total_meeting_hours, 0)  * 1.8) +
            (COALESCE(slack.complaints, 0)              * 2.5) -
            (COALESCE(slack.total_messages, 0)          * 0.3)
        , 1)) AS burnout_risk_score

    FROM github_engineers e

    -- GitHub: late-night commits per engineer
    LEFT JOIN (
        SELECT
            author,
            COUNT(*) FILTER (WHERE hour >= 21 OR hour < 9)   AS late_commits,
            COUNT(*)                                          AS total_commits
        FROM github_commits
        GROUP BY author
    ) commits ON commits.author = e.github_handle

    -- Slack: message count, complaints, avg response time
    LEFT JOIN (
        SELECT
            slack_id,
            COUNT(*)                                         AS total_messages,
            COUNT(*) FILTER (WHERE is_complaint = true)      AS complaints,
            AVG(response_latency_minutes)                    AS avg_response_mins
        FROM slack_messages
        GROUP BY slack_id
    ) slack ON slack.slack_id = e.slack_id

    -- Calendar: weekly meeting hours and declined meetings
    LEFT JOIN (
        SELECT
            attendee_email,
            SUM(duration_hours)                              AS total_meeting_hours,
            COUNT(*) FILTER (WHERE is_declined = true)       AS declined_meetings
        FROM calendar_events
        GROUP BY attendee_email
    ) calendar ON calendar.attendee_email = e.email



    ORDER BY burnout_risk_score DESC
    """

    # ── Individual Signal Queries ─────────────────────────────────────────────

    LATE_NIGHT_COMMITS = """
    SELECT
        author,
        COUNT(*) AS late_commits,
        MIN(committed_at) AS earliest,
        MAX(committed_at) AS latest
    FROM github_commits
    WHERE hour >= 21 OR hour < 9
    GROUP BY author
    ORDER BY late_commits DESC
    """

    SLACK_ENGAGEMENT_DECAY = """
    SELECT
        slack_id,
        COUNT(*) AS total_messages,
        AVG(response_latency_minutes) AS avg_response_mins,
        COUNT(*) FILTER (WHERE is_complaint = true) AS complaint_count,
        COUNT(*) FILTER (WHERE sentiment = 'negative') AS negative_messages
    FROM slack_messages
    GROUP BY slack_id
    ORDER BY avg_response_mins DESC
    """

    MEETING_OVERLOAD = """
    SELECT
        attendee_email,
        SUM(duration_hours) AS total_meeting_hours,
        COUNT(*) AS total_meetings,
        COUNT(*) FILTER (WHERE is_declined = true) AS declined_count,
        COUNT(*) FILTER (WHERE is_recurring = true) AS recurring_count
    FROM calendar_events
    GROUP BY attendee_email
    ORDER BY total_meeting_hours DESC
    """

    TEAM_SUMMARY = """
    SELECT
        team,
        COUNT(*) AS engineer_count,
        AVG(burnout_risk_score) AS avg_risk_score,
        MAX(burnout_risk_score) AS max_risk_score,
        COUNT(*) FILTER (WHERE burnout_risk_score >= 70) AS high_risk_count
    FROM (
        {master_query}
    ) AS scores
    GROUP BY team
    ORDER BY avg_risk_score DESC
    """.format(master_query=MASTER_BURNOUT_QUERY.strip().rstrip(";"))
