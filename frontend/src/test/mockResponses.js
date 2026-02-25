/**
 * Mock API responses for testing
 */

export const mockSuccessUpload = {
  job_id: 'test-job-123',
  status: 'uploaded',
  files_received: 1,
  message: 'Files uploaded successfully',
}

export const mockSuccessProcess = {
  status: 'success',
  records: 45,
  wells: ['HORIZON 10-01-15A', 'WILDCAT 05-12-18B'],
  excel_url: '/download/test-job-123/output.xlsx',
  csv_url: '/download/test-job-123/output.csv',
  message: 'Processing completed successfully',
}

export const mockJobStatus = {
  job_id: 'test-job-123',
  status: 'completed',
  progress: 100,
  records: 45,
  wells: ['HORIZON 10-01-15A', 'WILDCAT 05-12-18B'],
  message: 'Job completed',
}

export const mockJobStatusProcessing = {
  job_id: 'test-job-123',
  status: 'processing',
  progress: 50,
  records: null,
  wells: null,
  message: 'Job is being processed',
}

export const mockHealthCheck = {
  status: 'ok',
  version: '2.0.0',
  message: 'API is healthy',
}

export const mockErrorResponse = {
  error: 'Processing failed',
  message: 'Invalid PDF file format',
  job_id: 'test-job-123',
}

export const mockValidationError = {
  error: 'Validation failed',
  message: 'No valid production records found',
  job_id: 'test-job-123',
}

export const mockFileError = {
  error: 'File error',
  message: 'File is not a valid PDF',
  filename: 'test.txt',
}

export const mockNetworkError = new Error('Network request failed')
mockNetworkError.code = 'NETWORK_ERROR'

export const mockTimeoutError = new Error('Request timeout')
mockTimeoutError.code = 'TIMEOUT'

/**
 * Mock file for testing
 */
export const mockPdfFile = new File(
  ['dummy content'],
  'test.pdf',
  { type: 'application/pdf' }
)

export const mockInvalidFile = new File(
  ['dummy content'],
  'test.txt',
  { type: 'text/plain' }
)

/**
 * Mock dataset for component testing
 */
export const mockExtractedData = {
  wells: [
    {
      name: 'HORIZON 10-01-15A',
      records: 30,
      startDate: '2024-01-15',
      endDate: '2024-02-14',
    },
    {
      name: 'WILDCAT 05-12-18B',
      records: 15,
      startDate: '2024-01-15',
      endDate: '2024-01-29',
    },
  ],
  totalRecords: 45,
  validRecords: 45,
  invalidRecords: 0,
}

export const mockDownloadUrls = {
  excel: 'blob:http://localhost:3000/abc123',
  csv: 'blob:http://localhost:3000/def456',
}

/**
 * Create a mock Blob for file downloads
 */
export const createMockBlob = (content = 'test data', type = 'text/plain') => {
  return new Blob([content], { type })
}

/**
 * Create mock FormData
 */
export const createMockFormData = () => {
  const formData = new FormData()
  formData.append('files', mockPdfFile)
  return formData
}
