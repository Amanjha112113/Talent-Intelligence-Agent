"""
InterventionDrafter — SRP: only drafts intervention messages. No analysis. No reporting.
Implements IActionExecutor (DIP + ISP).
"""

from typing import Any
from src.core.interfaces.executor import IActionExecutor, ActionResult
from src.analysis.risk_scorer import RiskProfile, RiskLevel
from src.actions.gemini_service import GeminiService

class InterventionDrafter(IActionExecutor):
    """
    Drafts manager alerts and intervention messages for at-risk engineers.
    SRP: only drafts text. Does not send, does not analyze.
    """
    
    def __init__(self):
        self.gemini = GeminiService()

    def can_execute(self, action_type: str) -> bool:
        return action_type in ("draft_manager_alert", "draft_slack_message", "draft_hr_brief")

    def execute(self, action: dict[str, Any]) -> ActionResult:
        action_type = action.get("type")
        profile: RiskProfile = action.get("profile")

        if action_type == "draft_manager_alert":
            return self._draft_manager_alert(profile)
        if action_type == "draft_slack_message":
            return self._draft_slack_dm(profile)
        if action_type == "draft_hr_brief":
            return self._draft_hr_brief(profile)

        return ActionResult(
            action_type=action_type,
            target="unknown",
            success=False,
            message=f"Unknown action type: {action_type}",
        )

    # ── Drafters ──────────────────────────────────────────────────────────────

    def _draft_manager_alert(self, profile: RiskProfile) -> ActionResult:
        urgency = "⚠️ HIGH PRIORITY" if profile.risk_level == RiskLevel.HIGH else "📋 NOTICE"
        fallback_draft = f"""
Hi,

{urgency} — Burnout Risk Alert for {profile.engineer_name}

Our Talent Intelligence Agent has detected elevated burnout signals for {profile.engineer_name} (Risk Score: {profile.burnout_risk_score}/100).

Key signals identified:
• Late-night commits: {profile.raw_data.get('late_night_commits', 0)} in the last 30 days
• On-call incidents: {profile.raw_data.get('oncall_incidents', 0)} ({profile.raw_data.get('weekend_oncall', 0)} on weekends)
• Weekly meeting load: {profile.raw_data.get('weekly_meeting_hours', 0):.1f} hours
• Dominant burnout driver: {profile.dominant_signal}

Recommended actions:
1. Schedule a 1:1 focused on workload, not project status
2. Block 2 deep-work time slots in their calendar this week

This alert was generated automatically. Data is 100% local and confidential.

— Talent Intelligence Agent
""".strip()

        # Try to use Gemini to draft a better message
        prompt = f"""
        Write a polite, professional, and empathetic email alert to an engineering manager ({profile.manager_email}) 
        about one of their engineers, {profile.engineer_name}, who is showing elevated burnout risks.
        
        Context:
        - Risk Level: {profile.risk_level.value}
        - Risk Score: {profile.burnout_risk_score}/100
        - Dominant Issue: {profile.dominant_signal}
        - Late Night Commits: {profile.raw_data.get('late_night_commits', 0)}
        - Meeting load: {profile.raw_data.get('weekly_meeting_hours', 0)} hours/week
        
        The tone should be supportive and collaborative, not accusatory. Suggest concrete next steps like checking in on workload.
        """
        gemini_draft = self.gemini.generate_draft(prompt)
        final_draft = gemini_draft if gemini_draft else fallback_draft

        return ActionResult(
            action_type="draft_manager_alert",
            target=profile.manager_email,
            success=True,
            message=f"Draft ready for {profile.manager_email}",
            artifact=final_draft,
        )

    def _draft_slack_dm(self, profile: RiskProfile) -> ActionResult:
        fallback_draft = f"""
Hi {profile.engineer_name.split()[0]},

I noticed you've been putting in some long hours recently and dealing with {profile.dominant_signal}. 
I just wanted to check in and see how you're doing. Let's chat later today or tomorrow about your workload — I want to make sure you're not burning out.

— Your Manager
""".strip()

        prompt = f"""
        Draft a short, empathetic, and casual Slack direct message to an engineer, {profile.engineer_name}, 
        who has a {profile.risk_level.value} burnout risk score of {profile.burnout_risk_score}/100.
        The main issue is {profile.dominant_signal}.
        The message should be from their manager checking in on their wellbeing and workload. Do not mention the 'risk score' or 'algorithm' to the engineer. 
        Keep it very concise, casual, and supportive.
        """
        gemini_draft = self.gemini.generate_draft(prompt)
        final_draft = gemini_draft if gemini_draft else fallback_draft

        return ActionResult(
            action_type="draft_slack_message",
            target=f"@{profile.engineer_name.split()[0].lower()}",
            success=True,
            message="Slack DM draft ready",
            artifact=final_draft,
        )

    def _draft_hr_brief(self, profile: RiskProfile) -> ActionResult:
        fallback_brief = f"""
HR BRIEF — CONFIDENTIAL

Engineer: {profile.engineer_name}
Team: {profile.team}
Risk Level: {profile.risk_level} ({profile.burnout_risk_score}/100)

Signal Summary:
- Overwork: {profile.raw_data.get('late_night_commits', 0)} late commits
- Meetings: {profile.raw_data.get('weekly_meeting_hours', 0):.1f}h/week
- Disengagement: {profile.raw_data.get('slack_complaints', 0)} complaint messages in Slack

Recommended HR Action:
- Confidential wellbeing check-in within 48 hours
- Review team workload balance for {profile.team} team
- Flag for manager coaching on workload distribution
""".strip()

        prompt = f"""
        Write an internal HR brief regarding engineer {profile.engineer_name} on the {profile.team} team.
        They have a {profile.risk_level.value} burnout risk ({profile.burnout_risk_score}/100) mainly driven by {profile.dominant_signal}.
        Summarize the situation clinically but empathetically and list 3 recommended HR actions to mitigate this risk.
        Keep it professional, structured, and strictly confidential.
        """
        gemini_draft = self.gemini.generate_draft(prompt)
        final_brief = gemini_draft if gemini_draft else fallback_brief

        return ActionResult(
            action_type="draft_hr_brief",
            target="HR Team",
            success=True,
            message="HR brief ready",
            artifact=final_brief,
        )
