import { useState, useCallback } from 'react';
import { uploadFiles as uploadFilesAPI } from '../services/api';

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50 MB
const ALLOWED_TYPES = ['application/pdf'];

export const useFileUpload = () => {
  const [files, setFiles] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);

  const validateFiles = useCallback((filesToValidate) => {
    const errors = [];
    
    filesToValidate.forEach((file) => {
      // Check file type
      if (!ALLOWED_TYPES.includes(file.type)) {
        errors.push(`${file.name}: Not a PDF file`);
      }
      
      // Check file size
      if (file.size > MAX_FILE_SIZE) {
        errors.push(`${file.name}: File size exceeds 50 MB limit`);
      }
      
      // Check for duplicates
      if (files.some(f => f.name === file.name && f.size === file.size)) {
        errors.push(`${file.name}: Already selected`);
      }
    });

    return errors;
  }, [files]);

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
