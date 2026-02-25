import { useState, useEffect, useCallback, useRef } from 'react';
import { getJobStatus } from '../services/api';

export const usePolling = (jobId, pollingInterval = 2000) => {
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState(null);
  const pollingTimeoutRef = useRef(null);

  const stopPolling = useCallback(() => {
    if (pollingTimeoutRef.current) {
      clearTimeout(pollingTimeoutRef.current);
      pollingTimeoutRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const pollStatus = useCallback(async () => {
    if (!jobId) return;

    try {
      setError(null);
      const data = await getJobStatus(jobId);
      
      setStatus(data);
      setProgress(data.progress || 0);

      // Stop polling if job is complete or failed
      if (data.status === 'completed' || data.status === 'failed' || data.status === 'error') {
        stopPolling();
      } else {
        // Schedule next poll
        pollingTimeoutRef.current = setTimeout(pollStatus, pollingInterval);
      }
    } catch (err) {
      setError(err.message || 'Status check failed');
      // Continue polling on error
      pollingTimeoutRef.current = setTimeout(pollStatus, pollingInterval);
    }
  }, [jobId, pollingInterval, stopPolling]);

  const startPolling = useCallback(() => {
    if (!jobId) return;
    setIsPolling(true);
    // Initial poll immediately
    pollStatus();
  }, [jobId, pollStatus]);

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      if (pollingTimeoutRef.current) {
        clearTimeout(pollingTimeoutRef.current);
      }
    };
  }, []);

  return {
    status,
    progress,
    isPolling,
    error,
    startPolling,
    stopPolling,
    pollStatus,
  };
};
