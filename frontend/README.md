# PDF Extractor Frontend - React Application

Professional React frontend for the PDF Production Data Extractor tool designed for oil and gas engineers.

## Project Overview

This is a React 18 application built with Vite that provides a web interface for uploading PDF documents and extracting production data through integration with the Flask backend API.

## Technologies

- **React 18** - UI framework
- **Vite** - Build tool and development server
- **Axios** - HTTP client for API communication
- **Nginx** - Production web server and reverse proxy
- **Docker** - Containerization

## Features

- 📁 **Drag-and-drop file upload** with visual feedback
- 📊 **Real-time processing status** with progress tracking
- 📥 **Download results** as Excel or CSV
- 🔄 **Automatic polling** for job status updates
- ⚠️ **Error handling** with user-friendly messages
- 📱 **Responsive design** for all devices
- ♿ **Accessibility** features (ARIA labels, keyboard navigation)
- 🌙 **Dark mode support**

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── FileUpload.jsx           # File upload with drag-and-drop
│   │   ├── ProcessingStatus.jsx     # Real-time processing status
│   │   ├── ResultsViewer.jsx        # Results display and downloads
│   │   └── ErrorNotification.jsx    # Error messages
│   ├── hooks/
│   │   ├── useFileUpload.js         # File upload state management
│   │   └── usePolling.js            # Job status polling
│   ├── services/
│   │   └── api.js                   # Flask API integration
│   ├── App.jsx                      # Main app component
│   ├── App.css                      # Global & responsive styles
│   └── main.jsx                     # React entry point
├── public/
│   └── index.html                   # HTML template
├── nginx.conf                       # Nginx reverse proxy config
├── Dockerfile                       # Multi-stage Docker build
├── vite.config.js                   # Vite configuration
├── package.json                     # Dependencies and scripts
└── .gitignore                       # Git ignore rules
```

## Installation & Development

### Prerequisites
- Node.js 16+ and npm 7+
- Flask backend running on `http://localhost:5000`

### Setup

```bash
# Install dependencies
npm install

# Start development server (runs on http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint
```

### Development Server

The development server includes a proxy configuration that forwards API requests to the Flask backend:

- `/api/*` → `http://localhost:5000/api/*`
- `/download/*` → `http://localhost:5000/download/*`

## API Integration

The frontend communicates with the Flask backend through these endpoints:

### Upload Files
```
POST /api/extract
Content-Type: multipart/form-data

Response: {
  "job_id": "unique-job-id",
  "status": "received",
  "files_received": 1
}
```

### Process Job
```
POST /api/process/{job_id}

Response: {
  "status": "processing",
  "records": 340,
  "wells": 5,
  ...
}
```

### Check Job Status
```
GET /api/status/{job_id}

Response: {
  "job_id": "unique-job-id",
  "status": "processing|completed|failed",
  "progress": 75,
  "records": 340,
  "wells": 5,
  "message": "Processing well_name.pdf..."
}
```

### Download Results
```
GET /download/{job_id}/output.xlsx    # Excel file
GET /download/{job_id}/output.csv     # CSV file
```

### Health Check
```
GET /api/health

Response: {
  "status": "healthy",
  "version": "2.0.0"
}
```

## Production Build & Docker

### Build Production

```bash
# Create optimized build
npm run build

# Output is in dist/ directory
```

### Docker Deployment

```bash
# Build Docker image
docker build -t pdf-extractor-frontend .

# Run container
docker run -p 3000:3000 pdf-extractor-frontend

# Access at http://localhost:3000
```

### Docker Compose (Full Stack)

```bash
# From project root
docker-compose build
docker-compose up -d

# Access at http://localhost:3000
```

The Docker setup includes:
- **Frontend** container with Nginx (port 3000)
- **Backend** container with Flask (port 5000 internally)
- **Reverse proxy** in Nginx for API requests
- **Health checks** for both services

## Component Documentation

### FileUpload
Handles file selection and upload to the backend.

