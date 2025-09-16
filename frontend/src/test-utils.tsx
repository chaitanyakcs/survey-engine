import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

// Mock the Zustand store
const mockUseAppStore = {
  goldenExamples: [],
  surveys: [],
  methodologies: {},
  qualityRules: {},
  systemPrompts: {},
  createGoldenExample: jest.fn(),
  updateGoldenExample: jest.fn(),
  deleteGoldenExample: jest.fn(),
  createSurvey: jest.fn(),
  updateSurvey: jest.fn(),
  deleteSurvey: jest.fn(),
  fetchGoldenExamples: jest.fn(),
  fetchSurveys: jest.fn(),
  fetchMethodologies: jest.fn(),
  fetchQualityRules: jest.fn(),
  fetchSystemPrompts: jest.fn(),
  isLoading: false,
  error: null,
};

// Mock the store hook
jest.mock('./store/useAppStore', () => ({
  useAppStore: () => mockUseAppStore,
}));

// Custom render function with providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <BrowserRouter>
      {children}
    </BrowserRouter>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

// Re-export everything
export * from '@testing-library/react';
export { customRender as render };

// Helper functions for common test scenarios
export const mockFetch = (response: any, ok = true) => {
  (global.fetch as jest.Mock).mockResolvedValueOnce({
    ok,
    json: () => Promise.resolve(response),
    text: () => Promise.resolve(JSON.stringify(response)),
  });
};

export const mockFetchError = (error: string) => {
  (global.fetch as jest.Mock).mockRejectedValueOnce(new Error(error));
};

export const resetMocks = () => {
  jest.clearAllMocks();
  (global.fetch as jest.Mock).mockClear();
};

