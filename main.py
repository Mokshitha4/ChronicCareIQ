#main.py
from fastapi import FastAPI
from pydantic import BaseModel
from agents import survey_agent, PlanGenerationAgent, ChatAdjustmentAgent, SynthesisAgent
from typing import Dict, List
from fastapi.middleware.cors import CORSMiddleware

app=FastAPI()
# Enable CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

plan_agent=PlanGenerationAgent(); chat_agent=ChatAdjustmentAgent(); synth_agent=SynthesisAgent()

class SurveyRequest(BaseModel): condition:str; dietaryPrefs:str; exercisePrefs:str; busyDays:str
class ChatRequest(BaseModel): profile:Dict; plan:List[Dict]; message:str

@app.post('/api/plan')
def gen(req:SurveyRequest): return {'plan': plan_agent.run(survey_agent(req.dict()))}

@app.post('/api/chat')
def chat(req:ChatRequest): updated=chat_agent.run(req.plan, req.message); return {'updatedPlan':updated,'reply':synth_agent.run(updated)}