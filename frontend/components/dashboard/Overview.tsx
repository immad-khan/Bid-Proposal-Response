import React from 'react';

interface Project {
  id: string;
  name: string;
  rfpBlobUrl: string;
  createdAt: string;
  status: string;
}

export default function Overview({
  projects,
  activeProjectId,
  onSelectProject,
}: {
  projects: Project[];
  activeProjectId: string | null;
  onSelectProject: (id: string) => void;
}) {
  return (
    <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-sm p-5 space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="font-semibold text-zinc-900 dark:text-zinc-100 text-sm">Proposal Project Library</h3>
          <p className="text-xs text-zinc-500 mt-0.5">Historical records & active compilation status</p>
        </div>
      </div>

      <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
        {projects.length === 0 ? (
          <div className="py-8 text-center text-xs text-zinc-400">
            No projects registered yet. Upload an RFP document to begin.
          </div>
        ) : (
          projects.map((proj) => (
            <div
              key={proj.id}
              onClick={() => onSelectProject(proj.id)}
              className={`py-3.5 px-3 flex items-center justify-between cursor-pointer rounded-lg transition-all ${
                activeProjectId === proj.id
                  ? 'bg-zinc-50 dark:bg-zinc-800/60 border-l-4 border-indigo-600'
                  : 'hover:bg-zinc-50/50 dark:hover:bg-zinc-800/30'
              }`}
            >
              <div className="space-y-1">
                <span className="font-medium text-xs text-zinc-900 dark:text-zinc-100 block">
                  {proj.name}
                </span>
                <span className="text-[10px] text-zinc-400 block font-mono">
                  ID: {proj.id.substring(0, 8)}...
                </span>
              </div>
              <div className="text-right flex flex-col items-end gap-1">
                <span className="text-[10px] text-zinc-400">
                  {new Date(proj.createdAt).toLocaleDateString()}
                </span>
                <span className="px-2 py-0.5 text-[9px] font-bold uppercase rounded bg-indigo-50 text-indigo-700 border border-indigo-150 dark:bg-indigo-950/40 dark:text-indigo-400 dark:border-indigo-900">
                  {proj.status}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
