import React, { useState, useEffect } from 'react';
import { apiClient } from '../../../services/apiClient';

interface Requirement {
  id: string;
  section_path: string;
  description: string;
  is_mandatory: boolean;
  status?: 'COMPLIANT' | 'PARTIAL' | 'NON_COMPLIANT';
  evidence?: string;
  score?: number;
}

export default function ComplianceMatrix({ apiUrl }: { apiUrl: string }) {
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMatrix = async () => {
      try {
        const data = await apiClient.getCompliance();
        if (data && Array.isArray(data)) {
          setRequirements(data);
        }
      } catch (err) {
        console.warn('Failed to fetch compliance matrix, falling back to empty list.', err);
      } finally {
        setLoading(false);
      }
    };
    fetchMatrix();
  }, []);

  const [filter, setFilter] = useState<'ALL' | 'COMPLIANT' | 'PARTIAL' | 'NON_COMPLIANT'>('ALL');
  const [newReq, setNewReq] = useState({ id: '', path: '', desc: '' });

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'COMPLIANT':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400 dark:border-emerald-900/50';
      case 'PARTIAL':
        return 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/30 dark:text-amber-400 dark:border-amber-900/50';
      case 'NON_COMPLIANT':
        return 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/30 dark:text-rose-400 dark:border-rose-900/50';
      default:
        return 'bg-zinc-50 text-zinc-600 border-zinc-200 dark:bg-zinc-900/30 dark:text-zinc-400 dark:border-zinc-800';
    }
  };

  const handleAddRequirement = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newReq.id || !newReq.desc) return;
    const req: Requirement = {
      id: newReq.id,
      section_path: newReq.path || 'General',
      description: newReq.desc,
      is_mandatory: true,
      status: 'NON_COMPLIANT',
    };
    setRequirements((prev) => [...prev, req]);
    setNewReq({ id: '', path: '', desc: '' });
  };

  const filteredReqs = requirements.filter(
    (r) => filter === 'ALL' || r.status === filter
  );

  return (
    <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-sm overflow-hidden flex flex-col h-full min-h-[400px]">
      <div className="p-5 border-b border-zinc-100 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/50">
        <h3 className="font-semibold text-zinc-900 dark:text-zinc-100 text-sm">Compliance Matrix Mapping</h3>
        <p className="text-xs text-zinc-500 mt-0.5">Neo4j Knowledge Graph Requirements Traceability</p>

        {/* Filters */}
        <div className="flex gap-2 mt-4">
          {(['ALL', 'COMPLIANT', 'PARTIAL', 'NON_COMPLIANT'] as const).map((opt) => (
            <button
              key={opt}
              onClick={() => setFilter(opt)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                filter === opt
                  ? 'bg-zinc-900 text-white border-zinc-900 dark:bg-zinc-100 dark:text-black'
                  : 'bg-white text-zinc-600 border-zinc-200 hover:bg-zinc-50 dark:bg-zinc-800 dark:text-zinc-300 dark:border-zinc-700'
              }`}
            >
              {opt.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Requirement List */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {filteredReqs.map((req) => (
          <div
            key={req.id}
            className="p-4 rounded-xl border border-zinc-100 dark:border-zinc-800 bg-zinc-50/30 dark:bg-zinc-800/10 space-y-2.5 transition-all hover:shadow-sm"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <span className="font-mono text-xs font-semibold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/40 px-2 py-0.5 rounded">
                  {req.id}
                </span>
                <span className="text-xs text-zinc-400 ml-2 italic">{req.section_path}</span>
              </div>
              <span
                className={`text-[10px] font-bold px-2.5 py-1 rounded-full border ${getStatusColor(
                  req.status
                )}`}
              >
                {req.status}
              </span>
            </div>

            <p className="text-sm text-zinc-700 dark:text-zinc-300 font-medium">
              {req.description}
            </p>

            {req.evidence && (
              <div className="text-xs text-zinc-500 bg-zinc-50 dark:bg-zinc-800/50 p-2.5 rounded border border-zinc-100 dark:border-zinc-800/50">
                <span className="font-semibold block text-zinc-600 dark:text-zinc-400 mb-0.5">
                  Resolution Evidence:
                </span>
                {req.evidence}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Quick Add Requirement Form */}
      <form
        onSubmit={handleAddRequirement}
        className="p-4 border-t border-zinc-100 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/50 space-y-3"
      >
        <h4 className="text-xs font-semibold text-zinc-700 dark:text-zinc-300">
          Inject Custom Requirement
        </h4>
        <div className="grid grid-cols-2 gap-2">
          <input
            type="text"
            placeholder="ID (e.g., REQ-005)"
            value={newReq.id}
            onChange={(e) => setNewReq((prev) => ({ ...prev, id: e.target.value }))}
            className="w-full px-3 py-2 text-xs border rounded-lg dark:bg-zinc-800 dark:border-zinc-700 outline-none focus:border-indigo-500"
          />
          <input
            type="text"
            placeholder="Section Path"
            value={newReq.path}
            onChange={(e) => setNewReq((prev) => ({ ...prev, path: e.target.value }))}
            className="w-full px-3 py-2 text-xs border rounded-lg dark:bg-zinc-800 dark:border-zinc-700 outline-none focus:border-indigo-500"
          />
        </div>
        <textarea
          placeholder="Requirement description..."
          value={newReq.desc}
          onChange={(e) => setNewReq((prev) => ({ ...prev, desc: e.target.value }))}
          rows={2}
          className="w-full px-3 py-2 text-xs border rounded-lg dark:bg-zinc-800 dark:border-zinc-700 outline-none focus:border-indigo-500 resize-none"
        />
        <button
          type="submit"
          className="w-full py-2 bg-zinc-950 hover:bg-zinc-800 dark:bg-zinc-100 dark:hover:bg-zinc-200 text-white dark:text-black font-semibold text-xs rounded-lg transition-colors"
        >
          Add to Neo4j Graph
        </button>
      </form>
    </div>
  );
}
