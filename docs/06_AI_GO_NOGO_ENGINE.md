# File: `ai_engine/services/go_nogo_engine.py` — Go/No-Go ML Model & SHAP Explainer

This Python module acts as the strategic gatekeeper, using a machine learning model to evaluate the probability of winning a proposal and computing feature attribution metrics.

---

## 🏗️ 1. Initialization and Model Loading

When the `GoNoGoEngine` class is instantiated, it retrieves Neo4j connection parameters from environment variables and attempts to load the Random Forest model from disk:
```python
def __init__(self, model_path: str = "models/rf_model.joblib"):
    self.model_path = model_path
    self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    self.neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
    self.neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    self.model = None
    self.scaler = None
    if os.path.exists(self.model_path):
        try:
            saved_data = joblib.load(self.model_path)
            if isinstance(saved_data, dict) and 'model' in saved_data:
                self.model = saved_data['model']
                self.scaler = saved_data.get('scaler', None)
            else:
                self.model = saved_data
        except Exception as e:
            logger.error(f"Failed to load model from {self.model_path}: {e}")
```

### Key Elements:
- **`model_path`**: Path to the serialized `joblib` file.
- **Model format flexibility**: The loader is designed to handle both raw scikit-learn models and dictionaries containing both the model and preprocessing scales (`scaler`).

---

## 📊 2. Feature Definitions & Extraction

The Random Forest model requires features in a strict sequence:
```python
self.feature_names = ["compliance_rate", "tech_gap_count", "budget_margin_delta"]
```

### Feature Mechanics:

1. **`compliance_rate`** (from Neo4j):
   Queries Neo4j to count total requirements and calculates the ratio of requirements that have supporting evidence:
   ```cypher
   MATCH (r:Requirement)
   WITH count(r) AS total_reqs
   OPTIONAL MATCH (r)<-[rel:COMPLIES_WITH]-()
   WITH total_reqs, count(rel) AS satisfied_reqs
   RETURN total_reqs, satisfied_reqs
   ```
   If no requirements exist, it defaults to `1.0` (100%). If Neo4j is offline or errors out, it falls back to a neutral `0.5` (50%) to allow the pipeline to continue.

2. **`tech_gap_count`** (from LangGraph State):
   Calculates the count of identified gaps in the `compliance_gaps` array.

3. **`budget_margin_delta`** (from LangGraph State):
   Represents the expected profit margin delta. It is calculated using the total RFP budget and the company's estimated cost:
   $$\text{budget\_margin\_delta} = \frac{\text{rfp\_budget} - \text{company\_base\_cost}}{\text{rfp\_budget}}$$
   If the budget is missing or zero, it defaults to `0.0`.

---

## 🧠 3. Inference, SHAP Explainability & Decision Logic

The `evaluate_rfp(state)` function runs inference and generates explanations:

```python
def evaluate_rfp(self, state: Dict[str, Any]) -> Dict[str, Any]:
    extracted_features = self._extract_features(state)
    
    # 1. Prepare raw inputs into feature array matching the expected order
    X_raw = np.array([[
        extracted_features["compliance_rate"],
        extracted_features["tech_gap_count"],
        extracted_features["budget_margin_delta"]
    ]])
    
    X_scaled = self.scaler.transform(X_raw) if self.scaler else X_raw
```

### Heuristic Fallbacks
If the serialized machine learning model is missing, the engine falls back to a default `win_probability = 0.5` with neutral `0.0` SHAP contributions to prevent errors.

### Inference & Class Probabilities
```python
probas = self.model.predict_proba(X_scaled)
win_probability = float(probas[0][1])
```
Returns the class probability of index `1` (which represents the likelihood of winning the bid).

### SHAP (SHapley Additive exPlanations)
To explain the model's output, it computes SHAP attribution values:
```python
explainer = shap.TreeExplainer(self.model)
shap_values = explainer.shap_values(X_scaled)
```
- For Tree-based ensembles, the SHAP value indicates how much each feature pushes the model's prediction away from the baseline win rate.
- Returns a structured dictionary containing the feature's actual value alongside its positive or negative SHAP contribution.

### Decision Rule
```python
decision = "GO" if win_probability >= 0.65 else "NO-GO"
```
The decision rule uses a **65% threshold**: if the calculated win probability meets or exceeds 65%, the engine recommends proceeding (`GO`); otherwise, it recommends declining the opportunity (`NO-GO`).
