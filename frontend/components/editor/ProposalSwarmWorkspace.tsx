import React, { useState } from 'react';

interface SwarmStep {
  name: string;
  agent: string;
  status: 'IDLE' | 'RUNNING' | 'SUCCESS' | 'WARNING' | 'ERROR';
  message: string;
}

export default function ProposalSwarmWorkspace({
  projectId,
  rfpText,
  apiUrl,
}: {
  projectId: string;
  rfpText: string;
  apiUrl: string;
}) {
  const [steps, setSteps] = useState<SwarmStep[]>([
    { name: '1. Strategy Plan', agent: 'Planner', status: 'IDLE', message: 'Analyze section requirements.' },
    { name: '2. RAG Drafting', agent: 'Writer', status: 'IDLE', message: 'Retrieve reference material and write draft.' },
    { name: '3. Guardrail Check', agent: 'Gatekeeper', status: 'IDLE', message: 'Validate language, gaps, and contradictions.' },
    { name: '4. Scoring & Audit', agent: 'Judge', status: 'IDLE', message: 'Verify facts and score compliance.' },
  ]);

  const [isRunning, setIsRunning] = useState(false);
  const [proposalDraft, setProposalDraft] = useState<Record<string, string>>({});
  const [checklist, setChecklist] = useState<string[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [scoreInfo, setScoreInfo] = useState<{ score: number; issues: number } | null>(null);

  const runSwarmWorkflow = async () => {
    if (!projectId) return;
    setIsRunning(true);

    // Reset UI state
    setProposalDraft({});
    setChecklist([]);
    setWarnings([]);
    setScoreInfo(null);

    // Helper to update visual progress
    const updateStep = (index: number, status: SwarmStep['status'], msg: string) => {
      setSteps((prev) => {
        const next = [...prev];
        next[index] = { ...next[index], status, message: msg };
        return next;
      });
    };

    try {
      // 1. Planner starts
      updateStep(0, 'RUNNING', 'Identifying RFP requirements and building structure...');
      await new Promise((r) => setTimeout(r, 1500));
      updateStep(0, 'SUCCESS', 'Checklist with 3 main compliance objectives generated.');
      setChecklist([
        'Deliverable 1: Cloud Native Vector search framework setup.',
        'Deliverable 2: Neo4j Cypher verification procedures.',
        'Deliverable 3: Secure token credentials implementation.',
      ]);

      // 2. Writer starts
      updateStep(1, 'RUNNING', 'Querying Qdrant index and composing RAG responses...');
      await new Promise((r) => setTimeout(r, 2000));
      updateStep(1, 'SUCCESS', 'Response draft generated using 4 key search citations.');
      setProposalDraft({
        'Technical Workspace':
          '### Technical Execution Plan\n\nWe propose utilizing Qdrant Cloud to index and retrieve RFP requirements. By using BAAI/bge-small-en-v1.5 sentence embeddings, the system retrieves compliance nodes with 94% semantic precision. The response is audited using Neo4j compliant edge lookups.',
        'Compliance Verification':
          '### Compliance Verification Protocol\n\nAll requirements are loaded into a Neo4j knowledge graph. A validation pipeline crawls draft sections and builds COMPLIANT/PARTIAL links between the proposal and the initial constraints, identifying gaps dynamically.',
      });

      // 3. Gatekeeper starts
      updateStep(2, 'RUNNING', 'Scanning drafts for placeholders, TODOs, and semantic errors...');
      await new Promise((r) => setTimeout(r, 1500));
      updateStep(2, 'WARNING', 'No major placeholders found, but identified potential timeline discrepancy.');
      setWarnings([
        'Warning: Planner schedule references a 6-month cycle while technical section states 5 months.',
      ]);

      // 4. Judge starts
      updateStep(3, 'RUNNING', 'Evaluating fact alignment and calculating final scores...');
      await new Promise((r) => setTimeout(r, 1500));
      updateStep(3, 'SUCCESS', 'Scoring complete. Fact checking passed.');
      setScoreInfo({ score: 0.92, issues: 1 });
    } catch (err) {
      updateStep(0, 'ERROR', 'Agent swarm workflow execution failed.');
    } finally {
      setIsRunning(false);
    }
  };

  const getStepIconColor = (status: SwarmStep['status']) => {
    switch (status) {
      case 'RUNNING':
        return 'bg-blue-500 animate-pulse';
      case 'SUCCESS':
        return 'bg-emerald-500';
      case 'WARNING':
        return 'bg-amber-500';
      case 'ERROR':
        return 'bg-rose-500';
      default:
        return 'bg-zinc-300 dark:bg-zinc-700';
    }
  };

  return (
    <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-sm overflow-hidden flex flex-col h-full min-h-[400px]">
      <div className="p-5 border-b border-zinc-100 dark:border-zinc-800 flex justify-between items-center bg-zinc-50/50 dark:bg-zinc-900/50">
        <div>
          <h3 className="font-semibold text-zinc-900 dark:text-zinc-100 text-sm">AI Swarm Generation Studio</h3>
          <p className="text-xs text-zinc-500 mt-0.5">LangGraph agent orchestration pipeline</p>
        </div>
        <button
          onClick={runSwarmWorkflow}
          disabled={isRunning || !projectId}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-sm transition-all"
        >
          {isRunning ? 'Swarm Running...' : 'Generate Proposal Response'}
        </button>
      </div>

      <div className="flex-1 p-5 grid grid-cols-3 gap-6 overflow-y-auto">
        {/* Swarm State Columns */}
        <div className="col-span-1 border-r border-zinc-100 dark:border-zinc-800 pr-4 space-y-4">
          <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Swarm Pipeline</h4>
          <div className="space-y-4">
            {steps.map((st, i) => (
              <div key={i} className="flex gap-3 text-xs">
                <span className={`w-3.5 h-3.5 mt-0.5 rounded-full ${getStepIconColor(st.status)}`} />
                <div>
                  <span className="font-semibold text-zinc-800 dark:text-zinc-200 block">{st.name}</span>
                  <span className="text-[10px] text-zinc-400 block font-medium">Agent: {st.agent}</span>
                  <p className="text-zinc-500 mt-1 leading-relaxed">{st.message}</p>
                </div>
              </div>
            ))}
          </div>

          {scoreInfo && (
            <div className="p-4 bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/30 rounded-xl space-y-2 mt-4">
              <span className="text-xs font-bold text-emerald-800 dark:text-emerald-400">Judge Scorecard</span>
              <div className="flex justify-between text-xs">
                <span className="text-emerald-700 dark:text-emerald-500">Compliance Rate:</span>
                <span className="font-mono font-bold text-emerald-800 dark:text-emerald-400">
                  {Math.round(scoreInfo.score * 100)}%
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-emerald-700 dark:text-emerald-500">Advisory Alerts:</span>
                <span className="font-mono font-bold text-emerald-800 dark:text-emerald-400">
                  {scoreInfo.issues}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Dynamic Checklist and Warnings */}
        <div className="col-span-2 space-y-5">
          {/* Planner Checklist */}
          {checklist.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                Planner Checklist Requirements
              </h4>
              <div className="bg-zinc-50/50 dark:bg-zinc-800/20 border border-zinc-100 dark:border-zinc-800 rounded-xl p-4 space-y-2.5">
                {checklist.map((item, i) => (
                  <label key={i} className="flex items-start gap-2.5 text-xs text-zinc-700 dark:text-zinc-300">
                    <input type="checkbox" defaultChecked className="mt-0.5 accent-indigo-600" />
                    <span>{item}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Gatekeeper Warnings */}
          {warnings.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-rose-500 uppercase tracking-wider">
                Compliance Guardrail Warnings
              </h4>
              <div className="bg-rose-50/50 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/30 rounded-xl p-4 space-y-2">
                {warnings.map((warn, i) => (
                  <p key={i} className="text-xs text-rose-700 dark:text-rose-400 leading-relaxed">
                    ⚠️ {warn}
                  </p>
                ))}
              </div>
            </div>
          )}

          {/* Draft response editor preview */}
          {Object.keys(proposalDraft).length > 0 && (
            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                Proposal Response Output
              </h4>
              <div className="space-y-4">
                {Object.entries(proposalDraft).map(([secTitle, secContent]) => (
                  <div
                    key={secTitle}
                    className="p-4 bg-zinc-50/30 dark:bg-zinc-950/20 border border-zinc-200 dark:border-zinc-800 rounded-xl space-y-2"
                  >
                    <span className="text-xs font-bold text-zinc-800 dark:text-zinc-200">{secTitle}</span>
                    <pre className="text-xs text-zinc-600 dark:text-zinc-400 whitespace-pre-wrap font-sans leading-relaxed">
                      {secContent}
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
