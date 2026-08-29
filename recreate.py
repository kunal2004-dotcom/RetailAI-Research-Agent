import os

planner = """import logging
import time
import re
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.app.ai.state import ResearchState
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class PlannerOutput(BaseModel):
    queries: list[str] = Field(description="List of search queries")

def planner_node(state: ResearchState) -> ResearchState:
    logger.info(f"Session {state['session_id']}: Running Planner")
    state['current_step'] = 'planner'
    
    if settings.gemini_api_key in ('your_gemini_api_key_here', 'dummy'):
        logger.info("No Gemini API key found, using fallback planner logic.")
        state['search_queries'] = [state['research_question']]
        return state
        
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", google_api_key=settings.gemini_api_key, max_retries=10)
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
                match = re.search(r'retry in ([\d\.]+)s', str(e))
                sleep_time = float(match.group(1)) + 1.0 if match else 20.0
                if attempt < 4:
                    logger.warning(f'Rate limit hit, sleeping for {sleep_time}s... (Attempt {attempt+1})')
                    time.sleep(sleep_time)
                else:
                    state['errors'].append(f'Planner error: {str(e)}')
                    break
            else:
                state['errors'].append(f'Planner error: {str(e)}')
                break
                
    return state
"""

evidence = """import logging
import time
import re
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.app.ai.state import ResearchState
from backend.app.core.config import settings
import uuid

logger = logging.getLogger(__name__)

class EvidenceItemSchema(BaseModel):
    claim: str = Field(description="The extracted factual claim")
    evidence_type: str = Field(description="Type of evidence (statistic, quote, expert opinion, trend)")
    relevance_score: float = Field(description="Score from 0.0 to 1.0 representing relevance to the question")

class EvidenceList(BaseModel):
    items: list[EvidenceItemSchema] = Field(description="List of extracted evidence items")

def evidence_node(state: ResearchState) -> ResearchState:
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
        
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", google_api_key=settings.gemini_api_key, max_retries=10)
    structured_llm = llm.with_structured_output(EvidenceList)
    
    evidence_items = []
    
    for chunk in state.get('retrieved_chunks', []):
        content = chunk['content']
        metadata = chunk['metadata']
        
        prompt = f"Extract highly relevant factual evidence from the following text to answer the question: {state['research_question']}\\n\\nText:\\n{content}"
        
        for attempt in range(5):
            try:
                result = structured_llm.invoke(prompt)
                for item in result.items:
                    if item.relevance_score > 0.6:
                        evidence_items.append({
                            "temp_id": str(uuid.uuid4()),
                            "source_temp_id": metadata.get('source_temp_id'),
                            "claim": item.claim,
                            "evidence_type": item.evidence_type,
                            "relevance_score": item.relevance_score
                        })
                break
            except Exception as e:
                if '429' in str(e) or 'RESOURCE_EXHAUSTED' in str(e):
                    match = re.search(r'retry in ([\d\.]+)s', str(e))
                    sleep_time = float(match.group(1)) + 1.0 if match else 20.0
                    if attempt < 4:
                        logger.warning(f'Rate limit hit, sleeping for {sleep_time}s... (Attempt {attempt+1})')
                        time.sleep(sleep_time)
                    else:
                        logger.error(f'Evidence extraction error: {e}')
                        break
                else:
                    logger.error(f'Evidence extraction error: {e}')
                    break

    if not evidence_items:
        state['errors'].append("Insufficient evidence: Could not extract useful facts.")
        
    state['evidence'] = evidence_items
    return state
"""

findings = """import logging
import time
import re
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.app.ai.state import ResearchState
from backend.app.core.config import settings
import uuid

logger = logging.getLogger(__name__)

class EvidenceLink(BaseModel):
    evidence_temp_id: str = Field(description="The temp_id of the evidence supporting this finding")
    relationship_type: str = Field(description="How the evidence supports the finding (supports, contextualizes)")

class FindingSchema(BaseModel):
    statement: str = Field(description="A synthesized finding")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")
    evidence_links: list[EvidenceLink] = Field(description="Links to supporting evidence")

class FindingsList(BaseModel):
    items: list[FindingSchema] = Field(description="List of synthesized findings")

def findings_node(state: ResearchState) -> ResearchState:
    logger.info(f"Session {state['session_id']}: Running Finding Generation")
    state['current_step'] = 'findings'
    
    if not state.get('evidence') and not settings.gemini_api_key in ('your_gemini_api_key_here', 'dummy'):
        return state
        
    if settings.gemini_api_key in ('your_gemini_api_key_here', 'dummy'):
        state['findings'] = [{
            "statement": "Mock synthesis finding based on collected evidence.",
            "confidence": 0.9,
            "evidence_links": [
                {"evidence_temp_id": "temp_ev_0", "relationship_type": "supports"}
            ]
        }]
        return state
        
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", google_api_key=settings.gemini_api_key, max_retries=10)
    structured_llm = llm.with_structured_output(FindingsList)
    
    evidence_text = "\\n".join([f"ID: {e['temp_id']} | Claim: {e['claim']}" for e in state['evidence']])
    prompt = f"Synthesize the following evidence into 3-5 key findings that answer the research question: {state['research_question']}\\n\\nEvidence:\\n{evidence_text}"
    
    for attempt in range(5):
        try:
            result = structured_llm.invoke(prompt)
            findings_data = []
            for item in result.items:
                findings_data.append({
                    "statement": item.statement,
                    "confidence": item.confidence,
                    "evidence_links": [el.model_dump() for el in item.evidence_links]
                })
            state['findings'] = findings_data
            break
        except Exception as e:
            if '429' in str(e) or 'RESOURCE_EXHAUSTED' in str(e):
                match = re.search(r'retry in ([\d\.]+)s', str(e))
                sleep_time = float(match.group(1)) + 1.0 if match else 20.0
                if attempt < 4:
                    logger.warning(f'Rate limit hit, sleeping for {sleep_time}s... (Attempt {attempt+1})')
                    time.sleep(sleep_time)
                else:
                    state['errors'].append(f'Findings error: {e}')
                    break
            else:
                state['errors'].append(f'Findings error: {e}')
                break
                
    return state
"""

recommendations = """import logging
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

def recommendations_node(state: ResearchState) -> ResearchState:
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
        
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", google_api_key=settings.gemini_api_key, max_retries=10)
    structured_llm = llm.with_structured_output(RecommendationList)
    
    findings_text = "\\n".join([f"Finding: {f['statement']}" for f in state['findings']])
    prompt = f"Based on the following findings, generate actionable recommendations for the research question: {state['research_question']}\\n\\nFindings:\\n{findings_text}"
    
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
            if '429' in str(e) or 'RESOURCE_EXHAUSTED' in str(e):
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
"""

with open('backend/app/ai/nodes/planner.py', 'w', encoding='utf-8') as f:
    f.write(planner)
with open('backend/app/ai/nodes/evidence.py', 'w', encoding='utf-8') as f:
    f.write(evidence)
with open('backend/app/ai/nodes/findings.py', 'w', encoding='utf-8') as f:
    f.write(findings)
with open('backend/app/ai/nodes/recommendations.py', 'w', encoding='utf-8') as f:
    f.write(recommendations)
