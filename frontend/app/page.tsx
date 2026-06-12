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
  Zap
} from 'lucide-react';

interface Project {
  id: string;
  name: string;
  rfpBlobUrl: string;
  createdAt: string;
  status: string;
}

// ─── Animation Variants ───
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.2 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { type: "spring", stiffness: 100, damping: 15 }
  }
};

const pulseRing = {
  scale: [1, 1.2, 1],
  opacity: [0.5, 0, 0.5],
  transition: { duration: 2, repeat: Infinity, ease: "easeInOut" }
};

import WinProbabilityDashboard from '../components/dashboard/WinProbabilityDashboard';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'upload' | 'dashboard'>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>('');
  const [statusType, setStatusType] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

  const fetchProjects = useCallback(async () => {
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
      const mockList: Project[] = [
        {
          id: 'proj-08f2372c-f6ef-46e3-a3d8',
          name: 'RFP-US-East-AWS-Cloud-Migration',
          rfpBlobUrl: 'https://mockstorage.blob.core.windows.net/rfp-uploads/AWS_Migration.pdf',
          createdAt: new Date().toISOString(),
          status: 'Created'
        },
        {
          id: 'proj-9a8b7c6d-5e4f-3a2b-1c0d',
          name: 'RFP-EU-West-Azure-DevOps-Setup',
          rfpBlobUrl: 'https://mockstorage.blob.core.windows.net/rfp-uploads/Azure_DevOps.pdf',
          createdAt: new Date(Date.now() - 86400000).toISOString(),
          status: 'Processing'
        }
      ];
      setProjects(mockList);
      setActiveProjectId(mockList[0].id);
    }
  }, [apiUrl, activeProjectId]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

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

    // Simulate progress for UX
    const progressInterval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) return prev;
        return prev + Math.random() * 15;
      });
    }, 300);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:5282/api/RfpUpload/upload', {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();
      setStatus(`Upload complete! Job ID: ${data.jobId}`);
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

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-zinc-100 font-sans selection:bg-cyan-500/30 overflow-x-hidden">
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
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <motion.div 
                className="absolute inset-0 rounded-xl bg-cyan-400/30"
                animate={pulseRing}
              />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-white to-zinc-400 bg-clip-text text-transparent">
                RFP Nexus
              </h1>
              <p className="text-xs text-zinc-500 flex items-center gap-1">
                <Server className="w-3 h-3" />
                Connected to .NET Backend
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center bg-zinc-900/80 border border-zinc-800 rounded-full p-1 backdrop-blur-sm">
              <button
                onClick={() => setActiveTab('upload')}
                className={`px-4 py-1.5 text-xs font-semibold rounded-full transition-all ${
                  activeTab === 'upload' ? 'bg-cyan-500/20 text-cyan-400' : 'text-zinc-500 hover:text-zinc-300'
                }`}
              >
                RFP Ingestion
              </button>
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`px-4 py-1.5 text-xs font-semibold rounded-full transition-all ${
                  activeTab === 'dashboard' ? 'bg-cyan-500/20 text-cyan-400' : 'text-zinc-500 hover:text-zinc-300'
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

        {activeTab === 'upload' ? (
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
                  <Zap className="w-3 h-3" />
                  Hackathon Mode
                </div>

                <h2 className="text-3xl lg:text-4xl font-bold mb-3 bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent">
                  Upload Your RFP
                </h2>
                <p className="text-zinc-400 text-sm lg:text-base max-w-md leading-relaxed">
                  Drop your proposal documents here to analyze, process, and generate intelligent responses powered by our .NET backend engine.
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
                        className="h-full bg-gradient-to-r from-cyan-500 to-blue-500"
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
                      : 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white hover:shadow-lg hover:shadow-cyan-500/25 hover:scale-[1.02] active:scale-[0.98]'
                  }
                `}
              >
                <span className="relative z-10 flex items-center justify-center gap-2">
                  {statusType === 'loading' ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      Send to Backend Engine
                    </>
                  )}
                </span>
                {file && statusType !== 'loading' && (
                  <motion.div
                    className="absolute inset-0 bg-gradient-to-r from-cyan-400/20 to-blue-400/20"
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
                  <h3 className="text-lg font-semibold text-zinc-200">Recent Projects</h3>
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
                      onClick={() => setActiveProjectId(project.id)}
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
                          className="absolute left-0 top-4 bottom-4 w-1 rounded-full bg-gradient-to-b from-cyan-500 to-blue-500"
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
                  <p className="text-sm text-zinc-500">No projects yet</p>
                </motion.div>
              )}

              {/* API Status Card */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
                className="rounded-2xl bg-zinc-900/40 border border-zinc-800/50 p-4 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-8 h-8 rounded-lg bg-zinc-800 flex items-center justify-center">
                    <Server className="w-4 h-4 text-zinc-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-zinc-300">Backend Status</p>
                    <p className="text-xs text-zinc-500">localhost:5282</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-zinc-400">API Endpoint Active</span>
                </div>
              </motion.div>
            </div>
          </motion.div>
          </div>
        ) : (
          <WinProbabilityDashboard />
        )}
      </div>
    </div>
  );
}