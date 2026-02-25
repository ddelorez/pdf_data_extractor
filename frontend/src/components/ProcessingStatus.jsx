import React, { useEffect } from 'react';

const ProcessingStatus = ({ 
  jobId, 
  status, 
  progress, 
  isPolling, 
  onStart, 
  onCancel,
  pollingError 
}) => {
  useEffect(() => {
    if (jobId && !isPolling) {
      onStart();
    }
  }, [jobId, isPolling, onStart]);

  if (!jobId) {
    return null;
  }

  const getStatusMessage = () => {
    if (!status) return 'Initializing...';
    
    const messages = {
      'pending': 'Waiting to process...',
      'uploading': 'Uploading files...',
      'processing': status?.message || 'Processing files...',
      'completed': 'Processing completed!',
      'failed': 'Processing failed',
      'error': 'An error occurred',
      'cancelled': 'Processing cancelled'
    };

    return messages[status?.status] || 'Processing...';
  };

  const getStatusColor = () => {
    if (!status) return '#666';
    
    const colors = {
      'pending': '#FF6600',
      'uploading': '#FF6600',
      'processing': '#0066CC',
      'completed': '#4CAF50',
      'failed': '#F44336',
      'error': '#F44336',
      'cancelled': '#999'
    };

    return colors[status?.status] || '#666';
  };

  const isCompleted = status?.status === 'completed';
  const isFailed = status?.status === 'failed' || status?.status === 'error';
  const isProcessing = isPolling && !isCompleted && !isFailed;

  return (
    <div className="processing-status-container">
      <div className="status-card">
        <div className="status-header">
          <h2>Processing Status</h2>
          <div className="job-id">Job ID: <code>{jobId}</code></div>
        </div>

        {/* Status Message */}
        <div className="status-message" style={{ color: getStatusColor() }}>
          {isProcessing && <span className="spinner"></span>}
          <span>{getStatusMessage()}</span>
        </div>

        {/* Progress Bar */}
        <div className="progress-section">
          <div className="progress-bar-container">
            <div
              className="progress-bar-fill"
              style={{
                width: `${progress}%`,
                backgroundColor: getStatusColor()
              }}
            ></div>
          </div>
          <div className="progress-text">
            <span>{progress}% Complete</span>
          </div>
        </div>

        {/* Status Details */}
        {status && (
          <div className="status-details">
            {status.records !== undefined && (
              <div className="detail-row">
                <span className="detail-label">Records Processed:</span>
                <span className="detail-value">{status.records}</span>
              </div>
            )}
            {status.wells !== undefined && (
              <div className="detail-row">
                <span className="detail-label">Wells Found:</span>
                <span className="detail-value">{status.wells}</span>
              </div>
            )}
            {status.message && (
              <div className="detail-row full-width">
                <span className="detail-label">Details:</span>
                <span className="detail-value">{status.message}</span>
              </div>
            )}
          </div>
        )}

        {/* Error Message */}
        {pollingError && (
          <div className="polling-error" role="alert">
            <span className="error-icon">⚠️</span>
            <span>{pollingError}</span>
          </div>
        )}

        {/* Action Buttons */}
        <div className="status-actions">
          {isProcessing && (
            <button
              onClick={onCancel}
              className="cancel-btn secondary-btn"
              aria-label="Cancel processing"
            >
              Cancel Processing
            </button>
          )}
          {isCompleted && (
            <div className="completion-badge">
              <span className="success-icon">✓</span>
              <span>Processing completed successfully</span>
            </div>
          )}
          {isFailed && (
            <div className="failure-badge">
              <span className="error-icon">✕</span>
              <span>Processing failed - Please check the error details</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProcessingStatus;
