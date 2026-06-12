'use client';

import { useState, useEffect, useCallback } from 'react';
import Image from "next/image";
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  FolderOpen,
  ChevronRight,
  Sparkles,
  Server,
  Clock,
  X,
  Zap,
  Users,
  Download,
  History,
  TrendingUp,
  Plus,
  Send,
  UserPlus
} from 'lucide-react';

import { apiClient } from '../services/apiClient';
import WinProbabilityChart from '../components/WinProbabilityChart';
import InlineDocumentEditor from '../components/InlineDocumentEditor';
import VersionDiff from '../components/VersionDiff';

interface Project {
  id: string;
  name: string;
  clientName?: string;
  rfpBlobUrl: string;
  createdAt: string;
  status: string;
}

// ─── Animation Variants ───
const containerVariants: any = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.2 }
  }
};

const itemVariants: any = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { type: "spring", stiffness: 100, damping: 15 }
  }
};

const pulseRing: any = {
  scale: [1, 1.2, 1],
  opacity: [0.5, 0, 0.5],
  transition: { duration: 2, repeat: Infinity, ease: "easeInOut" }
};

import WinProbabilityDashboard from '../components/dashboard/WinProbabilityDashboard';

export default function Home() {
  const [viewMode, setViewMode] = useState<'upload' | 'dashboard'>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>('');
  const [statusType, setStatusType] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // New Workspace and Dashboard states
  const [activeTab, setActiveTab] = useState<'analytics' | 'editor' | 'versions' | 'collab'>('analytics');
  const [analysis, setAnalysis] = useState<any | null>(null);
  const [workspace, setWorkspace] = useState<any | null>(null);
  const [versions, setVersions] = useState<any[]>([]);
  const [isWorkspaceLoading, setIsWorkspaceLoading] = useState(false);
  const [isAnalysisLoading, setIsAnalysisLoading] = useState(false);
  const [isActionRunning, setIsActionRunning] = useState(false);

  // Invite states
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('Editor');
  const [inviteMsg, setInviteMsg] = useState('');

  // Version Comparison / Diff states
  const [compareVer1, setCompareVer1] = useState<string>('');
  const [compareVer2, setCompareVer2] = useState<string>('');
  const [ver1Content, setVer1Content] = useState<string>('');
  const [ver2Content, setVer2Content] = useState<string>('');
  const [showDiff, setShowDiff] = useState(false);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5282';

  // 1. Auto-login on mount to obtain JWT token for auth endpoints
  useEffect(() => {
    const autoLogin = async () => {
      try {
        const authData = await apiClient.login('admin', 'password');
        if (authData && authData.token) {
          apiClient.setToken(authData.token);
          console.log('Successfully authenticated as admin with JWT token.');
        }
      } catch (err) {
        console.warn('Auto-login failed. Using local mock/anonymous requests.', err);
      }
    };
    autoLogin();
  }, []);

  const fetchProjects = useCallback(async () => {
    try {
      const data = await apiClient.getProjects();
      setProjects(data);
      if (data.length > 0 && !activeProjectId) {
        setActiveProjectId(data[0].id);
      }
    } catch (err) {
      console.error("Failed to retrieve projects from API.", err);
      // Removed mock fallback as per production requirements.
      setProjects([]);
    }
  }, [activeProjectId]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // Load detailed analysis & workspace details for active project
  const loadProjectData = useCallback(async (projectId: string) => {
    setIsAnalysisLoading(true);
    setIsWorkspaceLoading(true);
    
    // 1. Fetch detailed win probability analysis
    try {
      const analysisData = await apiClient.getDetailedAnalysis(projectId);
      setAnalysis(analysisData);
    } catch (err) {
      console.error("Failed to retrieve detailed analysis from API.", err);
      setAnalysis(null);
    } finally {
      setIsAnalysisLoading(false);
    }

    // 2. Fetch workspace details
    try {
      const workspaceData = await apiClient.getWorkspace(projectId);
      setWorkspace(workspaceData);
      
      // Fetch version history
      const history = await apiClient.getVersionHistory(projectId);
      setVersions(history);
      
      // Set default version selections for diff
      if (history.length >= 2) {
        setCompareVer1(history[1].id);
        setCompareVer2(history[0].id);
      } else if (history.length === 1) {
        setCompareVer1(history[0].id);
        setCompareVer2(history[0].id);
      }
    } catch (err) {
      console.warn("Workspace not found or unauthorized. Setting null workspace.", err);
      setWorkspace(null);
      setVersions([]);
    } finally {
      setIsWorkspaceLoading(false);
    }
  }, [projects]);

  useEffect(() => {
    if (activeProjectId) {
      loadProjectData(activeProjectId);
    }
  }, [activeProjectId, loadProjectData]);

  // Create workspace action
  const handleCreateWorkspace = async () => {
    if (!activeProjectId) return;
    const project = projects.find(p => p.id === activeProjectId);
    if (!project) return;
    
    setIsActionRunning(true);
    try {
      const newWs = await apiClient.createWorkspace(
        `${project.name} Workspace`,
        `Collaboration space for drafting ${project.name} response.`,
        activeProjectId
      );
      // Save initial v1 draft
      const defaultContent = JSON.stringify([
        {
          type: 'paragraph',
          children: [{ text: `Proposal Response for ${project.name}. Client: ${project.clientName || 'General Client'}.` }]
        }
      ]);
      await apiClient.saveDraft(newWs.id, defaultContent, "Initial workspace version created.");
      
      // Reload project details
      await loadProjectData(activeProjectId);
    } catch (err) {
      console.error("Failed to create workspace:", err);
      alert("Failed to initialize workspace: " + err);
    } finally {
      setIsActionRunning(false);
    }
  };

  // Save draft editor action
  const handleSaveWorkspaceDraft = async (contentJson: string, comment: string) => {
    if (!activeProjectId) return;
    try {
      const savedVersion = await apiClient.saveDraft(activeProjectId, contentJson, comment);
      // Reload history and workspace
      const history = await apiClient.getVersionHistory(activeProjectId);
      setVersions(history);
      setWorkspace((prev: any) => ({
        ...prev,
        currentVersion: savedVersion.versionNumber,
        currentContent: contentJson
      }));
      return savedVersion;
    } catch (err) {
      console.error("Save draft failed:", err);
      throw err;
    }
  };

  // Compare versions action
  const handleCompareVersions = async () => {
    if (!compareVer1 || !compareVer2) return;
    setIsActionRunning(true);
    try {
      const v1 = await apiClient.getVersion(compareVer1);
      const v2 = await apiClient.getVersion(compareVer2);
      setVer1Content(v1.content);
      setVer2Content(v2.content);
      setShowDiff(true);
    } catch (err) {
      console.error("Failed to load versions for comparison:", err);
      alert("Failed to fetch version content: " + err);
    } finally {
      setIsActionRunning(false);
    }
  };

  // Export proposal action
  const handleExport = async (format: string) => {
    if (!activeProjectId) return;
    setIsActionRunning(true);
    try {
      const res = await apiClient.exportProposal(activeProjectId, format);
      if (res && res.downloadUrl) {
        window.open(res.downloadUrl, '_blank');
      } else {
        alert("Export generated, but no download URL was returned.");
      }
    } catch (err) {
      console.error("Export failed:", err);
      alert("Export failed: " + err);
    } finally {
      setIsActionRunning(false);
    }
  };

  // Team invitation action
  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProjectId || !inviteEmail) return;
    setIsActionRunning(true);
    setInviteMsg('Sending invitation...');
    try {
      const res = await apiClient.inviteMember(activeProjectId, inviteEmail, inviteRole);
      setInviteMsg(res.message || 'Invitation sent successfully!');
      setInviteEmail('');
      setTimeout(() => {
        loadProjectData(activeProjectId);
        setInviteMsg('');
      }, 2000);
    } catch (err) {
      console.error("Invitation failed:", err);
      setInviteMsg('Invitation failed: ' + err);
    } finally {
      setIsActionRunning(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && (droppedFile.name.endsWith('.pdf') || droppedFile.name.endsWith('.docx'))) {
      setFile(droppedFile);
      setStatus('');
      setStatusType('idle');
    } else {
      setStatus('Please drop a .pdf or .docx file');
      setStatusType('error');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setStatus('Please select a file first.');
      setStatusType('error');
      return;
    }

    setStatus('Initializing upload...');
    setStatusType('loading');
    setUploadProgress(0);

    const progressInterval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) return prev;
        return prev + Math.random() * 15;
      });
    }, 300);

    try {
      const data = await apiClient.uploadRfp(file);
      clearInterval(progressInterval);
      setUploadProgress(100);
      setStatus(`Upload complete! Job ID: ${data.jobId || data.id}`);
      setStatusType('success');

      // Refresh projects after successful upload
      setTimeout(() => fetchProjects(), 500);
    } catch (error) {
      clearInterval(progressInterval);
      console.error("Upload Error:", error);
      setStatus('Upload failed. Check your browser console or backend terminal.');
      setStatusType('error');
      setUploadProgress(0);
    }
  };

  const clearFile = () => {
    setFile(null);
    setStatus('');
    setStatusType('idle');
    setUploadProgress(0);
  };

  const getStatusIcon = () => {
    switch (statusType) {
      case 'loading': return <Loader2 className="w-5 h-5 animate-spin text-cyan-400" />;
      case 'success': return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
      case 'error': return <AlertCircle className="w-5 h-5 text-rose-400" />;
      default: return null;
    }
  };

  const getStatusColor = () => {
    switch (statusType) {
      case 'loading': return 'border-cyan-500/30 bg-cyan-950/20 text-cyan-200';
      case 'success': return 'border-emerald-500/30 bg-emerald-950/20 text-emerald-200';
      case 'error': return 'border-rose-500/30 bg-rose-950/20 text-rose-200';
      default: return 'border-zinc-700/50 bg-zinc-900/50 text-zinc-400';
    }
  };

  const activeProject = projects.find(p => p.id === activeProjectId);

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-zinc-100 font-sans selection:bg-cyan-500/30 overflow-x-hidden pb-24">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-[128px] animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-violet-500/10 rounded-full blur-[128px] animate-pulse delay-1000" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-blue-500/5 rounded-full blur-[150px]" />
      </div>

      {/* Grid Pattern Overlay */}
      <div 
        className="fixed inset-0 opacity-[0.02] pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: '50px 50px'
        }}
      />

      <div className="relative z-10 max-w-6xl mx-auto px-4 py-12 lg:py-20">
        {/* Header */}
        <motion.header 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-16"
        >
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-emerald-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <motion.div 
                className="absolute inset-0 rounded-xl bg-cyan-400/30"
                animate={pulseRing as any}
              />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-white to-zinc-400 bg-clip-text text-transparent">
                RFP Response Engine
              </h1>
              <p className="text-xs text-zinc-500 flex items-center gap-1">
                <Server className="w-3 h-3 text-emerald-400" />
                Connected to .NET 10 API
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center bg-zinc-900/80 border border-zinc-800 rounded-full p-1 backdrop-blur-sm">
              <button
                onClick={() => setViewMode('upload')}
                className={`px-4 py-1.5 text-xs font-semibold rounded-full transition-all ${
                  viewMode === 'upload' ? 'bg-cyan-500/20 text-cyan-400' : 'text-zinc-500 hover:text-zinc-300'
                }`}
              >
                RFP Ingestion
              </button>
              <button
                onClick={() => setViewMode('dashboard')}
                className={`px-4 py-1.5 text-xs font-semibold rounded-full transition-all ${
                  viewMode === 'dashboard' ? 'bg-cyan-500/20 text-cyan-400' : 'text-zinc-500 hover:text-zinc-355'
                }`}
              >
                Executive Dashboard
              </button>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-900/80 border border-zinc-800 backdrop-blur-sm">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs text-zinc-400 font-medium hidden sm:inline">System Online</span>
            </div>
          </div>
        </motion.header>

        {viewMode === 'upload' ? (
          <>
            <div className="grid lg:grid-cols-5 gap-8">
          {/* Left Panel - Upload */}
          <motion.div 
            className="lg:col-span-3 space-y-6"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            {/* Hero Card */}
            <motion.div 
              variants={itemVariants}
              className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-zinc-900/90 to-zinc-950/90 border border-zinc-800/50 backdrop-blur-xl p-8 lg:p-10"
            >
              <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-cyan-500/10 to-transparent rounded-full blur-3xl" />

              <div className="relative z-10">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-semibold mb-6">
                  <Zap className="w-3 h-3 text-cyan-400" />
                  RFP Intelligence Swarm
                </div>

                <h2 className="text-3xl lg:text-4xl font-bold mb-3 bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent">
                  Upload RFP Document
                </h2>
                <p className="text-zinc-400 text-sm lg:text-base max-w-md leading-relaxed">
                  Drop your proposal documents here to analyze, process, and generate intelligent responses powered by our backend engine.
                </p>
              </div>
            </motion.div>

            {/* Drop Zone */}
            <motion.div variants={itemVariants}>
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`
                  relative group cursor-pointer rounded-3xl border-2 border-dashed transition-all duration-300 overflow-hidden
                  ${isDragging 
                    ? 'border-cyan-500 bg-cyan-500/10 scale-[1.02]' 
                    : file 
                      ? 'border-emerald-500/50 bg-emerald-500/5' 
                      : 'border-zinc-700 hover:border-zinc-500 hover:bg-zinc-900/50'
                  }
                `}
              >
                <input
                  type="file"
                  accept=".pdf,.docx"
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
                  onChange={(e) => {
                    const selected = e.target.files?.[0];
                    if (selected) {
                      setFile(selected);
                      setStatus('');
                      setStatusType('idle');
                    }
                  }}
                />

                <div className="p-10 lg:p-14 flex flex-col items-center justify-center text-center relative z-10">
                  <AnimatePresence mode="wait">
                    {file ? (
                      <motion.div
                        key="file"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        className="flex flex-col items-center gap-4"
                      >
                        <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 flex items-center justify-center">
                          <FileText className="w-8 h-8 text-emerald-400" />
                        </div>
                        <div>
                          <p className="text-lg font-semibold text-zinc-200">{file.name}</p>
                          <p className="text-sm text-zinc-500 mt-1">
                            {(file.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            clearFile();
                          }}
                          className="mt-2 p-2 rounded-full hover:bg-zinc-800 transition-colors"
                        >
                          <X className="w-4 h-4 text-zinc-500" />
                        </button>
                      </motion.div>
                    ) : (
                      <motion.div
                        key="empty"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        className="flex flex-col items-center gap-4"
                      >
                        <motion.div 
                          className="w-20 h-20 rounded-3xl bg-zinc-800/80 flex items-center justify-center group-hover:bg-zinc-800 transition-colors"
                          whileHover={{ scale: 1.05, rotate: 5 }}
                        >
                          <Upload className="w-10 h-10 text-zinc-500 group-hover:text-cyan-400 transition-colors" />
                        </motion.div>
                        <div>
                          <p className="text-lg font-medium text-zinc-300">
                            {isDragging ? 'Drop it here!' : 'Drag & drop your file'}
                          </p>
                          <p className="text-sm text-zinc-500 mt-1">
                            or click to browse — supports PDF, DOCX
                          </p>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Progress Bar */}
                <AnimatePresence>
                  {statusType === 'loading' && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="absolute bottom-0 left-0 right-0 h-1 bg-zinc-800"
                    >
                      <motion.div
                        className="h-full bg-gradient-to-r from-cyan-500 to-emerald-500"
                        initial={{ width: 0 }}
                        animate={{ width: `${uploadProgress}%` }}
                        transition={{ duration: 0.3 }}
                      />
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>

            {/* Upload Button */}
            <motion.div variants={itemVariants}>
              <button
                onClick={handleUpload}
                disabled={!file || statusType === 'loading'}
                className={`
                  w-full relative overflow-hidden rounded-2xl py-4 px-6 font-semibold text-sm transition-all duration-300
                  ${!file 
                    ? 'bg-zinc-900 text-zinc-600 cursor-not-allowed border border-zinc-800' 
                    : statusType === 'loading'
                      ? 'bg-zinc-800 text-zinc-400 cursor-wait border border-zinc-700'
                      : 'bg-gradient-to-r from-cyan-600 to-emerald-600 text-white hover:shadow-lg hover:shadow-cyan-500/25 hover:scale-[1.02] active:scale-[0.98]'
                  }
                `}
              >
                <span className="relative z-10 flex items-center justify-center gap-2">
                  {statusType === 'loading' ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Analyzing Document...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      Analyze & Extract Compliance Matrix
                    </>
                  )}
                </span>
                {file && statusType !== 'loading' && (
                  <motion.div
                    className="absolute inset-0 bg-gradient-to-r from-cyan-400/20 to-emerald-400/20"
                    initial={{ x: '-100%' }}
                    whileHover={{ x: '100%' }}
                    transition={{ duration: 0.6 }}
                  />
                )}
              </button>
            </motion.div>

            {/* Status Message */}
            <AnimatePresence>
              {status && (
                <motion.div
                  initial={{ opacity: 0, y: 10, height: 0 }}
                  animate={{ opacity: 1, y: 0, height: 'auto' }}
                  exit={{ opacity: 0, y: -10, height: 0 }}
                  className={`
                    rounded-2xl border p-4 flex items-start gap-3 backdrop-blur-sm
                    ${getStatusColor()}
                  `}
                >
                  {getStatusIcon()}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium break-all">{status}</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>

          {/* Right Panel - Projects */}
          <motion.div 
            className="lg:col-span-2"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4, duration: 0.6 }}
          >
            <div className="sticky top-8 space-y-6">
              {/* Projects Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FolderOpen className="w-5 h-5 text-zinc-400" />
                  <h3 className="text-lg font-semibold text-zinc-200">Active Proposals</h3>
                </div>
                <span className="text-xs text-zinc-500 bg-zinc-900 px-2 py-1 rounded-full border border-zinc-800">
                  {projects.length} active
                </span>
              </div>

              {/* Project List */}
              <div className="space-y-3">
                <AnimatePresence>
                  {projects.map((project, index) => (
                    <motion.div
                      key={project.id}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      transition={{ delay: index * 0.1 }}
                      onClick={() => {
                        setActiveProjectId(project.id);
                        setActiveTab('analytics');
                      }}
                      className={`
                        group relative p-4 rounded-2xl border cursor-pointer transition-all duration-300
                        ${activeProjectId === project.id 
                          ? 'bg-zinc-900/80 border-cyan-500/30 shadow-lg shadow-cyan-500/10' 
                          : 'bg-zinc-900/40 border-zinc-800/50 hover:border-zinc-700 hover:bg-zinc-900/60'
                        }
                      `}
                    >
                      {/* Active Indicator */}
                      {activeProjectId === project.id && (
                        <motion.div
                          layoutId="activeIndicator"
                          className="absolute left-0 top-4 bottom-4 w-1 rounded-full bg-gradient-to-b from-cyan-500 to-emerald-500"
                        />
                      )}

                      <div className="flex items-start justify-between pl-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <FileText className="w-4 h-4 text-zinc-500 flex-shrink-0" />
                            <p className="text-sm font-medium text-zinc-200 truncate">
                              {project.name}
                            </p>
                          </div>
                          <div className="flex items-center gap-3 text-xs text-zinc-500">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {new Date(project.createdAt).toLocaleDateString()}
                            </span>
                            <span className={`
                              px-2 py-0.5 rounded-full text-[10px] font-semibold
                              ${project.status === 'Created' 
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                                : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                              }
                            `}>
                              {project.status}
                            </span>
                          </div>
                        </div>
                        <ChevronRight className={`
                          w-4 h-4 transition-all duration-300 flex-shrink-0
                          ${activeProjectId === project.id 
                            ? 'text-cyan-400 translate-x-0 opacity-100' 
                            : 'text-zinc-600 -translate-x-2 opacity-0 group-hover:translate-x-0 group-hover:opacity-100'
                          }
                        `} />
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>

              {/* Empty State */}
              {projects.length === 0 && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-center py-12 rounded-2xl border border-dashed border-zinc-800 bg-zinc-900/20"
                >
                  <FolderOpen className="w-8 h-8 text-zinc-600 mx-auto mb-2" />
                  <p className="text-sm text-zinc-500">No proposals created yet</p>
                </motion.div>
              )}
            </div>
          </motion.div>
            </div>

            {/* ─── Win Probability & Collaboration Workspace Panel ─── */}
            {activeProjectId && activeProject && (
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mt-16 pt-16 border-t border-zinc-800/80 space-y-6"
          >
            {/* Project Header Info */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div>
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-widest">Active Workspace</span>
                <h2 className="text-2xl font-black text-slate-100 mt-1">{activeProject.name}</h2>
                <p className="text-slate-400 text-xs mt-0.5">
                  Client: <span className="font-semibold text-slate-350">{activeProject.clientName || 'NASA Jet Propulsion Lab'}</span>
                </p>
              </div>

              {/* Tab selector */}
              <div className="flex bg-slate-900/80 border border-slate-800 p-1 rounded-xl gap-1 backdrop-blur-sm self-stretch md:self-auto">
                <button
                  onClick={() => setActiveTab('analytics')}
                  className={`flex-1 md:flex-none px-4 py-2 text-xs font-bold rounded-lg transition-all ${
                    activeTab === 'analytics' 
                      ? 'bg-emerald-500/10 text-emerald-450 border border-emerald-500/20 shadow-md shadow-emerald-500/5' 
                      : 'text-slate-450 hover:text-slate-200'
                  }`}
                >
                  📊 Dashboard
                </button>
                <button
                  onClick={() => setActiveTab('editor')}
                  className={`flex-1 md:flex-none px-4 py-2 text-xs font-bold rounded-lg transition-all ${
                    activeTab === 'editor' 
                      ? 'bg-emerald-500/10 text-emerald-450 border border-emerald-500/20 shadow-md shadow-emerald-500/5' 
                      : 'text-slate-450 hover:text-slate-200'
                  }`}
                >
                  📝 Slate Editor
                </button>
                <button
                  onClick={() => setActiveTab('versions')}
                  className={`flex-1 md:flex-none px-4 py-2 text-xs font-bold rounded-lg transition-all ${
                    activeTab === 'versions' 
                      ? 'bg-emerald-500/10 text-emerald-450 border border-emerald-500/20 shadow-md shadow-emerald-500/5' 
                      : 'text-slate-450 hover:text-slate-200'
                  }`}
                >
                  🕒 Version Diff
                </button>
                <button
                  onClick={() => setActiveTab('collab')}
                  className={`flex-1 md:flex-none px-4 py-2 text-xs font-bold rounded-lg transition-all ${
                    activeTab === 'collab' 
                      ? 'bg-emerald-500/10 text-emerald-450 border border-emerald-500/20 shadow-md shadow-emerald-500/5' 
                      : 'text-slate-450 hover:text-slate-200'
                  }`}
                >
                  👥 Collaboration
                </button>
              </div>
            </div>

            {/* Tab content area */}
            <div className="min-h-[400px]">
              {/* Analytics tab */}
              {activeTab === 'analytics' && (
                <div>
                  {isAnalysisLoading ? (
                    <div className="flex flex-col items-center justify-center py-20 gap-3">
                      <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
                      <span className="text-slate-400 text-sm">Loading Win Probability Analysis...</span>
                    </div>
                  ) : analysis ? (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                      <WinProbabilityChart data={analysis} />
                    </motion.div>
                  ) : (
                    <div className="text-center py-16 text-slate-500">
                      No analysis data available.
                    </div>
                  )}
                </div>
              )}

              {/* Editor tab */}
              {activeTab === 'editor' && (
                <div>
                  {isWorkspaceLoading ? (
                    <div className="flex flex-col items-center justify-center py-20 gap-3">
                      <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
                      <span className="text-slate-400 text-sm">Loading Workspace...</span>
                    </div>
                  ) : workspace ? (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                      <InlineDocumentEditor
                        initialContentJson={workspace.currentContent}
                        workspaceId={activeProjectId}
                        onSave={handleSaveWorkspaceDraft}
                        versionNumber={workspace.currentVersion || 1}
                      />
                    </motion.div>
                  ) : (
                    <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-10 text-center flex flex-col items-center gap-4 max-w-lg mx-auto">
                      <div className="w-12 h-12 rounded-full bg-amber-500/10 text-amber-500 flex items-center justify-center border border-amber-500/20">
                        <AlertCircle className="w-6 h-6" />
                      </div>
                      <div>
                        <h4 className="text-slate-200 font-bold">No Proposal Workspace Created</h4>
                        <p className="text-slate-400 text-xs mt-1 leading-relaxed">
                          This proposal does not have an active collaboration workspace yet. Create one now to begin drafting and editing.
                        </p>
                      </div>
                      <button
                        onClick={handleCreateWorkspace}
                        disabled={isActionRunning}
                        className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-cyan-600 text-white font-bold text-xs hover:shadow-lg hover:shadow-emerald-500/20 transition-all flex items-center gap-2"
                      >
                        {isActionRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                        Initialize Workspace & Document
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Versions / Diff tab */}
              {activeTab === 'versions' && (
                <div>
                  {isWorkspaceLoading ? (
                    <div className="flex flex-col items-center justify-center py-20 gap-3">
                      <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
                      <span className="text-slate-400 text-sm">Loading Version History...</span>
                    </div>
                  ) : versions.length > 0 ? (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                      {/* Version Selectors */}
                      <div className="bg-slate-900/40 border border-slate-800 p-6 rounded-2xl flex flex-col md:flex-row justify-between items-center gap-4">
                        <div className="flex flex-col md:flex-row gap-4 items-center w-full md:w-auto">
                          <div>
                            <label className="block text-[10px] uppercase font-bold tracking-wider text-slate-500 mb-1.5">Baseline Version</label>
                            <select
                              value={compareVer1}
                              onChange={(e) => setCompareVer1(e.target.value)}
                              className="bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                            >
                              {versions.map(v => (
                                <option key={v.id} value={v.id}>
                                  v{v.versionNumber} ({new Date(v.createdAt).toLocaleTimeString()}) - {v.createdBy}
                                </option>
                              ))}
                            </select>
                          </div>
                          
                          <div className="text-slate-600 font-bold text-xs hidden md:block">vs</div>
                          
                          <div>
                            <label className="block text-[10px] uppercase font-bold tracking-wider text-slate-500 mb-1.5">Comparison Target</label>
                            <select
                              value={compareVer2}
                              onChange={(e) => setCompareVer2(e.target.value)}
                              className="bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                            >
                              {versions.map(v => (
                                <option key={v.id} value={v.id}>
                                  v{v.versionNumber} ({new Date(v.createdAt).toLocaleTimeString()}) - {v.createdBy}
                                </option>
                              ))}
                            </select>
                          </div>
                        </div>

                        <button
                          onClick={handleCompareVersions}
                          disabled={isActionRunning}
                          className="w-full md:w-auto px-6 py-3 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-450 border border-emerald-500/20 font-bold text-xs transition-colors flex items-center justify-center gap-2"
                        >
                          {isActionRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <History className="w-4 h-4" />}
                          Compare Selected Versions
                        </button>
                      </div>

                      {/* Diff View */}
                      {showDiff && (
                        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                          <VersionDiff
                            oldContentJson={ver1Content}
                            newContentJson={ver2Content}
                            oldVersionLabel={`v${versions.find(v => v.id === compareVer1)?.versionNumber || 'A'}`}
                            newVersionLabel={`v${versions.find(v => v.id === compareVer2)?.versionNumber || 'B'}`}
                          />
                        </motion.div>
                      )}

                      {/* Version table list */}
                      <div className="bg-slate-950 border border-slate-800/80 rounded-2xl overflow-hidden">
                        <div className="bg-slate-900/40 px-6 py-4 border-b border-slate-850">
                          <h4 className="text-slate-200 font-bold text-xs">Full Revision History</h4>
                        </div>
                        <div className="divide-y divide-slate-850">
                          {versions.map(v => (
                            <div key={v.id} className="p-4 flex justify-between items-center text-xs hover:bg-slate-900/25 transition-colors">
                              <div>
                                <span className="font-bold text-emerald-400">v{v.versionNumber}</span>
                                <span className="text-slate-400 ml-2">{v.comment || 'Draft update'}</span>
                              </div>
                              <div className="flex items-center gap-4 text-slate-500">
                                <span>By: {v.createdBy}</span>
                                <span>{new Date(v.createdAt).toLocaleString()}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </motion.div>
                  ) : (
                    <div className="text-center py-16 text-slate-500">
                      No version history found. Initialize the workspace to create versions.
                    </div>
                  )}
                </div>
              )}

              {/* Collaboration / Team / Export tab */}
              {activeTab === 'collab' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Team invitation card */}
                  <div className="bg-slate-900/40 border border-slate-850 rounded-2xl p-6 flex flex-col justify-between">
                    <div>
                      <h4 className="text-slate-200 font-bold text-sm flex items-center gap-2">
                        <Users className="w-5 h-5 text-emerald-400" />
                        Workspace Team & Permissions
                      </h4>
                      <p className="text-slate-400 text-xs mt-1 leading-relaxed">
                        Invite users to collaborate on this proposal document. Assigned roles determine editing privileges and audit logging.
                      </p>

                      <form onSubmit={handleInvite} className="space-y-4 mt-6">
                        <div>
                          <label className="block text-[10px] uppercase font-bold tracking-wider text-slate-500 mb-1.5">Email Address</label>
                          <input
                            type="email"
                            required
                            placeholder="collaborator@company.com"
                            value={inviteEmail}
                            onChange={(e) => setInviteEmail(e.target.value)}
                            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-250 focus:outline-none focus:border-emerald-500"
                          />
                        </div>

                        <div>
                          <label className="block text-[10px] uppercase font-bold tracking-wider text-slate-500 mb-1.5">Collaboration Role</label>
                          <select
                            value={inviteRole}
                            onChange={(e) => setInviteRole(e.target.value)}
                            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-250 focus:outline-none focus:border-emerald-500"
                          >
                            <option value="Admin">Admin</option>
                            <option value="Editor">Editor</option>
                            <option value="Viewer">Viewer</option>
                            <option value="ComplianceOfficer">Compliance Officer</option>
                          </select>
                        </div>

                        <button
                          type="submit"
                          disabled={isActionRunning}
                          className="w-full py-3 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-450 border border-emerald-500/20 font-bold text-xs transition-colors flex items-center justify-center gap-2"
                        >
                          {isActionRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
                          Send Collaboration Invite
                        </button>
                      </form>

                      {inviteMsg && (
                        <p className="text-center text-xs text-emerald-400 font-medium mt-3">
                          {inviteMsg}
                        </p>
                      )}
                    </div>

                    {/* Members List */}
                    {workspace && workspace.members && (
                      <div className="border-t border-slate-850 mt-6 pt-4 space-y-2">
                        <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Active Members</span>
                        <div className="space-y-1.5">
                          {workspace.members.map((m: any, i: number) => (
                            <div key={i} className="flex justify-between items-center text-xs">
                              <span className="text-slate-350">{m.userId}</span>
                              <span className="bg-slate-800 border border-slate-700/50 text-slate-400 text-[10px] font-semibold px-2 py-0.5 rounded-md">
                                {m.role}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Document Generation / Export card */}
                  <div className="bg-slate-900/40 border border-slate-850 rounded-2xl p-6 flex flex-col justify-between">
                    <div>
                      <h4 className="text-slate-200 font-bold text-sm flex items-center gap-2">
                        <Download className="w-5 h-5 text-emerald-400" />
                        Proposal Response Exporter
                      </h4>
                      <p className="text-slate-400 text-xs mt-1 leading-relaxed">
                        Convert and package the latest editor draft into standard corporate procurement formats for final submission.
                      </p>

                      <div className="grid grid-cols-2 gap-4 mt-8">
                        <button
                          onClick={() => handleExport('pdf')}
                          disabled={isActionRunning}
                          className="p-6 rounded-2xl bg-rose-500/5 hover:bg-rose-500/10 text-rose-300 border border-rose-500/20 flex flex-col items-center gap-3 transition-colors"
                        >
                          <FileText className="w-8 h-8 text-rose-400" />
                          <span className="text-xs font-bold">Export Adobe PDF</span>
                        </button>

                        <button
                          onClick={() => handleExport('docx')}
                          disabled={isActionRunning}
                          className="p-6 rounded-2xl bg-blue-500/5 hover:bg-blue-500/10 text-blue-305 border border-blue-500/20 flex flex-col items-center gap-3 transition-colors"
                        >
                          <FileText className="w-8 h-8 text-blue-400" />
                          <span className="text-xs font-bold">Export MS Word (DOCX)</span>
                        </button>
                      </div>
                    </div>

                    <div className="text-[10px] text-slate-500 mt-6 border-t border-slate-850 pt-4 flex items-center gap-2 leading-relaxed">
                      <AlertCircle className="w-4 h-4 flex-shrink-0" />
                      <span>Exporting will automatically compile the latest version to Azure blob storage and provide a download link.</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </>
    ) : (
      <WinProbabilityDashboard />
    )}
      </div>
    </div>
  );
}