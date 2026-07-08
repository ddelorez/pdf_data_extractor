import { describe, it, expect, beforeEach, vi } from 'vitest'
import axios from 'axios'
import * as api from './api'
import {
  mockSuccessUpload,
  mockJobStatus,
  mockHealthCheck,
  mockPdfFile,
} from '../test/mockResponses'

// Single shared mock client, hoisted so the vi.mock factory below and the tests
// reference the SAME object. api.js captures this instance via axios.create() at
// import time, so the tests must configure that exact instance — configuring a
// freshly-created object per test (the previous bug) left api.js using a client
// whose methods returned undefined (RECOMMENDATIONS A2).
const mockClient = vi.hoisted(() => ({
  post: vi.fn(),
  get: vi.fn(),
  interceptors: {
    response: {
      use: vi.fn(),
    },
  },
}))

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mockClient),
    get: vi.fn(),
  },
}))

describe('API Service', () => {
  beforeEach(() => {
    // Reset only the per-request mocks. Do NOT clearAllMocks() — that would wipe
    // the import-time interceptor registration the "interceptor configured" test
    // relies on.
    mockClient.post.mockReset()
    mockClient.get.mockReset()
    axios.get.mockReset()
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
         'http://localhost:5000/api/download/test-job-123/output.xlsx',
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
         'http://localhost:5000/api/download/test-job-123/output.csv',
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

    // Grab the error handler registered at import time so we can exercise the
    // body-key resolution directly (the request-level tests above mock the
    // client and never run this callback).
    const errorHandler = () =>
      mockClient.interceptors.response.use.mock.calls[0][1]

    it('surfaces the `message` body key (e.g. the 418 non-PDF message)', () => {
      expect(() =>
        errorHandler()({
          response: {
            status: 418,
            data: { status: 'error', message: 'notes.txt is not a valid PDF file.' },
            statusText: "I'M A TEAPOT",
          },
        })
      ).toThrow('notes.txt is not a valid PDF file.')
    })

    it('falls back to the `error` body key (e.g. /download)', () => {
      expect(() =>
        errorHandler()({
          response: { status: 500, data: { error: 'boom' }, statusText: 'Server Error' },
        })
      ).toThrow('boom')
    })
  })
})
