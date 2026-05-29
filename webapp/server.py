import os
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio
import uuid

# Add project root to path so we can import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import build_agent
from src.actions.gemini_service import GeminiService
from src.queries.burnout_queries import BurnoutQueries

app = FastAPI(title="Talent Intelligence Agent")

# Mount static files and templates
os.makedirs("webapp/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")
templates = Jinja2Templates(directory="webapp/templates")

# Global state
base_agent_state = None
chat_sessions = {}
gemini_service = GeminiService()

@app.on_event("startup")
async def startup_event():
    global base_agent_state
    print("Pre-computing agent state for hackathon deployment...")
    agent = build_agent()
    base_agent_state = agent.run()
    print("Agent state pre-computed successfully!")

def get_session_id(request: Request, response: Response = None):
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        if response:
            response.set_cookie(key="session_id", value=session_id)
    return session_id

def get_chat_session(session_id: str):
    if session_id not in chat_sessions:
        history = []
        gemini_chat = None
        if gemini_service.is_configured and base_agent_state:
            summary = base_agent_state.analysis.get("summary", {})
            grades_info = [f"{g.engineer_name}: {g.grade} (Score: {g.overall_score:.1f})" for g in getattr(base_agent_state, 'performance_grades', [])]
            layoff_info = [f"{k}: {'Silent Hero' if v.is_silent_hero else 'Overrated' if v.is_overrated else 'Normal'}" for k, v in getattr(base_agent_state, 'layoff_risks', {}).items()]
            context = f"Team Summary: {summary}\nPerformance Grades: {grades_info}\nLayoff Risks: {layoff_info}\n\nFull Report: {base_agent_state.report}"
            gemini_chat = gemini_service.start_chat(context)
            
        chat_sessions[session_id] = {"history": history, "chat": gemini_chat}
    return chat_sessions[session_id]

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, response: Response):
    session_id = get_session_id(request, response)
    return templates.TemplateResponse(request=request, name="base.html", context={"request": request, "state": base_agent_state})

@app.get("/tabs/overview", response_class=HTMLResponse)
async def tab_overview(request: Request):
    return templates.TemplateResponse(request=request, name="tabs/overview.html", context={"request": request, "state": base_agent_state})

@app.get("/tabs/performance", response_class=HTMLResponse)
async def tab_performance(request: Request):
    return templates.TemplateResponse(request=request, name="tabs/performance.html", context={"request": request, "state": base_agent_state})

def generate_pie_chart(summary):
    risk_counts = {
        "High": summary.get("high_risk_count", 0),
        "Medium": summary.get("medium_risk_count", 0),
        "Low": summary.get("low_risk_count", 0),
    }
    fig = go.Figure(go.Pie(
        labels=list(risk_counts.keys()),
        values=list(risk_counts.values()),
        hole=0.6,
        marker_colors=["#ef4444", "#f97316", "#10b981"],
        textinfo='label+percent',
    ))
    fig.update_layout(
        height=300, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor='rgba(0,0,0,0)', font_color='#cbd5e1', showlegend=False,
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)

def generate_bar_chart(profiles):
    df_data = [{"Engineer": p.engineer_name, "Team": p.team, "Score": p.burnout_risk_score, "Level": p.risk_level.value} for p in profiles]
    if not df_data: return ""
    df = pd.DataFrame(df_data)
    fig = px.bar(
        df, x="Score", y="Engineer", orientation="h", color="Level",
        color_discrete_map={"HIGH": "#ef4444", "MEDIUM": "#f97316", "LOW": "#10b981"},
    )
    fig.update_layout(
        height=350, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font_color='#cbd5e1', showlegend=False,
        xaxis=dict(showgrid=True, gridcolor='#334155', range=[0, 100]), yaxis=dict(showgrid=False),
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)

def generate_breakdown_chart(profile):
    signals = {k: v for k, v in profile.signal_breakdown.items() if v > 0}
    if not signals: return ""
    fig = go.Figure(go.Bar(
        x=list(signals.values()), y=list(signals.keys()), orientation='h',
        marker_color=['#ef4444' if v > 15 else '#f97316' if v > 5 else '#3b82f6' for v in signals.values()],
    ))
    fig.update_layout(
        height=200, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font_color='#cbd5e1', xaxis=dict(showgrid=False), yaxis=dict(showgrid=False),
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)

