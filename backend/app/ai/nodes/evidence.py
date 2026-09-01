import logging
import time
import re
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.app.ai.state import ResearchState
from backend.app.core.config import settings
import uuid

logger = logging.getLogger(__name__)

class EvidenceItemSchema(BaseModel):
    source_id: str = Field(description="The SOURCE_ID of the text chunk from which the claim was extracted")
    claim: str = Field(description="The extracted factual claim")
    evidence_type: str = Field(description="Type of evidence (statistic, quote, expert opinion, trend)")
    relevance_score: float = Field(description="Score from 0.0 to 1.0 representing relevance to the question")

class EvidenceList(BaseModel):
    items: list[EvidenceItemSchema] = Field(description="List of extracted evidence items")

def extract_evidence(state: ResearchState) -> ResearchState:
    logger.info(f"Session {state['session_id']}: Running Evidence Extraction")
    state['current_step'] = 'evidence'
    
    if settings.gemini_api_key in ('your_gemini_api_key_here', 'dummy'):
        state['evidence'] = []
        for i in range(2):
            state['evidence'].append({
                "temp_id": f"temp_ev_{i}",
                "source_temp_id": f"temp_src_{i}",
                "claim": f"Mock evidence claim {i}",
                "evidence_type": "statistic",
                "relevance_score": 0.9
            })
        return state
        
    llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=settings.gemini_api_key, max_retries=0)
    structured_llm = llm.with_structured_output(EvidenceList)
    
    evidence_items = []
    
    chunks = state.get('retrieved_chunks', [])
    if not chunks:
        state['errors'].append("Insufficient evidence: Could not extract useful facts (no chunks).")
        return state
        
    # Batch chunks into a single large prompt to save time and API requests
    combined_text = ""
    for chunk in chunks:
        source_id = chunk['metadata'].get('source_temp_id', 'unknown')
        combined_text += f"\n--- SOURCE_ID: {source_id} ---\n{chunk['content']}\n"
        
    prompt = f"Extract highly relevant factual evidence from the provided text chunks to answer the question: {state['research_question']}\nMake sure to explicitly include the exact SOURCE_ID for each extracted claim.\n\nText:\n{combined_text}"
    
    for attempt in range(5):
        try:
            logger.info(f"Session {state['session_id']}: Extracting evidence in a single batched LLM call...")
            result = structured_llm.invoke(prompt)
            for item in result.items:
                if item.relevance_score > 0.0:
                    evidence_items.append({
                        "temp_id": str(uuid.uuid4()),
                        "source_temp_id": item.source_id if item.source_id != 'unknown' else None,
                        "claim": item.claim,
                        "evidence_type": item.evidence_type,
                        "relevance_score": item.relevance_score
                    })
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
                logger.error(f'Evidence extraction error: {e}')
                break

    if not evidence_items:
        state['errors'].append("Insufficient evidence: Could not extract useful facts.")
        
    state['evidence'] = evidence_items
    return state
