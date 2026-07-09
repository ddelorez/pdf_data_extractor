import { useState, useCallback } from 'react';
import { uploadFiles as uploadFilesAPI } from '../services/api';

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50 MB per file
const MAX_TOTAL_SIZE = 100 * 1024 * 1024; // 100 MB aggregate (matches backend MAX_CONTENT_LENGTH)
// PDFs feed the extraction pipeline; .xlsx workbooks feed the DPR Excel->Excel
// pipeline. The backend validates real content by magic bytes; this is UX only.
const ALLOWED_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
];
const ALLOWED_EXTENSIONS = ['.pdf', '.xlsx'];

// Browsers often report an empty MIME type for .xlsx (especially via drag-drop),
// so accept a file if EITHER its extension or its MIME type is recognised.
const isAllowedFile = (file) => {
  const name = (file.name || '').toLowerCase();
  const byExtension = ALLOWED_EXTENSIONS.some((ext) => name.endsWith(ext));
  return byExtension || ALLOWED_TYPES.includes(file.type);
};

export const useFileUpload = () => {
  const [files, setFiles] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);

  const validateFiles = useCallback((filesToValidate) => {
    const errors = [];
    // Start from the already-pending selection so the aggregate check accounts
    // for everything that will be uploaded together (RECOMMENDATIONS E4).
    let runningTotal = selectedFiles.reduce((sum, f) => sum + f.size, 0);

    filesToValidate.forEach((file) => {
      // Check file type
      if (!isAllowedFile(file)) {
        errors.push(`${file.name}: Not a PDF or Excel (.xlsx) file`);
      }

      // Check file size
      if (file.size > MAX_FILE_SIZE) {
        errors.push(`${file.name}: File size exceeds 50 MB limit`);
      }

      // Check for duplicates against the pending selection, not post-upload
      // files (which is empty until an upload completes) (RECOMMENDATIONS E2).
      if (selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
        errors.push(`${file.name}: Already selected`);
      }

      runningTotal += file.size;
    });

    // Aggregate size check across the whole pending batch (RECOMMENDATIONS E4).
    if (runningTotal > MAX_TOTAL_SIZE) {
      errors.push('Total upload size exceeds 100 MB limit');
    }

    return errors;
  }, [selectedFiles]);

  const addFiles = useCallback((filesToAdd) => {
    const errors = validateFiles(filesToAdd);
    
    if (errors.length > 0) {
      setError(errors.join('\n'));
      return false;
    }

    setSelectedFiles(prev => [...prev, ...filesToAdd]);
    setError(null);
    return true;
  }, [validateFiles]);

  const removeFile = useCallback((fileToRemove) => {
    setSelectedFiles(prev =>
      prev.filter(f => f !== fileToRemove)
    );
  }, []);

  const clearFiles = useCallback(() => {
    setSelectedFiles([]);
    setError(null);
  }, []);

  const upload = useCallback(async () => {
    if (selectedFiles.length === 0) {
      setError('No files selected');
      return null;
    }

    setIsUploading(true);
    setError(null);

    try {
      const result = await uploadFilesAPI(selectedFiles);
      setFiles(selectedFiles);
      setSelectedFiles([]);
      return result;
    } catch (err) {
      setError(err.message || 'Upload failed');
      return null;
    } finally {
      setIsUploading(false);
    }
  }, [selectedFiles]);

  return {
    files,
    selectedFiles,
    setSelectedFiles,
    addFiles,
    removeFile,
    clearFiles,
    upload,
    isUploading,
    error,
    setError,
  };
};
