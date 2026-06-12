'use client';

import { useState, useEffect } from 'react';
import Overview from '../components/dashboard/Overview';
import ComplianceMatrix from '../components/compliance_matrix/workspace/ComplianceMatrix';
import GoNoGoEvaluator from '../components/compliance_matrix/workspace/GoNoGoEvaluator';
import ProposalSwarmWorkspace from '../components/editor/ProposalSwarmWorkspace';

interface Project {
  id: string;
  name: string;
  rfpBlobUrl: string;
  createdAt: string;
  status: string;
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>('');
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [activeProjectText, setActiveProjectText] = useState<string>('');

  // Default API URL fallback to standard .NET Core Docker port 5000 (net-api port mapping: "5000:8080")
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

  // Load existing projects from .NET backend API
  const fetchProjects = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/project`);
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
        if (data.length > 0 && !activeProjectId) {
          setActiveProjectId(data[0].id);
        }
      }
    } catch (err) {
      console.warn("Could not retrieve projects from .NET API. Mock collection loaded instead.", err);
      // Load mock items for preview
      const mockList: Project[] = [
        {
          id: 'proj-08f2372c-f6ef-46e3-a3d8',
          name: 'RFP-US-East-AWS-Cloud-Migration',
          rfpBlobUrl: 'https://mockstorage.blob.core.windows.net/rfp-uploads/AWS_Migration.pdf',
          createdAt: new Date().toISOString(),
          status: 'Created'
        }
      ];
      setProjects(mockList);
      setActiveProjectId(mockList[0].id);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleUpload = async () => {
    if (!file) {
      setStatus('Please select a PDF document first.');
      return;
    }
    setStatus('Uploading document to .NET backend storage...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${apiUrl}/api/RfpUpload/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server returned status code: ${response.status}`);
      }

      const data = await response.json();
      setStatus(`Success! Proposal ID: ${data.jobId}`);
      
      // Fetch latest projects
      await fetchProjects();
      setActiveProjectId(data.jobId);
    } catch (error) {
      console.error("Upload Error:", error);
      setStatus('Failed to connect to backend service. Check configuration.');
    }
  };

  const getActiveProject = () => {
    return projects.find((p) => p.id === activeProjectId) || null;
  };

  const activeProj = getActiveProject();

  return (
    <div className="flex flex-col min-h-screen bg-zinc-50 dark:bg-zinc-950 font-sans text-zinc-900 dark:text-zinc-50">
      {/* Premium Header */}
      <header className="px-8 py-5 flex justify-between items-center bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-md">
            R
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight">RFP Proposal Response Engine</h1>
            <p className="text-[11px] text-zinc-500 font-medium">Production Swarm Orchestrator v1.0.0</p>
          </div>
        </div>

        {/* Sync Status Badges */}
        <div className="flex gap-3">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-[10px] font-medium text-zinc-600 dark:text-zinc-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            .NET API: Online
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-[10px] font-medium text-zinc-600 dark:text-zinc-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            AI Swarm: Ready
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-[10px] font-medium text-zinc-600 dark:text-zinc-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            Qdrant Vector DB: Synced
          </div>
        </div>
      </header>

      {/* Main Workspace Grid */}
      <main className="flex-grow p-8 grid grid-cols-1 lg:grid-cols-12 gap-8 max-w-[1900px] w-full mx-auto">
        {/* Left Side: Controls & Ingestion */}
        <div className="lg:col-span-4 flex flex-col gap-8">
          
          {/* File Upload Panel */}
          <div className="bg-white dark:bg-zinc-900 p-6 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-sm space-y-4">
            <div>
              <h3 className="font-semibold text-zinc-900 dark:text-zinc-100 text-sm">Document Ingestion Hub</h3>
              <p className="text-xs text-zinc-500 mt-0.5">Upload new RFP PDFs or Word docs for parsing</p>
            </div>

            <div className="border-2 border-dashed border-zinc-200 dark:border-zinc-800 hover:border-indigo-500/50 dark:hover:border-indigo-400/50 rounded-xl p-6 bg-zinc-50/50 dark:bg-zinc-950/20 text-center cursor-pointer transition-all">
              <input 
                type="file" 
                accept=".pdf,.docx"
                className="hidden"
                id="rfp-file-input"
                onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)} 
              />
              <label htmlFor="rfp-file-input" className="cursor-pointer flex flex-col items-center gap-2">
                <div className="w-10 h-10 rounded-lg bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center text-zinc-500 dark:text-zinc-400 text-lg">
                  📥
                </div>
                <span className="text-xs font-semibold text-zinc-800 dark:text-zinc-200">
                  {file ? file.name : 'Click to select document'}
                </span>
                <span className="text-[10px] text-zinc-400 block">PDF or DOCX (max 100MB)</span>
              </label>
            </div>

            <button 
              onClick={handleUpload}
              className="w-full py-2.5 bg-zinc-950 hover:bg-zinc-850 text-zinc-100 dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 font-semibold text-xs rounded-lg shadow-sm transition-all"
            >
              Parse & Upload to Blob
            </button>

            {status && (
              <div className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-800/40 text-[10px] font-mono border border-zinc-150 dark:border-zinc-800 break-all text-zinc-700 dark:text-zinc-300">
                {status}
              </div>
            )}
          </div>

          {/* Project List */}
          <Overview 
            projects={projects}
            activeProjectId={activeProjectId}
            onSelectProject={(id) => setActiveProjectId(id)}
          />

          {/* Go/No-Go Evaluator */}
          <GoNoGoEvaluator apiUrl={apiUrl} />
        </div>

        {/* Right Side: Compliance Matrix and Workspace */}
        <div className="lg:col-span-8 flex flex-col gap-8 h-full">
          {activeProj ? (
            <>
              {/* Proposal Swarm Workspace */}
              <div className="flex-1">
                <ProposalSwarmWorkspace 
                  projectId={activeProj.id}
                  rfpText={activeProjectText || `RFP constraints for ${activeProj.name}. Needs migration to Qdrant Cloud and Neo4j validation.`}
                  apiUrl={apiUrl}
                />
              </div>

              {/* Compliance Matrix Table/Tree */}
              <div className="flex-1">
                <ComplianceMatrix apiUrl={apiUrl} />
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center border border-dashed border-zinc-200 dark:border-zinc-800 rounded-2xl bg-white dark:bg-zinc-900 text-zinc-400 text-xs">
              Select or upload a project to load the active workspace.
            </div>
          )}
        </div>
      </main>
    </div>
  );
}