"""
PerformanceQueries — SRP: this module only contains SQL query definitions for performance grading.
"""

class PerformanceQueries:
    """
    All Coral SQL queries for performance and layoff intelligence.
    """

    PERFORMANCE_GRADE_QUERY = """
    SELECT
        e.name                                          AS engineer_name,
        e.email                                         AS email,
        e.team                                          AS team,
        e.manager_email                                 AS manager_email,
        
        -- Code Sector (40% weight)
        COALESCE(commits.total_commits, 0)              AS total_commits,
        COALESCE(commits.late_commits, 0)               AS late_commits,
        LEAST(100.0, ROUND(COALESCE(commits.total_commits, 0) * 1.5 + COALESCE(commits.late_commits, 0) * 0.5, 1)) AS code_score,

        -- Collaboration Sector (25% weight)
        COALESCE(slack.total_messages, 0)               AS total_messages,
        COALESCE(slack.complaints, 0)                   AS complaints,
        GREATEST(0.0, LEAST(100.0, ROUND(COALESCE(slack.total_messages, 0) * 2.0 - COALESCE(slack.complaints, 0) * 5.0, 1))) AS collab_score,

        -- Reliability Sector (20% weight)
        100.0 AS reliability_score,

        -- Availability Sector (15% weight)
        COALESCE(calendar.total_meetings, 0)            AS total_meetings,
        COALESCE(calendar.declined_meetings, 0)         AS declined_meetings,
        CASE 
            WHEN calendar.total_meetings IS NULL THEN 50.0
            WHEN COALESCE(calendar.total_meetings, 0) = 0 THEN 100.0 
            ELSE LEAST(100.0, ROUND(CAST((COALESCE(calendar.total_meetings, 0) - COALESCE(calendar.declined_meetings, 0)) AS FLOAT) / COALESCE(calendar.total_meetings, 0) * 100.0, 1))
        END AS availability_score

    FROM github_engineers e

    LEFT JOIN (
        SELECT
            author,
            COUNT(*) AS total_commits,
            COUNT(*) FILTER (WHERE hour >= 21 OR hour < 9) AS late_commits
        FROM github_commits
        GROUP BY author
    ) commits ON commits.author = e.github_handle

    LEFT JOIN (
        SELECT
            slack_id,
            COUNT(*) AS total_messages,
            COUNT(*) FILTER (WHERE is_complaint = true) AS complaints
        FROM slack_messages
        GROUP BY slack_id
    ) slack ON slack.slack_id = e.slack_id

    LEFT JOIN (
        SELECT
            attendee_email,
            COUNT(*) AS total_meetings,
            COUNT(*) FILTER (WHERE is_declined = true) AS declined_meetings
        FROM calendar_events
        GROUP BY attendee_email
    ) calendar ON calendar.attendee_email = e.email


    """
