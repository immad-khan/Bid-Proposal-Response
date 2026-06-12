/**
 * useApi — Custom React hook for API calls with loading/error state management.
 * Wraps the apiClient for use in React components with proper lifecycle handling.
 */

'use client';

import { useState, useCallback } from 'react';
import { apiClient } from '../services/apiClient';

// ── Generic async request hook ──
export function useApiRequest<T>() {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async (apiCall: () => Promise<T>) => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiCall();
      setData(result);
      return result;
    } catch (err: any) {
      const message = err?.message || 'An unexpected error occurred.';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, execute, setData };
}

// ── Typed hooks for specific API operations ──

export function useRFPUpload() {
  const { data, loading, error, execute } = useApiRequest<{
    jobId: string;
    blobUrl: string;
    filename: string;
  }>();

  const upload = useCallback(
    (file: File) => execute(() => apiClient.uploadRfp(file)),
    [execute]
  );

  return { upload, data, loading, error };
}

export function useProjects() {
  const { data, loading, error, execute, setData } = useApiRequest<any[]>();

  const fetchProjects = useCallback(
    () => execute(() => apiClient.getProjects()),
    [execute]
  );

  return { projects: data || [], fetchProjects, loading, error, setData };
}

export function useGoNoGo() {
  const { data, loading, error, execute } = useApiRequest<{
    decision: string;
    win_probability: number;
    feature_impacts: Array<{
      feature: string;
      value: number;
      impact: number;
      direction: string;
    }>;
  }>();

  const evaluate = useCallback(
    (features: Record<string, number>) =>
      execute(() => apiClient.evaluateGoNoGo(features)),
    [execute]
  );

  return { result: data, evaluate, loading, error };
}

export function useProposalGeneration() {
  const { data, loading, error, execute } = useApiRequest<{
    status: string;
    drafts: Record<string, string>;
    reviews: any[];
    approved: boolean;
  }>();

  const generate = useCallback(
    (projectId: string, rfpText: string) =>
      execute(() => apiClient.generateProposal(projectId, rfpText)),
    [execute]
  );

  return { result: data, generate, loading, error };
}

export function useHealthCheck() {
  const { data, loading, error, execute } = useApiRequest<{
    service: string;
    status: string;
  }>();

  const check = useCallback(
    () => execute(() => apiClient.healthCheck()),
    [execute]
  );

  return { health: data, check, loading, error };
}
