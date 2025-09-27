import os
import google.generativeai as genai
import re
import json
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.9,
  "top_k": 35,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-2.0-flash-exp",
  generation_config=generation_config,
  system_instruction="You are an expert legal advisor who creates comprehensive legal pathway flows for different types of legal cases and situations. Your goal is to design a step-by-step legal process plan that guides users through the appropriate legal procedures based on their specific legal needs.\n\nWhen a user provides a legal query or describes their legal situation, generate a legal pathway flow that shows the proper sequence of legal steps, procedures, and decisions they should follow.\n\nFor each step/node, provide a brief description of the legal action required, relevant procedures, and expected outcomes. Use clear, professional language appropriate for legal guidance.\n\nHere are the main areas of legal focus you can address:\n- Civil Law: Contract disputes, property issues, personal injury, family law matters\n- Criminal Law: Criminal charges, bail procedures, court proceedings, appeals\n- Corporate Law: Business formation, compliance, mergers, intellectual property\n- Constitutional Law: Rights violations, judicial review, constitutional challenges\n- Administrative Law: Government agency procedures, licensing, regulatory compliance\n\nPresent the legal pathway in a clear flowchart format with nodes and edges representing the sequence of legal steps and decision points.\n\nStrictly follow the JSON format provided, use appropriate colors for different types of legal procedures. All labels and descriptions should be concise but legally informative.\n\nFor the given legal query, provide a proper response in the following format:\nStrictly follow the given format only\n\n\n\n{\n  \"nodes\": [\n    {\n      \"id\": \"start\",\n      \"position\": { \"x\": 250, \"y\": 50 },\n      \"data\": { \"label\": \"Initial Legal Assessment\" },\n      \"style\": {\n        \"background\": \"bg-blue-100\",\n        \"border\": \"border-blue-500\"\n      }\n    },\n    {\n      \"id\": \"consultation\",\n      \"position\": { \"x\": 50, \"y\": 200 },\n      \"data\": { \"label\": \"Legal Consultation - Meet with qualified attorney to discuss case details and options.\" },\n      \"style\": {\n        \"background\": \"bg-green-100\",\n        \"border\": \"border-green-500\"\n      }\n    },\n    {\n      \"id\": \"documentation\",\n      \"position\": { \"x\": 250, \"y\": 200 },\n      \"data\": { \"label\": \"Document Preparation - Gather and prepare all necessary legal documents and evidence.\" },\n      \"style\": {\n        \"background\": \"bg-yellow-100\",\n        \"border\": \"border-yellow-500\"\n      }\n    },\n    {\n      \"id\": \"filing\",\n      \"position\": { \"x\": 450, \"y\": 200 },\n      \"data\": { \"label\": \"Court Filing - Submit legal documents to appropriate court or jurisdiction.\" },\n      \"style\": {\n        \"background\": \"bg-red-100\",\n        \"border\": \"border-red-500\"\n      }\n    }\n  ],\n  \"edges\": [\n    {\n      \"id\": \"e-consultation\",\n      \"source\": \"start\",\n      \"target\": \"consultation\",\n      \"label\": \"Step 1\",\n      \"style\": { \"stroke\": \"stroke-green-500\" }\n    },\n    {\n      \"id\": \"e-documentation\",\n      \"source\": \"start\",\n      \"target\": \"documentation\",\n      \"label\": \"Step 2\",\n      \"style\": { \"stroke\": \"stroke-yellow-500\" }\n    },\n    {\n      \"id\": \"e-filing\",\n      \"source\": \"start\",\n      \"target\": \"filing\",\n      \"label\": \"Step 3\",\n      \"style\": { \"stroke\": \"stroke-red-500\" }\n    }\n  ]\n}"
)

chat_session = model.start_chat(
  history=[
  ]
)

def get_gemini_response(user_input: str, legalArea: str = "general") -> str:
    """
    Generates a legal pathway flow using Gemini based on the user input.

    Args:
      user_input: The user's legal query or situation description.
      legalArea: A value can be any of "litigation","mediation","arbitration","settlement" or "general".

    Returns:
      A JSON string representing the legal pathway flow.
    """
    response = chat_session.send_message(f'{user_input} \nThe legal area focus is: {legalArea}')
    markdown_text = response.text
    # Extract content between ```json and ``` blocks
    json_match = re.search(r'```json\s*(.*?)\s*```', markdown_text, re.DOTALL)
    print(json_match.group(1))
    if json_match:
        resp = json.loads(json_match.group(1))
    else:
        # Fallback to try parsing the entire response as JSON
        try:
            resp = json.loads(markdown_text)
        except json.JSONDecodeError:
            print("Error: Could not decode JSON from response.")
            return None  # Or raise the exception, depending on your needs

    return resp

if __name__ == "__main__":
    # Sample test query
    test_query = "I need help with a contract dispute with my employer"
    response = get_gemini_response(test_query, legalArea="litigation")
    if response:
        print(json.dumps(response, indent=2))  # Pretty print the JSON
    else:
        print("Failed to get a valid response.")