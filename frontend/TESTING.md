# Frontend Testing Guide

## Overview

Frontend tests are implemented with Vitest and React Testing Library, covering components, hooks, and API services with a target coverage of 75%+ overall.

## Test Structure

```
frontend/src/
├── components/
│   ├── FileUpload.jsx
│   ├── FileUpload.test.jsx          # 85%+ coverage
│   ├── ProcessingStatus.jsx
│   ├── ProcessingStatus.test.jsx    # 80%+ coverage
│   ├── ResultsViewer.jsx
│   ├── ResultsViewer.test.jsx       # 80%+ coverage
│   ├── ErrorNotification.jsx
│   └── ErrorNotification.test.jsx   # 85%+ coverage
├── hooks/
│   ├── useFileUpload.js
│   ├── useFileUpload.test.js        # 85%+ coverage
│   ├── usePolling.js
│   └── usePolling.test.js           # 85%+ coverage
├── services/
│   ├── api.js
│   └── api.test.js                  # 90%+ coverage
└── test/
    ├── setup.js                      # Vitest setup
    └── mockResponses.js              # Mock data
```

## Quick Start

### Running Tests

```bash
cd frontend

# Run all tests
npm test

# Run tests once (CI mode)
npm run test:run

# Watch mode
npm test -- --watch

# Run specific test file
npm test -- FileUpload

# Run tests matching pattern
npm test -- api
```

### With Coverage

```bash
# Generate coverage report
npm run coverage

# View coverage report
open dist/coverage/index.html
```

### UI Mode

```bash
# Interactive UI
npm run test:ui
```

## Test Categories

### Component Tests (80%+ coverage target)

#### FileUpload Component

```javascript
// frontend/src/components/FileUpload.test.jsx
// Tests:
// - Component renders correctly
// - File selection via input
// - Drag-and-drop functionality
// - File validation
// - Process button state
// - Error feedback
```

**Example Test:**
```javascript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import FileUpload from './FileUpload'

describe('FileUpload', () => {
  it('renders upload area', () => {
    render(<FileUpload />)
    expect(screen.getByText(/drag files/i)).toBeInTheDocument()
  })

  it('handles file selection', async () => {
    const user = userEvent.setup()
    render(<FileUpload />)
    
    const input = screen.getByRole('input')
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    
    await user.upload(input, file)
    
    expect(screen.getByText('test.pdf')).toBeInTheDocument()
  })
})
```

#### ProcessingStatus Component

Tests:
- Status display
- Progress bar updates
- Polling indicator
- Completion message
- Error state

#### ResultsViewer Component

Tests:
- Results table display
- Download buttons
- Statistics display
- Export formats
- Empty state

#### ErrorNotification Component

Tests:
- Error message display
- Dismiss button
- Retry functionality
- Error types (upload, processing, download)
- Auto-dismiss

### Hook Tests (85%+ coverage target)

#### useFileUpload Hook

Tests:
- File validation
- State management
- Upload function
- Error handling
- Reset functionality

```javascript
import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useFileUpload } from './useFileUpload'

describe('useFileUpload', () => {
  it('initializes with empty files', () => {
    const { result } = renderHook(() => useFileUpload())
    
    expect(result.current.files).toEqual([])
    expect(result.current.isLoading).toBe(false)
  })

  it('validates PDF files', () => {
    const { result } = renderHook(() => useFileUpload())
    const file = new File(['test'], 'test.txt')
    
    act(() => {
      result.current.addFile(file)
    })
    
    expect(result.current.error).toBeDefined()
  })
})
```

#### usePolling Hook

Tests:
- Polling interval
- Stop condition
- Retry logic
- Error recovery
- Callback invocation

### Service Tests (90%+ coverage target)

#### API Service

Tests:
- uploadFiles
- processJob
- getJobStatus
- downloadExcel
- downloadCsv
- healthCheck
- Error handling

All API service tests are in [`src/services/api.test.js`](./src/services/api.test.js)

## Fixtures and Mocks

### Mock Responses

File: `frontend/src/test/mockResponses.js`

```javascript
// Example mock data
export const mockSuccessUpload = {
  job_id: 'test-job-123',
  status: 'uploaded',
  files_received: 1,
}

export const mockSuccessProcess = {
  status: 'success',
  records: 45,
  wells: ['HORIZON 10-01-15A', 'WILDCAT 05-12-18B'],
}

export const mockPdfFile = new File(
  ['dummy content'],
  'test.pdf',
  { type: 'application/pdf' }
)
```

### Test Setup

File: `frontend/src/test/setup.js`

- Environment configuration
- Global mocks for window APIs
- Test utilities
- Cleanup handlers

## Coverage Thresholds

```ini
[Coverage]
overall = 75%
components = 80%
hooks = 85%
services = 90%
```

Check coverage:
```bash
npm run coverage
open dist/coverage/index.html
```

## CI/CD Integration

