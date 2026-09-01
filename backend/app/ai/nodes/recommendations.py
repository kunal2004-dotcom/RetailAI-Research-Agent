import logging
import time
import re
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.app.ai.state import ResearchState
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class RecommendationSchema(BaseModel):
    recommendation: str = Field(description="Actionable recommendation")
    rationale: str = Field(description="Why this is recommended")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")

class RecommendationList(BaseModel):
    items: list[RecommendationSchema] = Field(description="List of recommendations")

def generate_recommendations(state: ResearchState) -> ResearchState:
    logger.info(f"Session {state['session_id']}: Running Recommendation Generation")
    state['current_step'] = 'recommendations'
    
    if not state.get('findings') and not settings.gemini_api_key in ('your_gemini_api_key_here', 'dummy'):
        return state
        
    if settings.gemini_api_key in ('your_gemini_api_key_here', 'dummy'):
        state['recommendations'] = [{
            "recommendation": "Mock actionable recommendation.",
            "rationale": "Based on mock findings.",
            "confidence": 0.95
        }]
        return state
        
    llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=settings.gemini_api_key, max_retries=0)
    structured_llm = llm.with_structured_output(RecommendationList)
    
    findings_text = "\n".join([f"Finding: {f['statement']}" for f in state['findings']])
    prompt = f"Based on the following findings, generate actionable recommendations for the research question: {state['research_question']}\n\nFindings:\n{findings_text}"
    
    for attempt in range(5):
        try:
            result = structured_llm.invoke(prompt)
            recs_data = []
            for item in result.items:
                recs_data.append({
                    "recommendation": item.recommendation,
                    "rationale": item.rationale,
                    "confidence": item.confidence
                })
            state['recommendations'] = recs_data
            break
        except Exception as e:
            if '429' in str(e) or 'RESOURCE_EXHAUSTED' in str(e) or '503' in str(e) or 'UNAVAILABLE' in str(e):
                if 'GenerateRequestsPerDay' in str(e) or 'quota exceeded' in str(e).lower():
                    state['errors'].append('Google Gemini API Error: You have exceeded your Free Tier daily quota limit. Please generate a new API key from a different Google account or enable billing in Google AI Studio.')
                    break
                match = re.search(r'retry in ([\d\.]+)s', str(e))
                sleep_time = float(match.group(1)) + 1.0 if match else 20.0
                if attempt < 4:
                    logger.warning(f'Rate limit hit, sleeping for {sleep_time}s... (Attempt {attempt+1})')
                    time.sleep(sleep_time)
                else:
                    state['errors'].append(f'Recommendations error: {e}')
                    break
            else:
                state['errors'].append(f'Recommendations error: {e}')
                break
                
    return state
