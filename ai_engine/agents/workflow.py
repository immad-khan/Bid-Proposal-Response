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
        _retrieval_service = RetrievalService(vector_store, _bm25_index, reranker)
    return _retrieval_service


# ── Graph Node Wrapper Functions ──

def plan_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Executing Graph Node: [PLAN]")
    llm = get_llm_client()
    retrieval = get_retrieval_service()
    agent = PlannerAgent(llm_client=llm, retrieval_service=retrieval)
    return agent.plan(state)


def write_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Executing Graph Node: [WRITE]")
    llm = get_llm_client()
    retrieval = get_retrieval_service()
    agent = WriterAgent(llm_client=llm, retrieval_service=retrieval)
    return agent.write(state)


def gatekeeper_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Executing Graph Node: [GATEKEEPER]")
    llm = get_llm_client()
    agent = GatekeeperAgent(llm_client=llm)
    return agent.verify(state)


def judge_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Executing Graph Node: [JUDGE]")
    llm = get_llm_client()
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