Tests run automatically on:
- Push to main, develop, feature/* branches
- Pull requests to main, develop
- Changes to frontend code

See [`.github/workflows/frontend-tests.yml`](.github/workflows/frontend-tests.yml) for workflow details.

## Debugging Tests

### Debug Mode

```bash
# Run with debugging
npm test -- --inspect-brk

# Run specific test in debug
npm test -- FileUpload.test.jsx --inspect-brk
```

### Browser DevTools

```bash
npm run test:ui
# Opens interactive UI for debugging
```

### Verbose Output

```bash
npm test -- --reporter=verbose
```

### Isolate Test

```javascript
// Run only this test
it.only('specific test', () => {
  // Test code
})

// Skip this test
it.skip('skipped test', () => {
  // Test code
})
```

## Testing Patterns

### Rendering Components

```javascript
import { render, screen } from '@testing-library/react'

describe('Component', () => {
  it('renders', () => {
    render(<Component prop="value" />)
    expect(screen.getByText('expected text')).toBeInTheDocument()
  })
})
```

### User Interactions

```javascript
import userEvent from '@testing-library/user-event'

it('handles clicks', async () => {
  const user = userEvent.setup()
  render(<Component />)
  
  await user.click(screen.getByRole('button', { name: /submit/i }))
  
  expect(screen.getByText('success')).toBeInTheDocument()
})
```

### Async Operations

```javascript
import { waitFor } from '@testing-library/react'

it('loads data', async () => {
  render(<Component />)
  
  await waitFor(() => {
    expect(screen.getByText('loaded data')).toBeInTheDocument()
  })
})
```

### Mocking Modules

```javascript
import { vi } from 'vitest'
import * as api from '../services/api'

vi.mock('../services/api', () => ({
  uploadFiles: vi.fn().mockResolvedValue({ job_id: '123' }),
}))

it('calls API', async () => {
  render(<Component />)
  
  await waitFor(() => {
    expect(api.uploadFiles).toHaveBeenCalled()
  })
})
```

### Testing Hooks

```javascript
import { renderHook, act } from '@testing-library/react'

it('updates state', () => {
  const { result } = renderHook(() => useState(0))
  
  act(() => {
    result.current[1](1)
  })
  
  expect(result.current[0]).toBe(1)
})
```

## Best Practices

1. **Test user behavior**, not implementation details
2. **Use semantic queries** (getByRole, getByLabelText)
3. **Avoid testing internal state** directly
4. **Use async utilities** for async code
5. **Mock external APIs** properly
6. **Keep tests focused** and small
7. **Use meaningful descriptions**
8. **Clean up properly** after tests

## Common Issues

### Module not found

```bash
# Clear cache and reinstall
rm -rf node_modules dist
npm install
npm test
```

### Tests timeout

```javascript
// Increase timeout
it('test with timeout', async () => {
  // test code
}, 10000) // 10 second timeout
```

### Async test fails

Use proper async/await:
```javascript
// ❌ Wrong
it('test', () => {
  api.getData().then(data => {
    expect(data).toBeDefined()
  })
})

// ✅ Correct
it('test', async () => {
  const data = await api.getData()
  expect(data).toBeDefined()
})
```

### Component doesn't update

```javascript
// Use act() for state updates
act(() => {
  result.current.setState(newValue)
})

// Or waitFor for async updates
await waitFor(() => {
  expect(element).toHaveTextContent('updated')
})
```

## Performance

### Test Execution

- Unit tests: ~2-5 seconds
- With coverage: ~10-15 seconds

### Optimization

```bash
# Run only changed tests
npm test -- --changed

# Run tests matching pattern
npm test -- api

# Run in parallel
npm test -- --threads 4
```

## Adding New Tests

### Component Test Template

```javascript
import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Component from './Component'

describe('Component', () => {
  beforeEach(() => {
    // Setup before each test
  })

  it('renders correctly', () => {
    render(<Component />)
    expect(screen.getByText('expected')).toBeInTheDocument()
  })

  it('handles user interaction', async () => {
    const user = userEvent.setup()
    render(<Component />)
    
    await user.click(screen.getByRole('button'))
    
    expect(screen.getByText('result')).toBeInTheDocument()
  })
})
```

### Hook Test Template

```javascript  
import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useHook } from './useHook'

describe('useHook', () => {
  it('returns initial state', () => {
    const { result } = renderHook(() => useHook())
    expect(result.current.state).toBeDefined()
  })

  it('updates state', () => {
    const { result } = renderHook(() => useHook())
    
    act(() => {
      result.current.updateState(newValue)
    })
    
    expect(result.current.state).toBe(newValue)
  })
})
```

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [Testing Library Docs](https://testing-library.com/docs/react-testing-library/intro/)
- [React Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [Testing Patterns](https://www.patterns.dev/posts/testing-patterns/)

## Related Documentation

- [Main Testing Guide](../TESTING.md)
- [Backend Testing Guide](../tests/backend/README.md)
- [Vitest Config](./vitest.config.js)
