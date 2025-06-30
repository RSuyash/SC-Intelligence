import google.generativeai as genai

class GeminiClient:
    """A client to interact with the Google Gemini API."""
    def __init__(self, api_key):
        if not api_key or 'YOUR_API_KEY' in api_key:
            raise ValueError("Gemini API key is not configured in config.ini")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def generate_text(self, prompt):
        """Generates text from a given prompt."""
        print("\nSending prompt to Gemini...")
        try:
            response = self.model.generate_content(prompt, generation_config={'response_mime_type': 'application/json'})
            # Handle cases where the response might be blocked
            if not response.parts:
                 return f"Error: The response from Gemini was empty or blocked. Finish reason: {response.prompt_feedback.block_reason}"

            return response.text
        except Exception as e:
            return f"Error communicating with Gemini API: {e}"