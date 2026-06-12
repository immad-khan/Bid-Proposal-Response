import os
import logging
from typing import Dict, Any, List
import joblib
import numpy as np
import shap
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

class GoNoGoEngine:
    """
    Module 5.0: Go/No-Go ML Engine (The Strategic Brain)
    Acts as a gatekeeper using RandomForest and SHAP to predict win probability.
    """
    
    def __init__(self, model_path: str = "models/rf_model.joblib"):
        self.model_path = model_path
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        # Load the ML model
        self.model = None
        self.scaler = None
        if os.path.exists(self.model_path):
            try:
                # Expecting a dict containing both model and scaler, or just model
                saved_data = joblib.load(self.model_path)
                if isinstance(saved_data, dict) and 'model' in saved_data:
                    self.model = saved_data['model']
                    self.scaler = saved_data.get('scaler', None)
                else:
                    self.model = saved_data
            except Exception as e:
                logger.error(f"Failed to load model from {self.model_path}: {e}")
                
        # Define the strict feature order expected by the model
        self.feature_names = ["compliance_rate", "tech_gap_count", "budget_margin_delta"]

    def _get_neo4j_compliance_rate(self) -> float:
        """
        Query Neo4j to count total Requirement nodes and how many 
        are satisfied by an Evidence (or COMPLIES_WITH a ProposalSection).
        """
        query = """
        MATCH (r:Requirement)
        WITH count(r) AS total_reqs
        OPTIONAL MATCH (r)<-[rel:COMPLIES_WITH]-()
        WITH total_reqs, count(rel) AS satisfied_reqs
        RETURN total_reqs, satisfied_reqs
        """
        try:
            driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
            with driver.session() as session:
                result = session.run(query).single()
                if not result or result["total_reqs"] == 0:
                    return 1.0 # Default to 100% if no rules exist
                
                total = result["total_reqs"]
                satisfied = result["satisfied_reqs"]
                return satisfied / total
        except Exception as e:
            logger.error(f"Neo4j query failed: {e}")
            return 0.5 # Neutral fallback

    def _extract_features(self, state: Dict[str, Any]) -> Dict[str, float]:
        """
        Combine LangGraph state metrics with Neo4j compliance rate.
        """
        # 1. Neo4j Compliance Rate
        compliance_rate = self._get_neo4j_compliance_rate()
        
        # 2. Tech Gap Count
        gaps = state.get("compliance_gaps", [])
        tech_gap_count = float(len(gaps))
        
        # 3. Budget Margin Delta
        rfp_budget = float(state.get("rfp_budget", 100000))
        company_base_cost = float(state.get("company_base_cost", 80000))
        
        if rfp_budget > 0:
            budget_margin_delta = (rfp_budget - company_base_cost) / rfp_budget
        else:
            budget_margin_delta = 0.0
            
        return {
            "compliance_rate": compliance_rate,
            "tech_gap_count": tech_gap_count,
            "budget_margin_delta": budget_margin_delta
        }

    def evaluate_rfp(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates the RFP and returns the decision payload.
        """
        # 1. Feature Extraction
        extracted_features = self._extract_features(state)
        
        # Create ordered feature array
        X_raw = np.array([[
            extracted_features["compliance_rate"],
            extracted_features["tech_gap_count"],
            extracted_features["budget_margin_delta"]
        ]])
        
        # Apply scaling if a scaler was loaded
        X_scaled = self.scaler.transform(X_raw) if self.scaler else X_raw

        # 2. Inference
        if self.model is None:
            # Fallback heuristic if no model is loaded
            win_probability = 0.5
            shap_dict = {f: {"value": extracted_features[f], "attribution": 0.0} for f in self.feature_names}
        else:
            # Predict probability of class 1 (Win)
            probas = self.model.predict_proba(X_scaled)
            win_probability = float(probas[0][1])
            
            # 4. Explainability (SHAP)
            try:
                explainer = shap.TreeExplainer(self.model)
                shap_values = explainer.shap_values(X_scaled)
                
                # Handling binary classification output format
                if isinstance(shap_values, list):
                    sv = shap_values[1][0] # class 1
                else:
                    # Depending on shap/model version, might just be a 2D array
                    sv = shap_values[0] if len(shap_values.shape) == 2 else shap_values[1][0]
                    
                shap_dict = {}
                for i, name in enumerate(self.feature_names):
                    shap_dict[name] = {
                        "value": float(extracted_features[name]),
                        "attribution": float(sv[i])
                    }
            except Exception as e:
                logger.error(f"SHAP explanation failed: {e}")
                shap_dict = {f: {"value": extracted_features[f], "attribution": 0.0} for f in self.feature_names}

        # 3. Decision Logic
        decision = "GO" if win_probability >= 0.65 else "NO-GO"

        return {
            "win_probability": round(win_probability, 3),
            "decision": decision,
            "features_extracted": extracted_features,
            "shap_explanations": shap_dict
        }
