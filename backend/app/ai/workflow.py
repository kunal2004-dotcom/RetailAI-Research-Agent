from langgraph.graph import StateGraph, END
from backend.app.ai.state import ResearchState
from backend.app.ai.nodes.planner import plan_research
from backend.app.ai.nodes.search import search_sources
from backend.app.ai.nodes.evidence import extract_evidence
from backend.app.ai.nodes.retrieval import ingest_and_retrieve
from backend.app.ai.nodes.findings import generate_findings
from backend.app.ai.nodes.recommendations import generate_recommendations

workflow = StateGraph(ResearchState)

workflow.add_node("planner", plan_research)
workflow.add_node("search", search_sources)
workflow.add_node("retrieval", ingest_and_retrieve)
workflow.add_node("evidence", extract_evidence)
workflow.add_node("findings", generate_findings)
workflow.add_node("recommendations", generate_recommendations)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "search")
workflow.add_edge("search", "retrieval")
workflow.add_edge("retrieval", "evidence")
workflow.add_edge("evidence", "findings")
workflow.add_edge("findings", "recommendations")
workflow.add_edge("recommendations", END)

research_graph = workflow.compile()
