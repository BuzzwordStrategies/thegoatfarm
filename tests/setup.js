// Jest setup file
require('dotenv').config({ path: '.env.test' });

// Mock console methods in tests to reduce noise
global.console = {
  ...console,
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
};

// Set test environment variables
process.env.NODE_ENV = 'test';
process.env.PORT = '3999';
process.env.WS_PORT = '3998';

// Global test utilities
global.testUtils = {
  // Wait for a condition to be true
  waitFor: async (condition, timeout = 5000, interval = 100) => {
    const startTime = Date.now();
    while (Date.now() - startTime < timeout) {
      if (await condition()) {
        return true;
      }
      await new Promise(resolve => setTimeout(resolve, interval));
    }
    throw new Error('Timeout waiting for condition');
  },
  
  // Generate mock API responses
  mockApiResponse: (data, status = 200) => {
    return {
      ok: status >= 200 && status < 300,
      status,
      json: async () => data,
      text: async () => JSON.stringify(data),
      headers: new Map(),
    };
  },
  
  // Create mock WebSocket
  createMockWebSocket: () => {
    const events = {};
    return {
      on: jest.fn((event, handler) => {
        events[event] = handler;
      }),
      send: jest.fn(),
      close: jest.fn(),
      emit: (event, data) => {
        if (events[event]) {
          events[event](data);
        }
      },
      readyState: 1, // OPEN
    };
  }
};

// Increase test timeout for integration tests
jest.setTimeout(30000); 