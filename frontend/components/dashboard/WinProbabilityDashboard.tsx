import React, { useState } from 'react';

interface FeatureImpact {
  feature: string;
  value: number;
  attribution: number;
}

interface RFPProject {
  id: string;
  name: string;
  status: 'Ingestion' | 'Drafting' | 'Completed';
  budget: number;
  winProbability: number;
  decision: 'GO' | 'NO-GO' | 'PENDING';
  shapData: FeatureImpact[];
}

// Mock data simulating the backend integration from Module 5
const mockProjects: RFPProject[] = [
  {
    id: 'proj-101',
    name: 'US Air Force Cloud Migration RFP',
    status: 'Completed',
    budget: 1500000,
    winProbability: 0.82,
    decision: 'GO',
    shapData: [
      { feature: 'compliance_rate', value: 1.0, attribution: 0.15 },
      { feature: 'tech_gap_count', value: 0, attribution: 0.08 },
      { feature: 'budget_margin_delta', value: 0.35, attribution: 0.12 },
    ]
  },
  {
    id: 'proj-102',
    name: 'State Dept Cybersecurity Audit',
    status: 'Drafting',
    budget: 450000,
    winProbability: 0.31,
    decision: 'NO-GO',
    shapData: [
      { feature: 'compliance_rate', value: 0.75, attribution: -0.22 },
      { feature: 'tech_gap_count', value: 4, attribution: -0.18 },
      { feature: 'budget_margin_delta', value: -0.1, attribution: -0.05 },
    ]
  },
  {
    id: 'proj-103',
    name: 'NHS Patient Portal Upgrade',
    status: 'Ingestion',
    budget: 850000,
    winProbability: 0.68,
    decision: 'GO',
    shapData: [
      { feature: 'compliance_rate', value: 0.92, attribution: 0.10 },
      { feature: 'tech_gap_count', value: 1, attribution: 0.02 },
      { feature: 'budget_margin_delta', value: 0.15, attribution: 0.06 },
    ]
  }
];

export default function WinProbabilityDashboard() {
  const [activeProject, setActiveProject] = useState<RFPProject | null>(null);

  const stats = {
    ingestion: mockProjects.filter(p => p.status === 'Ingestion').length,
    drafting: mockProjects.filter(p => p.status === 'Drafting').length,
    goRevenue: mockProjects.filter(p => p.decision === 'GO').reduce((acc, p) => acc + p.budget, 0),
  };

  return (
    <div className="w-full h-full bg-zinc-950 text-zinc-100 p-6 md:p-8 font-sans overflow-y-auto">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
            Win Probability Dashboard
          </h1>
          <p className="text-zinc-400 mt-2">Executive Overview & ML Go/No-Go Engine Insights</p>
        </div>

        {/* 7.3 Pipeline Health KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-lg shadow-black/50">
            <p className="text-sm text-zinc-400 font-medium uppercase tracking-wider mb-1">In Ingestion</p>
            <p className="text-4xl font-bold text-zinc-100">{stats.ingestion}</p>
            <div className="mt-4 h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
              <div className="h-full bg-cyan-500 w-1/3" />
            </div>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-lg shadow-black/50">
            <p className="text-sm text-zinc-400 font-medium uppercase tracking-wider mb-1">Being Drafted</p>
            <p className="text-4xl font-bold text-zinc-100">{stats.drafting}</p>
            <div className="mt-4 h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
              <div className="h-full bg-indigo-500 w-2/3" />
            </div>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-lg shadow-black/50">
            <p className="text-sm text-zinc-400 font-medium uppercase tracking-wider mb-1">Projected "GO" Revenue</p>
            <p className="text-4xl font-bold text-emerald-400">
              ${(stats.goRevenue / 1000000).toFixed(2)}M
            </p>
            <div className="mt-4 h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
              <div className="h-full bg-emerald-500 w-full" />
            </div>
          </div>
        </div>

        {/* 7.4 Drill Down Area */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* RFP List */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-lg shadow-black/50 flex flex-col h-[500px]">
            <h3 className="text-lg font-semibold text-zinc-200 mb-4">RFP Pipeline</h3>
            <div className="flex-1 overflow-y-auto pr-2 space-y-3">
              {mockProjects.map(proj => (
                <div 
                  key={proj.id}
                  onClick={() => setActiveProject(proj)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    activeProject?.id === proj.id 
                      ? 'bg-zinc-800 border-cyan-500/50 shadow-md shadow-cyan-900/20' 
                      : 'bg-zinc-950/50 border-zinc-800 hover:border-zinc-700 hover:bg-zinc-800/80'
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-medium text-zinc-200 text-sm">{proj.name}</h4>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold tracking-wider ${
                      proj.decision === 'GO' ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-800' :
                      'bg-rose-900/50 text-rose-400 border border-rose-800'
                    }`}>
                      {proj.decision}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-xs text-zinc-500">
                    <span>Status: <span className="text-zinc-300">{proj.status}</span></span>
                    <span>Win Prob: <span className={proj.winProbability >= 0.65 ? 'text-emerald-400' : 'text-rose-400'}>{(proj.winProbability * 100).toFixed(0)}%</span></span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* SHAP Explainer */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-lg shadow-black/50 flex flex-col h-[500px]">
            <h3 className="text-lg font-semibold text-zinc-200 mb-4">ML Explanation (SHAP)</h3>
            
            {!activeProject ? (
              <div className="flex-1 flex items-center justify-center text-zinc-500 text-sm">
                Select an RFP to view probability drivers
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto">
                <div className="mb-6 pb-6 border-b border-zinc-800">
                  <h4 className="text-base text-zinc-200 font-medium mb-1">{activeProject.name}</h4>
                  <p className="text-xs text-zinc-400 leading-relaxed">
                    The model predicts a <strong className={activeProject.winProbability >= 0.65 ? "text-emerald-400" : "text-rose-400"}>{(activeProject.winProbability * 100).toFixed(1)}%</strong> chance of winning this bid. 
                    Below are the mathematical drivers (SHAP values) that pushed the score {activeProject.winProbability >= 0.5 ? 'up' : 'down'}.
                  </p>
                </div>

                <div className="space-y-5">
                  {activeProject.shapData.map((feature, idx) => {
                    const isPositive = feature.attribution > 0;
                    // Normalize attribution for visual bar length (max ~0.25)
                    const widthPercent = Math.min(100, Math.abs(feature.attribution) * 400); 

                    return (
                      <div key={idx} className="relative">
                        <div className="flex justify-between items-end mb-1.5">
                          <div>
                            <span className="text-xs font-mono text-zinc-300">{feature.feature}</span>
                            <span className="text-[10px] text-zinc-500 ml-2">(Val: {feature.value})</span>
                          </div>
                          <span className={`text-xs font-medium ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {isPositive ? '+' : ''}{feature.attribution.toFixed(3)}
                          </span>
                        </div>
                        
                        {/* Bi-directional Bar Chart */}
                        <div className="w-full h-2 bg-zinc-800 rounded-full flex items-center relative">
                          <div className="absolute left-1/2 top-0 bottom-0 w-px bg-zinc-600 z-10" />
                          <div 
                            className={`h-full absolute rounded-full ${isPositive ? 'bg-emerald-500 left-1/2' : 'bg-rose-500 right-1/2'}`}
                            style={{ width: `${widthPercent / 2}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
