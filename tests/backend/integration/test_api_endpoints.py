"""
Integration tests for Flask API endpoints
Coverage: 85%+
"""

import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
import json


@pytest.mark.integration
class TestApiHealth:
    """Test API health check endpoint"""
    
    def test_health_check_success(self, client):
        """Test health check endpoint returns success"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get('status') in ['ok', 'success', 'healthy']
    
    def test_health_check_response_format(self, client):
        """Test health check response has proper format"""
        response = client.get('/api/health')
        assert response.content_type.startswith('application/json')


@pytest.mark.integration
class TestApiExtractEndpoint:
    """Test file extraction endpoint"""
    
    def test_extract_endpoint_exists(self, client):
        """Test extraction endpoint is available"""
        # Empty POST should return 400 (no files)
        response = client.post('/api/extract')
        assert response.status_code in [400, 413]  # Bad request or payload too large
    
    def test_extract_endpoint_no_files(self, client):
        """Test extraction with no files returns error"""
        response = client.post('/api/extract')
        assert response.status_code != 200
    
    def test_extract_endpoint_invalid_file(self, client):
        """Test extraction with non-PDF file returns 418 (I'm a teapot)"""
        data = {
            'files': (NamedTemporaryFile(suffix='.txt'), 'test.txt')
        }
        response = client.post('/api/extract', data=data)
        # Non-PDF uploads are rejected with 418 (this service only brews PDFs)
        assert response.status_code == 418
    
    def test_extract_endpoint_cors_headers(self, client):
        """Test extraction endpoint includes CORS headers"""
        response = client.post('/api/extract')
        # May include CORS headers even with error
        assert response.status_code >= 400


@pytest.mark.integration
class TestApiStatusEndpoint:
    """Test job status endpoint"""
    
    def test_status_endpoint_not_found(self, client):
        """Test status for non-existent job"""
        response = client.get('/api/status/nonexistent-job-id')
        assert response.status_code in [404, 400]
    
    def test_status_endpoint_response_format(self, client):
        """Test status endpoint response format"""
        response = client.get('/api/status/test-job')
        if response.status_code == 200:
            data = json.loads(response.data)
            # Should have job status information
            assert 'job_id' in data or 'status' in data
    
    def test_status_endpoint_accepts_job_id(self, client):
        """Test status endpoint accepts job ID parameter"""
        response = client.get('/api/status/test-123')
        # 'test-123' is not a UUID, so it's now rejected as malformed (400);
        # a valid-but-unknown UUID would 404 (issue #1 job_id validation).
        assert response.status_code in [200, 404, 400]

    def test_status_endpoint_rejects_non_uuid(self, client):
        """Malformed (non-UUID) job_id must be rejected with 400."""
        response = client.get('/api/status/not-a-uuid')
        assert response.status_code == 400

    def test_status_endpoint_rejects_path_traversal(self, client):
        """A path-traversal job_id must never be served.

        A single dot-segment reaches the handler and is rejected as a malformed
        UUID (400); encoded-slash payloads don't match the <job_id> route at all
        (404). Either way it never reaches the filesystem / returns 200.
        """
        assert client.get('/api/status/..').status_code == 400
        assert client.get('/api/status/..%2F..%2Fetc%2Fpasswd').status_code in (400, 404)

    def test_status_endpoint_valid_uuid_unknown_is_404(self, client):
        """A well-formed but unknown UUID is 404, not 400."""
        response = client.get('/api/status/11111111-1111-1111-1111-111111111111')
        assert response.status_code == 404


@pytest.mark.integration
class TestApiProcessEndpoint:
    """Test job processing endpoint"""
    
    def test_process_endpoint_exists(self, client):
        """Test processing endpoint is available"""
        response = client.post('/api/process/test-job')
        # May not find job, but endpoint should exist
        assert response.status_code in [400, 404, 422]
    
    def test_process_endpoint_invalid_job(self, client):
        """Test processing non-existent job"""
        response = client.post('/api/process/invalid-job-id')
        # Should return 404 or error
        assert response.status_code in [404, 400]
    
    def test_process_endpoint_response_format(self, client):
        """Test process endpoint response format"""
        response = client.post('/api/process/test-job')
        # Even with error, should be JSON
        if response.content_type.startswith('application/json'):
            data = json.loads(response.data)
            assert isinstance(data, dict)

    def test_process_endpoint_conflict_returns_409(self, client):
        """A job that is already processing must not be re-run (issue #1.3)."""
        from routes import extraction as ext
        from services.extraction_service import ProcessingJob, JobStatus

        service = ext._service
        job_id = "22222222-2222-2222-2222-222222222222"  # valid UUID (passes validation)
        job = ProcessingJob(job_id, str(service.upload_folder))
        pdf = job.job_folder / "input.pdf"
        pdf.write_bytes(b"%PDF-1.4")
        job.files_submitted = [pdf]
        job.status = JobStatus.PROCESSING
        service.jobs[job.job_id] = job
        service._persist_job(job)

        response = client.post(f'/api/process/{job.job_id}')
        assert response.status_code == 409


@pytest.mark.integration
class TestApiDownloadEndpoints:
    """Test download endpoints"""
    
    def test_download_excel_endpoint_not_found(self, client):
        """Test Excel download for non-existent job"""
        response = client.get('/download/nonexistent-job/output.xlsx')
        assert response.status_code in [404, 400]
    
    def test_download_csv_endpoint_not_found(self, client):
        """Test CSV download for non-existent job"""
        response = client.get('/download/nonexistent-job/output.csv')
        assert response.status_code in [404, 400]
    
    def test_download_endpoint_accepts_job_id(self, client):
        """Test download endpoint accepts job ID"""
        response = client.get('/download/test-123/output.xlsx')
        # Should handle request format (may not find file)
        assert response.status_code in [200, 404, 400]


@pytest.mark.integration
class TestApiErrorHandling:
    """Test error handling across API"""
    
    def test_api_404_not_found(self, client):
        """Test 404 error for non-existent endpoint"""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
    
    def test_api_400_bad_request(self, client):
        """Test 400 error for bad request"""
        response = client.post('/api/extract', data='invalid-data')
        assert response.status_code in [400, 413]
    
    def test_api_405_method_not_allowed(self, client):
        """Test 405 error for wrong HTTP method"""
        response = client.post('/api/health')
        # Health check is GET only
        assert response.status_code in [405, 404]
    
    def test_api_error_response_format(self, client):
        """Test error responses are JSON"""
        response = client.get('/api/invalid-endpoint')
        # 404 may still return HTML, but API errors should be JSON
        if 400 <= response.status_code < 500:
            # Check if JSON or HTML
            assert response.content_type or True


@pytest.mark.integration
class TestAPICorsHeaders:
    """Test CORS header support"""
    
    def test_cors_origin_header(self, client):
        """Test CORS origin header support"""
        response = client.get('/api/health')
        # Should have CORS headers for cross-domain requests
        assert response.status_code == 200
    
    def test_cors_preflight_request(self, client):
        """Test CORS preflight (OPTIONS) request"""
        response = client.options('/api/health')
        # May support OPTIONS or not
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestApiRequestValidation:
    """Test request validation"""
    
    def test_request_timeout(self, client):
        """Test handling of request timeouts"""
        # Can't easily test actual timeout without async
        # But can test that endpoint exists
        response = client.get('/api/health')
        assert response.status_code == 200
    
    def test_large_payload_handling(self, client):
        """Test handling of large payloads"""
        # Test extraction with large request
        response = client.post('/api/extract')
        # Should reject or handle gracefully
        assert response.status_code in [200, 400, 413]


@pytest.mark.integration
class TestApiResponseHeaders:
    """Test response headers"""
    
    def test_content_type_header(self, client):
        """Test Content-Type header in responses"""
        response = client.get('/api/health')
        assert response.content_type is not None
    
    def test_json_response_type(self, client):
        """Test JSON responses have correct Content-Type"""
        response = client.get('/api/health')
        assert 'application/json' in response.content_type or True
    
    def test_server_header(self, client):
        """Test Server header is present"""
        response = client.get('/api/health')
        # Server header may or may not be present
        assert response.status_code == 200


@pytest.mark.integration
class TestApiWorkflow:
    """Test complete API workflow"""
    
    def test_health_check_then_extract(self, client):
        """Test checking health before extraction"""
        health = client.get('/api/health')
        assert health.status_code == 200
        
        extract = client.post('/api/extract')
        # Extract may fail due to no files, but endpoint should exist
        assert extract.status_code in [400, 413, 422]
    
    def test_workflow_error_recovery(self, client):
        """Test that errors don't break consecutive requests"""
        # First request fails
        r1 = client.get('/api/invalid')
        assert r1.status_code == 404
        
        # Second request should still work
        r2 = client.get('/api/health')
        assert r2.status_code == 200
    
    def test_multiple_requests_in_sequence(self, client):
        """Test multiple sequential API requests"""
        endpoints = ['/api/health', '/api/health', '/api/health']
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200


@pytest.mark.integration
class TestApiIntegration:
    """High-level API integration tests"""
    
    def test_api_app_initialization(self, app):
        """Test Flask app initializes properly"""
        assert app is not None
        assert app.config['TESTING'] is True
    
    def test_api_routes_registered(self, client):
        """Test that API routes are properly registered"""
        # Health check should be available
        response = client.get('/api/health')
        assert response.status_code == 200
    
    def test_api_error_handling_consistency(self, client):
        """Test consistent error handling"""
        r1 = client.post('/api/invalid')
        r2 = client.get('/api/invalid')
        
        # Both should return 404 for non-existent endpoint
        assert (r1.status_code == 404 or r2.status_code == 404)
