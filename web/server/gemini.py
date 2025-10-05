import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# Initialize the model - using the latest flash model
model = genai.GenerativeModel('gemini-2.5-flash')

def generate_response(prompt):
    """
    Generate a response from Gemini based on the given prompt.
    
    Args:
        prompt (str): The input prompt for Gemini
    
    Returns:
        dict: Response containing generated text or error
    """
    if not prompt:
        return {"error": "Prompt is required"}

    try:
        response = model.generate_content(prompt)
        return {"generated_text": response.text}
    except Exception as e:
        return {"error": str(e)}