@app.get("/tabs/burnout", response_class=HTMLResponse)
async def tab_burnout(request: Request):
    profiles = base_agent_state.analysis.get("profiles", [])
    summary = base_agent_state.analysis.get("summary", {})
    
    # Calculate team summary
    teams_dict = {}
    for p in profiles:
        t = p.team
        if t not in teams_dict: teams_dict[t] = {"name": t, "count": 0, "total_score": 0, "high_risk": 0}
        teams_dict[t]["count"] += 1
        teams_dict[t]["total_score"] += p.burnout_risk_score
        if p.risk_level.value == "HIGH": teams_dict[t]["high_risk"] += 1
    
    teams = sorted(teams_dict.values(), key=lambda x: -x["total_score"])
    
    # Generate charts
    pie_chart = generate_pie_chart(summary)
    bar_chart = generate_bar_chart(profiles)
    breakdown_charts = {p.engineer_name: generate_breakdown_chart(p) for p in profiles}

    return templates.TemplateResponse(request=request, name="tabs/burnout.html", context={
        "request": request, "state": base_agent_state, "teams": teams,
        "pie_chart": pie_chart, "bar_chart": bar_chart, "breakdown_charts": breakdown_charts
    })

@app.get("/tabs/chat", response_class=HTMLResponse)
async def tab_chat(request: Request):
    session_id = get_session_id(request)
    session_data = get_chat_session(session_id)
    return templates.TemplateResponse(request=request, name="tabs/chat.html", context={"request": request, "state": base_agent_state, "chat_history": session_data["history"]})

@app.post("/api/chat", response_class=HTMLResponse)
async def api_chat(request: Request, prompt: str = Form(...)):
    session_id = get_session_id(request)
    session_data = get_chat_session(session_id)
    chat_history = session_data["history"]
    gemini_chat = session_data["chat"]
    
    chat_history.append({"role": "user", "content": prompt})
    
    html = f"""
    <div class="mb-4 flex justify-end">
        <div class="max-w-[75%] p-3 rounded-lg bg-blue-600 text-white rounded-br-none">
            {prompt}
        </div>
    </div>
    """
    
    if not gemini_service.is_configured or not gemini_chat:
        resp = "Gemini API is not configured. Please add GEMINI_API_KEY to your environment."
        chat_history.append({"role": "assistant", "content": resp})
        html += f"""
        <div class="mb-4 flex justify-start">
            <div class="max-w-[75%] p-3 rounded-lg bg-gray-800 text-gray-200 rounded-bl-none border border-gray-700">
                {resp}
            </div>
        </div>
        """
        return HTMLResponse(content=html)
    
    try:
        response = gemini_chat.send_message(prompt)
        content = response.text
        chat_history.append({"role": "assistant", "content": content})
        html += f"""
        <div class="mb-4 flex justify-start">
            <div class="max-w-[75%] p-3 rounded-lg bg-gray-800 text-gray-200 rounded-bl-none border border-gray-700">
                {content.replace(chr(10), '<br>')}
            </div>
        </div>
        """
    except Exception as e:
        html += f"""<div class="mb-4 flex justify-start"><div class="text-red-500">Error communicating with Gemini: {e}</div></div>"""
        
    return HTMLResponse(content=html)

@app.post("/api/draft_alert", response_class=HTMLResponse)
async def api_draft_alert(request: Request, type: str = Form(...), target: str = Form(...)):
    draft = None
    action_type = "draft_manager_alert" if type == "manager" else "draft_slack_message"
    
    for action in base_agent_state.executed_actions:
        if action.action_type == action_type and (target in action.target or type == "slack"):
            draft = action.artifact
            break
            
    if not draft:
        draft = "Draft not generated or action not found for this target."
        
    html = f"""
    <div class="mt-2 p-3 bg-gray-900 border border-gray-700 rounded text-sm text-gray-300 font-mono whitespace-pre-wrap">{draft}</div>
    """
    return HTMLResponse(content=html)

@app.get("/tabs/system", response_class=HTMLResponse)
async def tab_system(request: Request):
    return templates.TemplateResponse(request=request, name="tabs/system.html", context={"request": request, "state": base_agent_state, "sql_query": BurnoutQueries.MASTER_BURNOUT_QUERY})

@app.post("/api/refresh", response_class=HTMLResponse)
async def api_refresh(request: Request):
    global base_agent_state
    print("User clicked Refresh: Re-running agent pipeline to pull live data...")
    agent = build_agent()
    base_agent_state = agent.run()
    print("Agent state refreshed successfully!")
    return templates.TemplateResponse(request=request, name="sidebar.html", context={"request": request, "state": base_agent_state})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("webapp.server:app", host="0.0.0.0", port=port, reload=True)
