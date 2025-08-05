import json
import google.generativeai as genai
from typing import List, Dict

def build_claim_prompt(query: str, context_docs: List[Dict]) -> str:
    context_text = "\n---\n".join([doc["content"] for doc in context_docs])
    prompt = f"""
Insurance Claim Analysis Request

Claim Query: {query}

Supporting Documents:
{context_text}

Please provide an outcome:
- decision: APPROVED, REJECTED, or REVIEW
- amount (if applicable)
- justification
- confidence score

Reply only in valid JSON format.
"""
    return prompt

async def call_gemini_api(prompt: str) -> Dict:
    model = genai.GenerativeModel('gemini-2.5-pro')
    response = model.generate_content(prompt)
    text = response.text.strip()
    try:
        if text.startswith('{'):
            return json.loads(text)
    except Exception:
        pass
    return {"decision": "REVIEW", "justification": text, "confidence_score": 0.7}
