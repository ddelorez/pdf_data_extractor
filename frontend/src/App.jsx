import { useState, useEffect } from 'react';
import FileUpload from './components/FileUpload';
import ProcessingStatus from './components/ProcessingStatus';
import ResultsViewer from './components/ResultsViewer';
import ErrorNotification from './components/ErrorNotification';
import { useFileUpload } from './hooks/useFileUpload';
import { usePolling } from './hooks/usePolling';
import { processJob, healthCheck } from './services/api';

const App = () => {
  const [appState, setAppState] = useState('idle'); // idle, uploading, processing, complete, error
  const [jobId, setJobId] = useState(null);
  const [results, setResults] = useState(null);
  const [appError, setAppError] = useState(null);
  const [backendHealthy, setBackendHealthy] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);

  const fileUpload = useFileUpload();
  const polling = usePolling(jobId, 2000);

  // Health check on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await healthCheck();
        setBackendHealthy(true);
      } catch (error) {
        setAppError({
          message: 'Backend service is not available. Please ensure the Flask server is running.',
          details: error.message,
          retryable: true
        });
        setBackendHealthy(false);
      } finally {
        setIsInitializing(false);
      }
    };

    checkHealth();
  }, []);

  const handleFilesSelected = async (files) => {
    if (!fileUpload.addFiles(files)) {
      // Error already set by addFiles
      setAppError({
        message: fileUpload.error,
        retryable: true
      });
    }
  };

  const handleProcess = async () => {
    setAppError(null);
    setAppState('uploading');

    try {
      // Upload files
      const uploadResult = await fileUpload.upload();
      
      if (!uploadResult || !uploadResult.job_id) {
        throw new Error('Upload failed: No job ID received');
      }

      setJobId(uploadResult.job_id);
      setAppState('processing');

      // Start polling immediately
      setTimeout(() => {
        polling.startPolling();
      }, 100);

    } catch (error) {
      setAppError({
        message: error.message || 'Upload failed',
        retryable: true
      });
      setAppState('error');
    }
  };

  // Handle polling completion
  useEffect(() => {
    if (polling.status?.status === 'completed') {
      setAppState('complete');
      setResults(polling.status);
    } else if (polling.status?.status === 'failed' || polling.status?.status === 'error') {
      setAppError({
        message: polling.status?.message || 'Processing failed',
        retryable: true
      });
      setAppState('error');
    }
  }, [polling.status]);

  const handleProcessMore = () => {
    setAppState('idle');
    setJobId(null);
    setResults(null);
    fileUpload.clearFiles();
    polling.stopPolling();
  };

  const handleErrorDismiss = () => {
    if (appState === 'error') {
      setAppState('idle');
    }
    setAppError(null);
  };

  const handleErrorRetry = () => {
    if (appState === 'error' && jobId) {
      // If error during processing, retry polling
      setAppError(null);
      setAppState('processing');
      polling.startPolling();
    } else if (appState === 'error') {
      // If upload error, allow retry
      handleErrorDismiss();
    }
  };

  // Check health periodically
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        await healthCheck();
        if (!backendHealthy) {
          setBackendHealthy(true);
          if (appError?.message?.includes('not available')) {
            setAppError(null);
          }
        }
      } catch (error) {
        if (backendHealthy) {
          setBackendHealthy(false);
          setAppError({
            message: 'Backend service connection lost',
            details: error.message,
            retryable: true
          });
        }
      }
    }, 10000); // Check every 10 seconds

    return () => clearInterval(interval);
  }, [backendHealthy, appError]);

  if (isInitializing) {
    return (
      <div className="app-container initializing">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Connecting to service...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <h1>PDF Production Data Extractor</h1>
          <p className="tagline">Professional extraction tool for oil and gas production data</p>
          <div className="health-indicator">
            <span className={`status-dot ${backendHealthy ? 'healthy' : 'unhealthy'}`}></span>
            <span className="status-text">
              {backendHealthy ? 'Service Connected' : 'Service Unavailable'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="app-main">
        <div className="content-container">
          {/* Error Notification */}
          {appError && (
            <ErrorNotification
              error={appError}
              onDismiss={handleErrorDismiss}
              onRetry={handleErrorRetry}
            />
          )}

          {/* Dispatch to appropriate component based on state */}
          {appState === 'idle' && (
            <FileUpload
              selectedFiles={fileUpload.selectedFiles}
              onFilesSelected={handleFilesSelected}
              onFileRemoved={fileUpload.removeFile}
              onProcess={handleProcess}
              isProcessing={appState === 'processing'}
              isUploading={fileUpload.isUploading}
              error={fileUpload.error}
            />
          )}

          {(appState === 'uploading' || appState === 'processing') && (
            <>
              <ProcessingStatus
                jobId={jobId}
                status={polling.status}
                progress={polling.progress}
                isPolling={polling.isPolling}
                onStart={polling.startPolling}
                onCancel={polling.stopPolling}
                pollingError={polling.error}
              />
            </>
          )}

          {appState === 'complete' && (
            <ResultsViewer
              jobId={jobId}
              results={results}
              onProcessMore={handleProcessMore}
            />
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div className="footer-content">
          <p>PDF Production Data Extractor v2.0.0</p>
          <p className="footer-note">
            For technical support, please contact the development team
          </p>
        </div>
      </footer>
    </div>
  );
};

export default App;
