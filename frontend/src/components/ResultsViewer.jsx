import React, { useState } from 'react';
import { downloadExcel, downloadCsv } from '../services/api';

const ResultsViewer = ({ jobId, results, onProcessMore }) => {
  const [downloading, setDownloading] = useState(null);
  const [downloadError, setDownloadError] = useState(null);

  if (!results || !jobId) {
    return null;
  }

  const handleDownload = async (format) => {
    setDownloading(format);
    setDownloadError(null);

    try {
      const downloadFn = format === 'excel' ? downloadExcel : downloadCsv;
      const blob = await downloadFn(jobId);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `production-data.${format === 'excel' ? 'xlsx' : 'csv'}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      setDownloadError(`Failed to download ${format}: ${error.message}`);
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="results-viewer-container">
      <div className="results-card">
        <div className="results-header">
          <h2>Processing Complete</h2>
          <div className="success-badge">
            <span className="badge-icon">✓</span>
            <span>Successfully Processed</span>
          </div>
        </div>

        {/* Summary Statistics */}
        <div className="results-summary">
          <div className="summary-stat">
            <span className="stat-label">Total Records</span>
            <span className="stat-value">{results.records || 0}</span>
          </div>
          <div className="summary-stat">
            <span className="stat-label">Wells Found</span>
            <span className="stat-value">{results.wells || 0}</span>
          </div>
          {results.date_range && (
            <div className="summary-stat">
              <span className="stat-label">Date Range</span>
              <span className="stat-value">{results.date_range}</span>
            </div>
          )}
          {results.processing_time && (
            <div className="summary-stat">
              <span className="stat-label">Processing Time</span>
              <span className="stat-value">{results.processing_time}</span>
            </div>
          )}
        </div>

        {/* Results Details */}
        {results.details && (
          <div className="results-details">
            <h3>Processing Details</h3>
            <div className="details-content">
              {Array.isArray(results.details) ? (
                <ul className="details-list">
                  {results.details.map((detail, index) => (
                    <li key={index} className="detail-item">
                      {detail}
                    </li>
                  ))}
                </ul>
              ) : (
                <p>{results.details}</p>
              )}
            </div>
          </div>
        )}

        {/* Download Buttons */}
        <div className="download-section">
          <h3>Download Results</h3>
          <div className="download-buttons">
            <button
              onClick={() => handleDownload('excel')}
              disabled={downloading !== null}
              className="download-btn primary-btn excel-btn"
              aria-busy={downloading === 'excel'}
            >
              {downloading === 'excel' ? (
                <>
                  <span className="spinner"></span>
                  Downloading...
                </>
              ) : (
                <>
                  <span className="file-icon">📊</span>
                  Download Excel
                </>
              )}
            </button>
            <button
              onClick={() => handleDownload('csv')}
              disabled={downloading !== null}
              className="download-btn secondary-btn csv-btn"
              aria-busy={downloading === 'csv'}
            >
              {downloading === 'csv' ? (
                <>
                  <span className="spinner"></span>
                  Downloading...
                </>
              ) : (
                <>
                  <span className="file-icon">📋</span>
                  Download CSV
                </>
              )}
            </button>
          </div>

          {downloadError && (
            <div className="download-error" role="alert">
              <span className="error-icon">⚠️</span>
              <span>{downloadError}</span>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="results-actions">
          <button
            onClick={onProcessMore}
            className="process-more-btn primary-btn"
          >
            Process More Files
          </button>
        </div>

        {/* Job Info */}
        <div className="job-info">
          <small>Job ID: <code>{jobId}</code></small>
        </div>
      </div>
    </div>
  );
};

export default ResultsViewer;
