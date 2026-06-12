"""
LangGraph Multi-Agent Swarm Orchestrator.
Defines the StateGraph nodes, edges, and compilation for executing
the planning, writing, compliance checks, and judge scoring sequence.
"""

import logging
from typing import Dict, Any, List

from langgraph.graph import StateGraph, END

from agents.state import AgentState
from agents.planner import PlannerAgent
from agents.writer import WriterAgent
from agents.gatekeeper import GatekeeperAgent
from agents.judge import JudgeAgent

from services.llm_client import LLMClient
from services.vector_store import VectorStore
from services.bm25_index import BM25Index
from services.reranker import Reranker
from services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)


# ── Lazy Global Service Initialization ──
# To prevent slow application startup, instantiate clients on-demand
_llm_client = None
_retrieval_service = None
_bm25_index = None


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


def get_retrieval_service() -> RetrievalService:
    global _retrieval_service, _bm25_index
    if _retrieval_service is None:
        vector_store = VectorStore()
        _bm25_index = BM25Index()
        reranker = Reranker()
        
        # Try to pre-load capability_library into BM25 from Qdrant
        try:
            # Check if collection exists
            collections = vector_store.client.get_collections().collections
            if any(c.name == "capability_library" for c in collections):
                # Scroll points to build the BM25 index
                points, _ = vector_store.client.scroll(
                    collection_name="capability_library", 
                    limit=1000, 
                    with_payload=True
                )
                if points:
                    docs = []
                    for pt in points:
                        docs.append({
                            "id": str(pt.id),
                            "text_for_embedding": pt.payload.get("text", ""),
                            "original_text": pt.payload.get("original_text", ""),
                            "metadata": {k: v for k, v in pt.payload.items() if k not in ("text", "original_text")}
                        })
                    _bm25_index.index_documents(docs, collection_name="capability_library")
        except Exception as e:
            logger.warning(f"Could not pre-load capability_library into BM25: {e}")
            
        _retrieval_service = RetrievalService(vector_store, _bm25_index, reranker)
    return _retrieval_service


import os

# ── Graph Node Wrapper Functions ──

def plan_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Executing Graph Node: [PLAN]")
    llm = LLMClient(
        api_key=os.getenv("PLANNER_GROQ_API_KEY"),
        backup_api_key=os.getenv("PLANNER_GROQ_API_KEY_BACKUP")
    )
    retrieval = get_retrieval_service()
    agent = PlannerAgent(llm_client=llm, retrieval_service=retrieval)
    return agent.plan(state)


def write_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Executing Graph Node: [WRITE]")
    llm = LLMClient(
        api_key=os.getenv("WRITER_GROQ_API_KEY"),
        backup_api_key=os.getenv("WRITER_GROQ_API_KEY_BACKUP")
    )
    retrieval = get_retrieval_service()
    agent = WriterAgent(llm_client=llm, retrieval_service=retrieval)
    return agent.write(state)


def gatekeeper_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Executing Graph Node: [GATEKEEPER]")
    llm = LLMClient(
        api_key=os.getenv("GATEKEEPER_GROQ_API_KEY"),
        backup_api_key=os.getenv("GATEKEEPER_GROQ_API_KEY_BACKUP")
    )
    agent = GatekeeperAgent(llm_client=llm)
    return agent.verify(state)


def judge_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Executing Graph Node: [JUDGE]")
    llm = LLMClient(
        api_key=os.getenv("JUDGE_GROQ_API_KEY"),
        backup_api_key=os.getenv("JUDGE_GROQ_API_KEY_BACKUP")
    )
    agent = JudgeAgent(llm_client=llm)
    return agent.score(state)


# ── LangGraph Compilation ──

# Define StateGraph with AgentState type
workflow = StateGraph(AgentState)

# Add Agent Nodes
workflow.add_node("planner", plan_node)
workflow.add_node("writer", write_node)
workflow.add_node("gatekeeper", gatekeeper_node)
workflow.add_node("judge", judge_node)

# Set Up Standard Pipeline Edges
workflow.set_entry_point("planner")
workflow.add_edge("planner", "writer")
workflow.add_edge("writer", "gatekeeper")
workflow.add_edge("gatekeeper", "judge")
workflow.add_edge("judge", END)

# Compile into a Runnable Graph
proposal_swarm_graph = workflow.compile()
logger.info("LangGraph multi-agent swarm workflow successfully compiled.")
