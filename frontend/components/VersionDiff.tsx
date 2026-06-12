'use client';

import React, { useMemo } from 'react';
import { Plus, Minus, FileText, ArrowRight } from 'lucide-react';

interface VersionDiffProps {
  oldContentJson: string;
  newContentJson: string;
  oldVersionLabel: string;
  newVersionLabel: string;
}

interface DiffLine {
  type: 'added' | 'removed' | 'unchanged';
  value: string;
}

// Convert Slate JSON to plain text lines
function slateJsonToText(jsonStr: string): string {
  try {
    if (!jsonStr) return '';
    const parsed = JSON.parse(jsonStr);
    if (Array.isArray(parsed)) {
      return parsed.map((node: any) => {
        if (node.text) return node.text;
        if (node.children && Array.isArray(node.children)) {
          return node.children.map((child: any) => child.text || '').join('');
        }
        return '';
      }).join('\n');
    }
  } catch (e) {
    // If it's not JSON, treat it as plain text
  }
  return jsonStr;
}

// Simple line-level LCS diff algorithm
function computeLineDiff(oldText: string, newText: string): DiffLine[] {
  const oldLines = oldText.split('\n');
  const newLines = newText.split('\n');
  
  const m = oldLines.length;
  const n = newLines.length;
  
  // DP matrix for Longest Common Subsequence
  const dp: number[][] = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));
  
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (oldLines[i - 1] === newLines[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }
  
  const diffResult: DiffLine[] = [];
  let i = m, j = n;
  
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && oldLines[i - 1] === newLines[j - 1]) {
      diffResult.unshift({ type: 'unchanged', value: oldLines[i - 1] });
      i--;
      j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      diffResult.unshift({ type: 'added', value: newLines[j - 1] });
      j--;
    } else {
      diffResult.unshift({ type: 'removed', value: oldLines[i - 1] });
      i--;
    }
  }
  
  return diffResult;
}

export default function VersionDiff({
  oldContentJson,
  newContentJson,
  oldVersionLabel,
  newVersionLabel
}: VersionDiffProps) {
  const oldText = useMemo(() => slateJsonToText(oldContentJson), [oldContentJson]);
  const newText = useMemo(() => slateJsonToText(newContentJson), [newContentJson]);
  const diffLines = useMemo(() => computeLineDiff(oldText, newText), [oldText, newText]);

  // Count additions and deletions
  const stats = useMemo(() => {
    let added = 0;
    let removed = 0;
    diffLines.forEach(line => {
      if (line.type === 'added') added++;
      if (line.type === 'removed') removed++;
    });
    return { added, removed };
  }, [diffLines]);

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl overflow-hidden shadow-2xl">
      {/* Diff Header */}
      <div className="bg-slate-900 px-6 py-4 flex flex-col md:flex-row justify-between md:items-center gap-4 border-b border-slate-850">
        <div>
          <h3 className="text-slate-200 font-bold text-sm flex items-center gap-2">
            <FileText className="w-4 h-4 text-emerald-400" />
            Workspace Version Comparison
          </h3>
          <p className="text-slate-400 text-xs mt-0.5 flex items-center gap-1.5">
            <span>Comparing version {oldVersionLabel}</span>
            <ArrowRight className="w-3.5 h-3.5" />
            <span>version {newVersionLabel}</span>
          </p>
        </div>

        {/* Change Stats */}
        <div className="flex gap-3 text-xs">
          <div className="bg-rose-500/10 text-rose-400 px-3 py-1.5 rounded-lg border border-rose-500/20 flex items-center gap-1">
            <Minus className="w-3.5 h-3.5" />
            <span className="font-bold">{stats.removed}</span> deletions
          </div>
          <div className="bg-emerald-500/10 text-emerald-400 px-3 py-1.5 rounded-lg border border-emerald-500/20 flex items-center gap-1">
            <Plus className="w-3.5 h-3.5" />
            <span className="font-bold">{stats.added}</span> additions
          </div>
        </div>
      </div>

      {/* Diff Code Container */}
      <div className="p-4 bg-slate-950 overflow-x-auto max-h-[500px] scrollbar-thin scrollbar-thumb-slate-800">
        <div className="font-mono text-xs space-y-1.5 min-w-[600px]">
          {diffLines.map((line, idx) => {
            const isAdded = line.type === 'added';
            const isRemoved = line.type === 'removed';
            
            let bgClass = 'text-slate-400 hover:bg-slate-900/40';
            let icon = <span className="w-4 inline-block" />;
            
            if (isAdded) {
              bgClass = 'bg-emerald-950/20 text-emerald-300 border-l-2 border-emerald-500 px-2 py-0.5 hover:bg-emerald-950/30';
              icon = <Plus className="w-3.5 h-3.5 text-emerald-400 mr-1 inline" />;
            } else if (isRemoved) {
              bgClass = 'bg-rose-950/20 text-rose-400 border-l-2 border-rose-500 px-2 py-0.5 line-through hover:bg-rose-950/30';
              icon = <Minus className="w-3.5 h-3.5 text-rose-400 mr-1 inline" />;
            } else {
              bgClass = 'text-slate-300 px-2 py-0.5 hover:bg-slate-900/40';
            }

            return (
              <div 
                key={idx} 
                className={`flex items-start rounded transition-all duration-200 ${bgClass}`}
              >
                {/* Line number */}
                <span className="w-8 text-right pr-3 text-slate-600 select-none font-medium">
                  {idx + 1}
                </span>
                
                {/* Line content */}
                <span className="flex-1 whitespace-pre-wrap leading-relaxed">
                  {icon}
                  {line.value || ' '}
                </span>
              </div>
            );
          })}
          
          {diffLines.length === 0 && (
            <div className="text-center py-8 text-slate-500">
              No differences found between these versions.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
