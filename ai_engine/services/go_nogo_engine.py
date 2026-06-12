"""
Go/No-Go Engine — ML-based bid viability classifier with SHAP explanations.
Evaluates whether the company should bid on an RFP based on extracted features.
Supports training new models from historical bid data and explains decisions
with SHAP feature importance.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

logger = logging.getLogger(__name__)

# Default feature names expected by the model
FEATURE_NAMES = [
    "capability_score",       # 0-1: how well team skills match RFP requirements
    "budget_alignment",       # 0-1: budget size relative to estimated cost
    "timeline_feasibility",   # 0-1: delivery timeline realism
    "past_win_rate",          # 0-1: historical win rate on similar RFPs
    "competitive_intensity",  # 0-1: estimated number of competitors (inverted)
    "strategic_value",        # 0-1: strategic importance of client/sector
]


class GoNoGoEngine:
    """
    Engine to evaluate if the company should bid on an RFP (Go / No-Go decision).
    Uses a scikit-learn RandomForest classifier with SHAP explanations.
    Falls back to a rule-based heuristic if no trained model exists.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or os.getenv(
            "GONOGO_MODEL_PATH", "models/go_nogo_classifier.pkl"
        )
        self.model: Optional[RandomForestClassifier] = None
        self.feature_names = FEATURE_NAMES

        # Attempt to load a pre-trained model
        if Path(self.model_path).exists():
            try:
                self.model = joblib.load(self.model_path)
                logger.info(f"GoNoGoEngine: Loaded trained model from {self.model_path}")
            except Exception as e:
                logger.warning(f"GoNoGoEngine: Could not load model — {e}. Using heuristic.")
        else:
            logger.info(
                f"GoNoGoEngine: No model at '{self.model_path}'. "
                "Using rule-based heuristic until a model is trained."
            )

    def _extract_features(self, rfp_features: Dict[str, Any]) -> np.ndarray:
        """Extract and normalize feature values into a numpy array."""
        features = []
        for name in self.feature_names:
            value = rfp_features.get(name, 0.5)  # default to 0.5 (neutral)
            features.append(float(np.clip(value, 0.0, 1.0)))
        return np.array([features])

    def _heuristic_evaluation(self, features: np.ndarray) -> float:
        """
        Simple weighted-sum fallback when no ML model is available.
        Weights reflect typical business importance ordering.
        """
        weights = [0.25, 0.20, 0.15, 0.20, 0.10, 0.10]
        score = float(np.dot(features[0], weights))
        return score

    def evaluate_bid(self, rfp_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate features extracted from an RFP and return a Go/No-Go decision
        with probability and feature impact explanations.

        Args:
            rfp_features: Dict mapping feature names to values (0-1 scale).
                Expected keys: capability_score, budget_alignment, timeline_feasibility,
                past_win_rate, competitive_intensity, strategic_value.

        Returns:
            Dict with decision, win_probability, feature_impacts, and explanation.
        """
        logger.info("GoNoGoEngine: Analyzing RFP features for Go/No-Go probability.")
        features = self._extract_features(rfp_features)

        if self.model is not None:
            # ── ML Model Path ──
            probability = float(self.model.predict_proba(features)[0][1])
            decision = "GO" if probability >= 0.65 else "NO-GO"

            # SHAP explanations
            feature_impacts = self._compute_shap_values(features)
        else:
            # ── Heuristic Fallback ──
            probability = self._heuristic_evaluation(features)
            decision = "GO" if probability >= 0.65 else "NO-GO"

            # Simplified impact calculation (feature value × weight)
            weights = [0.25, 0.20, 0.15, 0.20, 0.10, 0.10]
            feature_impacts = [
                {
                    "feature": name,
                    "value": float(features[0][i]),
                    "impact": float(features[0][i] * weights[i]),
                    "direction": "positive" if features[0][i] >= 0.5 else "negative",
                }
                for i, name in enumerate(self.feature_names)
            ]

        # Sort impacts by absolute magnitude
        feature_impacts.sort(key=lambda x: abs(x["impact"]), reverse=True)

        result = {
            "decision": decision,
            "win_probability": round(probability, 3),
            "threshold": 0.65,
            "model_type": "random_forest" if self.model else "heuristic",
            "feature_impacts": feature_impacts,
            "top_factors": [
                f"{fi['feature']} ({fi['direction']})" for fi in feature_impacts[:3]
            ],
        }

        logger.info(f"GoNoGoEngine: Decision={decision}, Probability={probability:.3f}")
        return result

    def _compute_shap_values(self, features: np.ndarray) -> List[Dict[str, Any]]:
        """Compute SHAP feature importances using TreeExplainer."""
        try:
            import shap
            explainer = shap.TreeExplainer(self.model)
            shap_values = explainer.shap_values(features)

            # shap_values shape: [2, n_samples, n_features] for binary classification
            # We want class 1 (GO) contributions
            if isinstance(shap_values, list):
                sv = shap_values[1][0]  # class=1, first sample
            else:
                sv = shap_values[0]

            impacts = [
                {
                    "feature": name,
                    "value": float(features[0][i]),
                    "impact": float(sv[i]),
                    "direction": "positive" if sv[i] > 0 else "negative",
                }
                for i, name in enumerate(self.feature_names)
            ]
            return impacts

        except Exception as e:
            logger.warning(f"GoNoGoEngine: SHAP computation failed — {e}. Using feature importances.")
            importances = self.model.feature_importances_
            return [
                {
                    "feature": name,
                    "value": float(features[0][i]),
                    "impact": float(importances[i] * features[0][i]),
                    "direction": "positive" if features[0][i] >= 0.5 else "negative",
                }
                for i, name in enumerate(self.feature_names)
            ]

    def train_model(
        self,
        training_data: List[Dict[str, Any]],
        save: bool = True,
    ) -> Dict[str, Any]:
        """
        Train a new RandomForest classifier on historical bid data.

        Args:
            training_data: List of dicts, each with feature values and a 'label' key (1=won, 0=lost).
            save: Whether to persist the model to disk.

        Returns:
            Training metrics (accuracy, cross-val scores).
        """
        logger.info(f"GoNoGoEngine: Training classifier with {len(training_data)} records.")

        X = np.array([
            [float(d.get(name, 0.5)) for name in self.feature_names]
            for d in training_data
        ])
        y = np.array([int(d["label"]) for d in training_data])

        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            random_state=42,
            class_weight="balanced",
        )
        self.model.fit(X, y)

        # Cross-validation
        cv_scores = cross_val_score(self.model, X, y, cv=min(5, len(y)), scoring="accuracy")

        if save:
            Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.model, self.model_path)
            logger.info(f"GoNoGoEngine: Model saved to {self.model_path}")

        metrics = {
            "samples": len(training_data),
            "accuracy_mean": round(float(cv_scores.mean()), 4),
            "accuracy_std": round(float(cv_scores.std()), 4),
            "feature_importances": {
                name: round(float(imp), 4)
                for name, imp in zip(self.feature_names, self.model.feature_importances_)
            },
        }
        logger.info(f"GoNoGoEngine: Training complete — {metrics}")
        return metrics
