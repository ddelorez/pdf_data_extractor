import axios from 'axios';

// Configure API base URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
const DOWNLOAD_BASE_URL = import.meta.env.VITE_DOWNLOAD_BASE_URL || '/download';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.error || error.response.statusText || 'Server error occurred';
      throw new Error(message);
    } else if (error.request) {
      // Request made but no response
      throw new Error('No response from server. Check your connection.');
    } else {
      // Error in request setup
      throw new Error('Error: ' + error.message);
    }
  }
);

/**
 * Upload PDF files for extraction
 * @param {File[]} files - Array of PDF files
 * @returns {Promise<{job_id, status, files_received}>}
 */
export const uploadFiles = async (files) => {
  try {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    const response = await apiClient.post('/extract', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    throw new Error(`Upload failed: ${error.message}`);
  }
};

/**
 * Process a job
 * @param {string} jobId - Job ID to process
 * @returns {Promise<{status, records, wells, excel_url, csv_url}>}
 */
export const processJob = async (jobId) => {
  try {
    const response = await apiClient.post(`/process/${jobId}`);
    return response.data;
  } catch (error) {
    throw new Error(`Processing failed: ${error.message}`);
  }
};

/**
 * Get job status
 * @param {string} jobId - Job ID to check
 * @returns {Promise<{job_id, status, progress, records, wells, message}>}
 */
export const getJobStatus = async (jobId) => {
  try {
    const response = await apiClient.get(`/status/${jobId}`);
    return response.data;
  } catch (error) {
    throw new Error(`Status check failed: ${error.message}`);
  }
};

/**
 * Download Excel file
 * @param {string} jobId - Job ID
 * @returns {Promise<Blob>}
 */
export const downloadExcel = async (jobId) => {
  try {
    const response = await axios.get(
      `${DOWNLOAD_BASE_URL}/${jobId}/output.xlsx`,
      { responseType: 'blob' }
    );
    return response.data;
  } catch (error) {
    throw new Error(`Excel download failed: ${error.message}`);
  }
};

/**
 * Download CSV file
 * @param {string} jobId - Job ID
 * @returns {Promise<Blob>}
 */
export const downloadCsv = async (jobId) => {
  try {
    const response = await axios.get(
      `${DOWNLOAD_BASE_URL}/${jobId}/output.csv`,
      { responseType: 'blob' }
    );
    return response.data;
  } catch (error) {
    throw new Error(`CSV download failed: ${error.message}`);
  }
};

/**
 * Health check for backend
 * @returns {Promise<{status, version}>}
 */
export const healthCheck = async () => {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    throw new Error(`Health check failed: ${error.message}`);
  }
};

export default apiClient;
