import React, { useRef, useState } from 'react';

const FileUpload = ({ 
  selectedFiles, 
  onFilesSelected, 
  onFileRemoved, 
  onProcess, 
  isProcessing,
  isUploading,
  error 
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    onFilesSelected(droppedFiles);
  };

  const handleFileSelect = (e) => {
    const selectedFileList = Array.from(e.target.files);
    onFilesSelected(selectedFileList);
    // Reset input so same file can be selected again
    e.target.value = '';
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="file-upload-container">
      <div className="upload-section">
        <h2>Upload PDF Files</h2>
        <p className="subtitle">Upload production data PDFs for extraction</p>

        {/* Drag and Drop Zone */}
        <div
          className={`drag-drop-zone ${isDragging ? 'dragging' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleClick}
          role="button"
          tabIndex="0"
          aria-label="Drag and drop PDF files or click to select"
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              handleClick();
            }
          }}
        >
          <div className="drag-drop-content">
            <svg className="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <h3>Drag and drop your PDFs here</h3>
            <p>or click to select files</p>
            <p className="file-info">Supported: PDF files (Max 50 MB each)</p>
          </div>
        </div>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,application/pdf"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
          aria-hidden="true"
          disabled={isProcessing}
        />

        {/* Selected Files List */}
        {selectedFiles.length > 0 && (
          <div className="selected-files">
            <h4>Selected Files ({selectedFiles.length}):</h4>
            <ul className="file-list">
              {selectedFiles.map((file, index) => (
                <li key={`${file.name}-${index}`} className="file-item">
                  <div className="file-info-container">
                    <span className="file-icon">📄</span>
                    <div className="file-details">
                      <span className="file-name">{file.name}</span>
                      <span className="file-size">{formatFileSize(file.size)}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => onFileRemoved(file)}
                    className="remove-btn"
                    aria-label={`Remove ${file.name}`}
                    disabled={isProcessing}
                  >
                    ✕
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Process Button */}
        <div className="button-container">
          <button
            onClick={onProcess}
            disabled={selectedFiles.length === 0 || isProcessing || isUploading}
            className="process-btn primary-btn"
            aria-busy={isProcessing || isUploading}
          >
            {isProcessing || isUploading ? (
              <>
                <span className="spinner"></span>
                Processing...
              </>
            ) : (
              `Process ${selectedFiles.length} File${selectedFiles.length !== 1 ? 's' : ''}`
            )}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="error-message" role="alert">
            <span className="error-icon">⚠️</span>
            <span>{error}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUpload;
