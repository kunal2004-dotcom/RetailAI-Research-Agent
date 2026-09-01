import logging
import time
import re
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.app.ai.state import ResearchState
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class PlannerOutput(BaseModel):
    queries: list[str] = Field(description="List of search queries")

def plan_research(state: ResearchState) -> ResearchState:
    logger.info(f"Session {state['session_id']}: Running Planner")
    state['current_step'] = 'planner'
    
    if settings.gemini_api_key in ('your_gemini_api_key_here', 'dummy'):
        logger.info("No Gemini API key found, using fallback planner logic.")
        state['search_queries'] = [state['research_question']]
        return state
        
    llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=settings.gemini_api_key, max_retries=0)
    logger.info(f"LLM provider: {llm.__class__.__name__}")
    structured_llm = llm.with_structured_output(PlannerOutput)
    
    prompt = f"Generate 3 focused search queries to research this question: {state['research_question']}"
    
    for attempt in range(5):
        try:
            result = structured_llm.invoke(prompt)
            state['search_queries'] = result.queries
            logger.info(f"Session {state['session_id']}: Generated queries: {result.queries}")
            break
        except Exception as e:
            if '429' in str(e) or 'RESOURCE_EXHAUSTED' in str(e):
                if 'GenerateRequestsPerDay' in str(e) or 'quota exceeded' in str(e).lower():
                    state['errors'].append('Google Gemini API Error: You have exceeded your Free Tier daily quota limit. Please generate a new API key from a different Google account or enable billing in Google AI Studio.')
                    break
                match = re.search(r'retry in ([\d\.]+)s', str(e))
                sleep_time = float(match.group(1)) + 1.0 if match else 20.0
                if attempt < 4:
                    logger.warning(f'Rate limit hit, sleeping for {sleep_time}s... (Attempt {attempt+1})')
                    time.sleep(sleep_time)
                else:
                    state['errors'].append(f'Google Gemini API Error: Free Tier rate limit exceeded after multiple retries. Please wait 1 minute and try again.')
                    break
            else:
                state['errors'].append(f'Planner error: {str(e)}')
                break
                
    return state
