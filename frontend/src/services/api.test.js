import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import axios from 'axios'
import * as api from './api'
import {
  mockSuccessUpload,
  mockSuccessProcess,
  mockJobStatus,
  mockHealthCheck,
  mockErrorResponse,
  mockPdfFile,
} from '../test/mockResponses'

// Mock axios - handles both create() for apiClient and direct get() calls
vi.mock('axios', () => {
  const mockGet = vi.fn()
  return {
    default: {
      create: vi.fn(),
      get: mockGet,
    },
  }
})

describe('API Service', () => {
  let mockClient

  beforeEach(() => {
    mockClient = {
      post: vi.fn(),
      get: vi.fn(),
      interceptors: {
        response: {
          use: vi.fn(),
        },
      },
    }
    axios.create.mockReturnValue(mockClient)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('uploadFiles', () => {
    it('should upload files successfully', async () => {
      mockClient.post.mockResolvedValue({ data: mockSuccessUpload })

      const files = [mockPdfFile]
      const result = await api.uploadFiles(files)

      expect(mockClient.post).toHaveBeenCalledWith(
        '/extract',
        expect.any(FormData),
        expect.any(Object)
      )
      expect(result).toEqual(mockSuccessUpload)
    })

    it('should throw error on upload failure', async () => {
      mockClient.post.mockRejectedValue(new Error('Upload failed'))

      const files = [mockPdfFile]
      await expect(api.uploadFiles(files)).rejects.toThrow('Upload failed')
    })

    it('should handle empty file list', async () => {
      mockClient.post.mockResolvedValue({ data: mockSuccessUpload })

      const files = []
      await api.uploadFiles(files)

      expect(mockClient.post).toHaveBeenCalled()
    })
  })

  describe('processJob', () => {
    it('should process job successfully', async () => {
      mockClient.post.mockResolvedValue({ data: mockSuccessProcess })

      const result = await api.processJob('test-job-123')

      expect(mockClient.post).toHaveBeenCalledWith('/process/test-job-123')
      expect(result).toEqual(mockSuccessProcess)
    })

    it('should throw error on process failure', async () => {
      mockClient.post.mockRejectedValue(new Error('Processing failed'))

      await expect(api.processJob('test-job-123')).rejects.toThrow()
    })

    it('should handle invalid job ID', async () => {
      mockClient.post.mockRejectedValue(new Error('Job not found'))

      await expect(api.processJob('invalid-id')).rejects.toThrow()
    })
  })

  describe('getJobStatus', () => {
    it('should get job status successfully', async () => {
      mockClient.get.mockResolvedValue({ data: mockJobStatus })

      const result = await api.getJobStatus('test-job-123')

      expect(mockClient.get).toHaveBeenCalledWith('/status/test-job-123')
      expect(result).toEqual(mockJobStatus)
    })

    it('should throw error on status check failure', async () => {
      mockClient.get.mockRejectedValue(new Error('Status check failed'))

      await expect(api.getJobStatus('test-job-123')).rejects.toThrow()
    })

    it('should return job with progress', async () => {
      mockClient.get.mockResolvedValue({ data: mockJobStatus })

      const result = await api.getJobStatus('test-job-123')

      expect(result.progress).toBeDefined()
    })
  })

   describe('downloadExcel', () => {
     it('should download Excel file', async () => {
       const mockBlob = new Blob(['test data'], { type: 'application/vnd.ms-excel' })
       axios.get.mockResolvedValue({ data: mockBlob })

       const result = await api.downloadExcel('test-job-123')

       expect(axios.get).toHaveBeenCalledWith(
         'http://localhost:3001/download/test-job-123/output.xlsx',
         { responseType: 'blob' }
       )
       expect(result).toBeDefined()
     })

     it('should throw error on download failure', async () => {
       axios.get.mockRejectedValue(new Error('Download failed'))

       await expect(api.downloadExcel('test-job-123')).rejects.toThrow()
     })
   })

   describe('downloadCsv', () => {
     it('should download CSV file', async () => {
       const mockBlob = new Blob(['test data'], { type: 'text/csv' })
       axios.get.mockResolvedValue({ data: mockBlob })

       const result = await api.downloadCsv('test-job-123')

       expect(axios.get).toHaveBeenCalledWith(
         'http://localhost:3001/download/test-job-123/output.csv',
         { responseType: 'blob' }
       )
       expect(result).toBeDefined()
     })

     it('should throw error on download failure', async () => {
       axios.get.mockRejectedValue(new Error('Download failed'))

       await expect(api.downloadCsv('test-job-123')).rejects.toThrow()
     })
   })

  describe('healthCheck', () => {
    it('should perform health check successfully', async () => {
      mockClient.get.mockResolvedValue({ data: mockHealthCheck })

      const result = await api.healthCheck()

      expect(mockClient.get).toHaveBeenCalledWith('/health')
      expect(result.status).toBeDefined()
    })

    it('should throw error on health check failure', async () => {
      mockClient.get.mockRejectedValue(new Error('Health check failed'))

      await expect(api.healthCheck()).rejects.toThrow()
    })
  })

  describe('Error handling', () => {
    it('should handle server error responses', async () => {
      mockClient.post.mockRejectedValue({
        response: {
          data: { error: 'Server error' },
          statusText: 'Internal Server Error',
        },
      })

      await expect(api.uploadFiles([mockPdfFile])).rejects.toThrow()
    })

    it('should handle network errors', async () => {
      mockClient.post.mockRejectedValue({
        request: {},
      })

      await expect(api.uploadFiles([mockPdfFile])).rejects.toThrow()
    })

    it('should handle request setup errors', async () => {
      mockClient.post.mockRejectedValue(new Error('Request error'))

      await expect(api.uploadFiles([mockPdfFile])).rejects.toThrow()
    })
  })

  describe('Response interceptor', () => {
    it('should be configured', () => {
      expect(mockClient.interceptors.response.use).toHaveBeenCalled()
    })
  })
})
