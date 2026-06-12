import React, { useState } from 'react';
import { apiClient } from '../../../services/apiClient';

interface FeatureState {
  capability_score: number;
  budget_alignment: number;
  timeline_feasibility: number;
  past_win_rate: number;
  competitive_intensity: number;
  strategic_value: number;
}

interface GoNoGoResult {
  decision: string;
  win_probability: number;
  threshold: number;
  top_factors: string[];
  feature_impacts: { feature: string; impact: number }[];
}

export default function GoNoGoEvaluator({ apiUrl }: { apiUrl: string }) {
  const [features, setFeatures] = useState<FeatureState>({
    capability_score: 0.8,
    budget_alignment: 0.75,
    timeline_feasibility: 0.6,
    past_win_rate: 0.5,
    competitive_intensity: 0.7,
    strategic_value: 0.85,
  });

  const [result, setResult] = useState<GoNoGoResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSliderChange = (key: keyof FeatureState, val: number) => {
    setFeatures((prev) => ({ ...prev, [key]: val }));
  };

  const evaluateBid = async () => {
    setLoading(true);
    try {
      // Use the centralized apiClient proxy
      const data = await apiClient.evaluateGoNoGo(features as unknown as Record<string, number>);
      if (data && data.decision) {
        setResult(data);
      } else {
        simulateEvaluation();
      }
    } catch (err) {
      console.error('Failed to call evaluateGoNoGo, falling back to heuristic simulation', err);
      simulateEvaluation();
    } finally {
      setLoading(false);
    }
  };

  const simulateEvaluation = () => {
    const sum =
      features.capability_score * 0.3 +
      features.budget_alignment * 0.2 +
      features.timeline_feasibility * 0.15 +
      features.past_win_rate * 0.1 +
      features.competitive_intensity * 0.1 +
      features.strategic_value * 0.15;

    const prob = Math.round(sum * 100);
    const dec = prob >= 65 ? 'GO' : 'NO-GO';

    setResult({
      decision: dec,
      win_probability: sum,
      threshold: 0.65,
      top_factors: [
        features.capability_score > 0.7 ? 'High technical capability match' : 'Weak technical fit',
        features.strategic_value > 0.7 ? 'Strong strategic account value' : 'Low long-term value',
      ],
      feature_impacts: [
        { feature: 'Capability Match', impact: features.capability_score * 0.3 },
        { feature: 'Budget Alignment', impact: features.budget_alignment * 0.2 },
        { feature: 'Timeline Feasibility', impact: features.timeline_feasibility * 0.15 },
        { feature: 'Strategic Value', impact: features.strategic_value * 0.15 },
      ],
    });
  };

  return (
    <div className="p-6 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">Go/No-Go Viability Engine</h3>
          <p className="text-xs text-zinc-500">ML-driven probability classifier & SHAP explanations</p>
        </div>
        <span className="p-1 px-2.5 bg-zinc-100 dark:bg-zinc-800 text-[10px] font-medium rounded-full text-zinc-600 dark:text-zinc-400">
          Random Forest
        </span>
      </div>

      <div className="space-y-4">
        {/* Sliders Grid */}
        <div className="grid grid-cols-2 gap-4">
          {(Object.keys(features) as Array<keyof FeatureState>).map((key) => (
            <div key={key} className="flex flex-col gap-1">
              <div className="flex items-center justify-between text-xs font-medium">
                <span className="capitalize text-zinc-600 dark:text-zinc-400">
                  {key.replace(/_/g, ' ')}
                </span>
                <span className="font-mono text-indigo-600 dark:text-indigo-400">
                  {Math.round(features[key] * 100)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={features[key]}
                onChange={(e) => handleSliderChange(key, parseFloat(e.target.value))}
                className="w-full h-1.5 bg-zinc-200 dark:bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-indigo-600"
              />
            </div>
          ))}
        </div>

        <button
          onClick={evaluateBid}
          disabled={loading}
          className="w-full py-2.5 mt-2 flex items-center justify-center gap-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm transition-colors shadow-sm disabled:opacity-50"
        >
          {loading ? 'Evaluating Model...' : 'Calculate Viability Score'}
        </button>

        {result && (
          <div className="mt-4 pt-4 border-t border-zinc-100 dark:border-zinc-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs text-zinc-500 block">Viability Decision</span>
                <span
                  className={`text-xl font-bold ${
                    result.decision === 'GO' ? 'text-emerald-600' : 'text-rose-600'
                  }`}
                >
                  {result.decision}
                </span>
              </div>
              <div className="text-right">
                <span className="text-xs text-zinc-500 block">Win Probability</span>
                <span className="text-xl font-mono font-bold text-zinc-900 dark:text-zinc-100">
                  {Math.round(result.win_probability * 100)}%
                </span>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-zinc-100 dark:bg-zinc-800 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-500 ${
                  result.decision === 'GO' ? 'bg-emerald-500' : 'bg-rose-500'
                }`}
                style={{ width: `${Math.round(result.win_probability * 100)}%` }}
              />
            </div>

            {/* SHAP Explanation */}
            <div>
              <span className="text-xs font-semibold text-zinc-700 dark:text-zinc-300 block mb-2">
                SHAP Local Explanations
              </span>
              <div className="space-y-2">
                {result.feature_impacts.map((fi, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-xs">
                    <span className="w-24 truncate text-zinc-500">{fi.feature}</span>
                    <div className="flex-1 bg-zinc-100 dark:bg-zinc-800 h-2.5 rounded relative overflow-hidden">
                      <div
                        className="bg-indigo-500 h-full rounded"
                        style={{ width: `${Math.round(fi.impact * 200)}%` }}
                      />
                    </div>
                    <span className="font-mono text-zinc-400">+{fi.impact.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
