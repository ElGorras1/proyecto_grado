import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def list_available_models():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY found.")
        return
        
    client = genai.Client(api_key=api_key)
    
    print("--- Modelos Disponibles ---")
    try:
        models = client.models.list(config={"page_size": 50})
        for m in models:
            # We want models that support generateContent (or just print names)
            print(f"Name: {m.name} | Display: {m.display_name}")
    except Exception as e:
        print(f"Error fetching models: {e}")

if __name__ == "__main__":
    list_available_models()