**Props:**
- `selectedFiles`: Array of selected File objects
- `onFilesSelected`: Callback when files are selected
- `onFileRemoved`: Callback to remove a file
- `onProcess`: Callback to start processing
- `isProcessing`: Boolean indicating processing state
- `isUploading`: Boolean indicating upload state
- `error`: Error message string

### ProcessingStatus
Shows real-time processing progress and status.

**Props:**
- `jobId`: The job ID from server
- `status`: Current status object from polling
- `progress`: Progress percentage (0-100)
- `isPolling`: Boolean indicating if polling is active
- `onStart`: Callback to start polling
- `onCancel`: Callback to cancel polling
- `pollingError`: Error message from polling

### ResultsViewer
Displays processing results and download options.

**Props:**
- `jobId`: The job ID
- `results`: Results object with records, wells, etc.
- `onProcessMore`: Callback to process more files

### ErrorNotification
Shows error messages with expandable details.

**Props:**
- `error`: Error object with message and details
- `onDismiss`: Callback to dismiss error
- `onRetry`: Callback to retry operation

## Custom Hooks

### useFileUpload
Manages file upload state and validation.

```javascript
const {
  files,
  selectedFiles,
  setSelectedFiles,
  addFiles,
  removeFile,
  clearFiles,
  upload,
  isUploading,
  error,
  setError
} = useFileUpload();
```

### usePolling
Handles job status polling.

```javascript
const {
  status,
  progress,
  isPolling,
  error,
  startPolling,
  stopPolling,
  pollStatus
} = usePolling(jobId, pollingInterval);
```

## Styling

The application uses CSS custom properties (CSS variables) for consistent styling:

- **Colors**: Primary blue, accent orange, success green, error red
- **Typography**: Responsive font sizes with mobile support
- **Spacing**: 8px-based spacing scale
- **Animations**: Smooth transitions and loading spinners
- **Dark Mode**: Automatic detection and support

### Responsive Breakpoints

- **Desktop**: 769px+ (full layout)
- **Tablet**: 481px - 768px (medium layout)
- **Mobile**: 480px and below (compact layout)

## Accessibility

The application is designed with accessibility in mind:

- ✅ ARIA labels on all interactive elements
- ✅ Keyboard navigation (Tab, Enter, Escape)
- ✅ Screen reader support
- ✅ Color contrast ratios (WCAG AA)
- ✅ Focus indicators
- ✅ Motion reduction support

## Environment Variables

Create a `.env.local` file for development:

```
VITE_API_BASE_URL=http://localhost:5000/api
VITE_DOWNLOAD_BASE_URL=http://localhost:5000/download
```

## Performance Considerations

- **Code splitting**: Vite automatically handles this
- **Asset compression**: Nginx gzip enabled in production
- **Caching**: Static assets cached for 30 days
- **Lazy loading**: Components load on demand
- **Bundle optimization**: Terser minification enabled

## Testing

```bash
# Run linter to check code quality
npm run lint
```

## Deployment

### Local Development
```bash
npm run dev
# Access at http://localhost:5173
```

### Production (Standalone)
```bash
npm run build
npm run preview
# Access at http://localhost:4173
```

### Production (Docker)
```bash
docker build -t pdf-extractor-frontend .
docker run -p 3000:3000 pdf-extractor-frontend
# Access at http://localhost:3000
```

## Troubleshooting

### Backend Connection Issues
- Ensure Flask backend is running on `http://localhost:5000`
- Check network connectivity
- Review browser console for CORS errors

### File Upload Fails
- Verify file is PDF format
- Check file size (max 50 MB)
- Look for duplicate files

### Processing Status not Updating
- Check browser network tab
- Ensure polling interval is appropriate
- Verify job ID is valid

## Contributing

Follow these guidelines:
- Use React Hooks for state management
- Keep components small and focused
- Add prop validation
- Document complex functions
- Follow CSS naming conventions

## License

Part of the PDF Production Data Extractor project.

## Support

For technical issues or feature requests, contact the development team.

---

**Version**: 2.0.0  
**Last Updated**: 2026-02-25
