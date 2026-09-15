import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def test_model(model_name):
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    print(f"Testing {model_name}...")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Say hello"
        )
        print(f"Success! Response: {response.text}")
    except Exception as e:
        print(f"Failed with {model_name}: {e}")

if __name__ == "__main__":
    test_model("gemini-2.5-flash")
    test_model("gemini-3.5-flash")
    test_model("gemini-3.7-flash")
