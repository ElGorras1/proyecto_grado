import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def test_model_burst(model_name):
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    print(f"Testing BURST {model_name}...")
    for i in range(25): # Try more than 20 requests
        try:
            response = client.models.generate_content(
                model=model_name,
                contents="Say hello briefly."
            )
            print(f"Req {i}: Success")
        except Exception as e:
            print(f"Req {i} Failed: {e}")
            break

if __name__ == "__main__":
    test_model_burst("gemini-3.5-flash-lite")
