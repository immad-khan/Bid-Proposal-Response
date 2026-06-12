'use client';

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, ReferenceLine, Cell, Tooltip } from 'recharts';
import { CheckCircle2, XCircle, AlertCircle, DollarSign, TrendingUp } from 'lucide-react';

interface ShapFeature {
  featureName: string;
  value: number;
  shapContribution: number;
}

interface WinProbabilityDetail {
  projectId: string;
  projectName: string;
  client: string;
  winProbability: number;
  complianceScore: number;
  goNoGoDecision: string;
  topFeatures: ShapFeature[];
  complianceGaps: string[];
  rfpBudget: number;
  companyBaseCost: number;
}

interface WinProbabilityChartProps {
  data: WinProbabilityDetail;
}

export default function WinProbabilityChart({ data }: WinProbabilityChartProps) {
  // Format SHAP data for chart
  const chartData = data.topFeatures.map(feat => {
    // Human readable feature names
    let name = feat.featureName;
    if (name === 'compliance_rate') name = 'Compliance Rate';
    if (name === 'tech_gap_count') name = 'Technical Gaps';
    if (name === 'budget_margin_delta') name = 'Budget Margin';

    return {
      name,
      value: feat.shapContribution * 100, // percentage point impact
      rawValue: feat.value,
      displayValue: name === 'Compliance Rate' 
        ? `${(feat.value * 100).toFixed(0)}%` 
        : name === 'Technical Gaps'
          ? `${feat.value} gaps`
          : `${(feat.value * 100).toFixed(0)}% margin`
    };
  });

  const isGo = data.goNoGoDecision === 'GO';

  // Custom Tooltip for Recharts
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload;
      const isPositive = item.value >= 0;
      return (
        <div className="bg-slate-900 border border-slate-700/50 p-3 rounded-lg shadow-xl text-xs backdrop-blur-md">
          <p className="font-semibold text-slate-200">{item.name}</p>
          <p className="text-slate-400 mt-1">
            Current Value: <span className="font-medium text-slate-200">{item.displayValue}</span>
          </p>
          <p className={isPositive ? "text-emerald-400 font-medium mt-0.5" : "text-rose-400 font-medium mt-0.5"}>
            {isPositive ? 'Increases' : 'Decreases'} win chance by {Math.abs(item.value).toFixed(1)}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Metric Dashboard */}
      <div className="lg:col-span-1 bg-slate-900/40 backdrop-blur-md border border-slate-800/80 rounded-2xl p-6 flex flex-col justify-between hover:shadow-2xl hover:shadow-emerald-500/5 transition-all duration-300">
        <div>
          <div className="flex justify-between items-start">
            <div>
              <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Win Probability</span>
              <h3 className="text-slate-100 font-bold text-2xl truncate mt-1">{data.projectName}</h3>
              <p className="text-slate-400 text-xs">{data.client}</p>
            </div>
            <div className={`p-2.5 rounded-xl ${isGo ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
              {isGo ? <CheckCircle2 className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
            </div>
          </div>

          {/* Large Circle Progress */}
          <div className="relative flex items-center justify-center my-8">
            <svg className="w-48 h-48 transform -rotate-90">
              <circle
                cx="96"
                cy="96"
                r="80"
                className="stroke-slate-800/60"
                strokeWidth="10"
                fill="transparent"
              />
              <circle
                cx="96"
                cy="96"
                r="80"
                className={`transition-all duration-1000 ease-out ${isGo ? 'stroke-emerald-500' : 'stroke-amber-500'}`}
                strokeWidth="12"
                fill="transparent"
                strokeDasharray={2 * Math.PI * 80}
                strokeDashoffset={2 * Math.PI * 80 * (1 - data.winProbability)}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute text-center">
              <span className="text-5xl font-black text-slate-100 tracking-tight">
                {(data.winProbability * 100).toFixed(0)}%
              </span>
              <p className="text-slate-400 text-xs font-medium uppercase mt-1 tracking-wider">Win Likelihood</p>
            </div>
          </div>
        </div>

        {/* Go/No-Go Decision Alert Banner */}
        <div className={`p-4 rounded-xl border ${
          isGo 
            ? 'bg-emerald-500/5 border-emerald-500/20 text-emerald-300' 
            : 'bg-rose-500/5 border-rose-500/20 text-rose-300'
        } flex items-center gap-3`}>
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isGo ? 'bg-emerald-500/20' : 'bg-rose-500/20'}`}>
            <TrendingUp className="w-4.5 h-4.5" />
          </div>
          <div>
            <div className="font-bold text-sm">Decision recommendation: {data.goNoGoDecision}</div>
            <div className="text-xs opacity-80">
              {isGo 
                ? 'High probability of capture. Proceeding to response creation is recommended.' 
                : 'Identified gaps reduce win chance. Review compliance before resource allocation.'}
            </div>
          </div>
        </div>
      </div>

      {/* Feature Attribution (SHAP Chart) */}
      <div className="lg:col-span-2 flex flex-col justify-between bg-slate-900/40 backdrop-blur-md border border-slate-800/80 rounded-2xl p-6 hover:shadow-2xl hover:shadow-emerald-500/5 transition-all duration-300">
        <div>
          <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">AI Strategic Insights</span>
          <h4 className="text-slate-100 font-bold text-lg mt-1">Feature Contribution Analysis</h4>
          <p className="text-slate-400 text-xs mt-0.5">Impact of RFP criteria on win probability based on past performance historical models (SHAP explanation).</p>
          
          <div className="h-64 mt-6">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 10, right: 30, left: 40, bottom: 10 }}
              >
                <XAxis 
                  type="number" 
                  domain={[-30, 30]} 
                  tickFormatter={(v) => `${v}%`}
                  stroke="#64748b" 
                  fontSize={10} 
                />
                <YAxis 
                  type="category" 
                  dataKey="name" 
                  stroke="#64748b" 
                  fontSize={11}
                  tickLine={false}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                <ReferenceLine x={0} stroke="#475569" strokeWidth={1.5} />
                <Bar dataKey="value" radius={[4, 4, 4, 4]} barSize={24}>
                  {chartData.map((entry, index) => {
                    const isPositive = entry.value >= 0;
                    return (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={isPositive ? '#10b981' : '#f43f5e'} 
                        className="transition-colors duration-300 hover:opacity-85 cursor-pointer"
                      />
                    );
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Technical Gaps and Financial Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-6 border-t border-slate-800/80 mt-4">
          <div>
            <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <AlertCircle className="w-4 h-4" />
              <span>Compliance Gaps ({data.complianceGaps.length})</span>
            </div>
            <ul className="space-y-1.5">
              {data.complianceGaps.map((gap, i) => (
                <li key={i} className="text-slate-300 text-xs flex items-start gap-1.5">
                  <span className="text-amber-500 mt-1">•</span>
                  <span>{gap}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="flex flex-col justify-between bg-slate-950/40 p-4 rounded-xl border border-slate-800/50">
            <div>
              <div className="flex items-center gap-2 text-slate-400 text-xs font-semibold uppercase tracking-wider mb-3">
                <DollarSign className="w-4 h-4 text-emerald-400" />
                <span>Financial Alignment</span>
              </div>
              <div className="flex justify-between items-center text-xs mb-1.5">
                <span className="text-slate-400">RFP Budget:</span>
                <span className="font-semibold text-slate-200">${data.rfpBudget.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Company Base Cost:</span>
                <span className="font-semibold text-slate-200">${data.companyBaseCost.toLocaleString()}</span>
              </div>
            </div>
            <div className="text-[10px] text-slate-400 mt-3 border-t border-slate-800/50 pt-2 flex justify-between">
              <span>Gross Margin Potential:</span>
              <span className="font-medium text-emerald-400">
                {(((data.rfpBudget - data.companyBaseCost) / data.rfpBudget) * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
