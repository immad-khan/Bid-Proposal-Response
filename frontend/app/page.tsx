'use client';
import { useState } from 'react';
import Image from "next/image";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>('');

  const handleUpload = async () => {
    if (!file) {
      setStatus('Please select a file first.');
      return;
    }
    setStatus('Uploading to .NET API...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Pointing directly to your active .NET backend port 5282
      const response = await fetch('http://localhost:5282/api/RfpUpload/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Server Response:", data);
      setStatus(`Handshake Success! Job ID: ${data.jobId}`);
    } catch (error) {
      console.error("Upload Error:", error);
      setStatus('Upload failed. Check your browser console or backend terminal.');
    }
  };

  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black min-h-screen">
      <main className="flex flex-col w-full max-w-xl items-center justify-center p-8 bg-white dark:bg-zinc-900 rounded-xl shadow-md gap-6 border border-zinc-200 dark:border-zinc-800">
        <Image
          className="dark:invert"
          src="/next.svg"
          alt="Next.js logo"
          width={100}
          height={20}
          priority
        />
        
        <div className="text-center">
          <h1 className="text-2xl font-bold text-black dark:text-zinc-50">
            RFP Proposal Workspace
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            Phase 1: Connectivity Handshake
          </p>
        </div>

        <div className="w-full flex flex-col gap-4 items-center border-2 border-dashed border-zinc-300 dark:border-zinc-700 rounded-lg p-6 bg-zinc-50 dark:bg-zinc-800/50">
          <input 
            type="file" 
            accept=".pdf,.docx"
            className="block w-full text-sm text-zinc-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-zinc-900 file:text-white hover:file:bg-zinc-800 dark:file:bg-zinc-100 dark:file:text-black cursor-pointer"
            onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)} 
          />
        </div>

        <button 
          onClick={handleUpload}
          className="w-full h-12 flex items-center justify-center rounded-full bg-foreground text-background font-medium transition-colors hover:bg-[#383838] dark:hover:bg-[#ccc]"
        >
          Send to Backend Engine
        </button>

        {status && (
          <div className="w-full text-center p-3 rounded bg-zinc-100 dark:bg-zinc-800 text-sm font-mono break-all text-zinc-800 dark:text-zinc-200">
            {status}
          </div>
        )}
      </main>
    </div>
  );
}