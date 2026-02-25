import React, { useState } from 'react';

const ErrorNotification = ({ 
  error, 
  onDismiss, 
  onRetry,
  isExpanded: initialExpanded = false 
}) => {
  const [isExpanded, setIsExpanded] = useState(initialExpanded);

  if (!error) {
    return null;
  }

  // Parse error message to extract main message and details
  const errorMessage = typeof error === 'string' ? error : error.message || 'An unexpected error occurred';
  const errorDetails = error.details || error.stack || null;
  const isRetryable = error.retryable !== false; // Default to retryable

  const handleToggleDetails = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <div className="error-notification" role="alert" aria-live="assertive">
      <div className="error-content">
        <div className="error-header">
          <span className="error-icon">❌</span>
          <div className="error-message-section">
            <h3 className="error-title">Error</h3>
            <p className="error-message">{errorMessage}</p>
          </div>
          <button
            onClick={onDismiss}
            className="error-close-btn"
            aria-label="Dismiss error"
          >
            ✕
          </button>
        </div>

        {/* Expandable Details */}
        {errorDetails && (
          <div className="error-details-section">
            <button
              onClick={handleToggleDetails}
              className="details-toggle"
              aria-expanded={isExpanded}
            >
              <span className="toggle-icon">{isExpanded ? '▼' : '▶'}</span>
              <span className="toggle-text">
                {isExpanded ? `Hide Details` : `Show Details`}
              </span>
            </button>

            {isExpanded && (
              <div className="error-details">
                <pre className="details-content">{errorDetails}</pre>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="error-actions">
          {isRetryable && onRetry && (
            <button
              onClick={onRetry}
              className="retry-btn secondary-btn"
              aria-label="Retry the operation"
            >
              Try Again
            </button>
          )}
          <button
            onClick={onDismiss}
            className="dismiss-btn secondary-btn"
            aria-label="Dismiss the error notification"
          >
            Dismiss
          </button>
        </div>

        {/* Support Information */}
        <div className="error-support">
          <small>
            If this error persists, please contact support or check the{' '}
            <a href="#" onClick={(e) => { e.preventDefault(); }}>
              documentation
            </a>
          </small>
        </div>
      </div>
    </div>
  );
};

export default ErrorNotification;
