import os
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

def train_mock_model():
    """
    Generates dummy historical data and trains a RandomForest model 
    for the Go/No-Go Engine, saving it to a .joblib file.
    """
    print("Generating dummy historical data...")
    # Features: [compliance_rate, tech_gap_count, budget_margin_delta]
    np.random.seed(42)
    
    # Generate 500 mock samples
    compliance_rates = np.random.uniform(0.5, 1.0, 500)
    tech_gap_counts = np.random.randint(0, 10, 500)
    budget_margin_deltas = np.random.uniform(-0.2, 0.4, 500)
    
    # Create target variable based on a simple heuristic with some noise
    # Win (1) is more likely if compliance > 0.8, gaps < 3, margin > 0.1
    labels = []
    for c, g, m in zip(compliance_rates, tech_gap_counts, budget_margin_deltas):
        score = (c * 0.4) - (g * 0.05) + (m * 0.5)
        # Add random noise
        score += np.random.normal(0, 0.1)
        labels.append(1 if score > 0.35 else 0)
        
    df = pd.DataFrame({
        'compliance_rate': compliance_rates,
        'tech_gap_count': tech_gap_counts,
        'budget_margin_delta': budget_margin_deltas,
        'label': labels
    })
    
    X = df[['compliance_rate', 'tech_gap_count', 'budget_margin_delta']]
    y = df['label']
    
    print("Training StandardScaler and RandomForestClassifier...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X_scaled, y)
    
    print(f"Training complete. Model Accuracy: {model.score(X_scaled, y):.2f}")
    
    # Save the model and scaler
    output_dir = "models"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "rf_model.joblib")
    
    joblib.dump({'model': model, 'scaler': scaler}, output_path)
    print(f"Model saved to {output_path}")

if __name__ == "__main__":
    train_mock_model()
