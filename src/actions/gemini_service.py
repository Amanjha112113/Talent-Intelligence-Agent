from google import genai
from google.genai import types
from typing import Optional
from src.core.config import get_settings

class GeminiService:
    """
    A service wrapper for the Gemini API.
    Handles configuration and provides methods for generating text.
    """
    def __init__(self):
        cfg = get_settings()
        self.api_key = cfg.gemini_api_key
        self.is_configured = bool(self.api_key)
        if self.is_configured:
            self.client = genai.Client(api_key=self.api_key)
            self.model_name = 'gemini-2.5-flash'

    def generate_draft(self, prompt: str) -> Optional[str]:
        """
        Generate a text draft using Gemini. Returns None if API key is not configured or an error occurs.
        """
        if not self.is_configured:
            return None
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return None

    def start_chat(self, context: str):
        """
        Start a chat session with the given context.
        """
        if not self.is_configured:
            return None
        
        try:
            system_instruction = f"System Context:\n{context}\n\nYou are an intelligent HR Assistant for the Engineering Talent Intelligence dashboard. You help HR professionals understand engineer burnout risks, metrics, and you can draft empathetic messages to managers or engineers. Keep your responses professional, concise, and helpful. IMPORTANT: When generating a draft message/email, ALWAYS start the draft with 'Subject: ' so the UI can detect it and attach a Send button."
            
            chat = self.client.chats.create(
                model=self.model_name,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction
                )
            )
            return chat
        except Exception as e:
            print(f"Gemini API Error starting chat: {e}")
            return None
