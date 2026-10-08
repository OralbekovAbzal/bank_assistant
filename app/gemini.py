import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(timeout=30000)
)

def ask_gemini(message: str, prev_id: str) -> tuple:
    interaction = client.interactions.create(
        model="gemini-2.5-flash",
        input=message,
        previous_interaction_id=prev_id,
    )
    return (interaction.id, interaction.output_text)
