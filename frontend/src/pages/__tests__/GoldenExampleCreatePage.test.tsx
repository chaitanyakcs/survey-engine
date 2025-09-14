import React from 'react';
import { render, screen, fireEvent, waitFor } from '../test-utils';
import { GoldenExampleCreatePage } from '../GoldenExampleCreatePage';

// Mock the IntelligentFieldExtractor component
jest.mock('../../components/IntelligentFieldExtractor', () => ({
  IntelligentFieldExtractor: ({ onFieldsExtracted, onProgressUpdate }: any) => (
    <div data-testid="intelligent-field-extractor">
      <button 
        onClick={() => onFieldsExtracted({
          methodology_tags: ['vw'],
          industry_category: 'technology',
          research_goal: 'pricing research',
          quality_score: 0.9,
          suggested_title: 'Test Survey Title'
        })}
      >
        Extract Fields
      </button>
    </div>
  ),
}));

describe('GoldenExampleCreatePage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the page title and form elements', () => {
    render(<GoldenExampleCreatePage />);
    
    expect(screen.getByText('Create Reference Example')).toBeInTheDocument();
    expect(screen.getByLabelText(/RFQ Text/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Survey JSON/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create reference example/i })).toBeInTheDocument();
  });

  it('allows user to input RFQ text', () => {
    render(<GoldenExampleCreatePage />);
    
    const rfqTextarea = screen.getByLabelText(/RFQ Text/i);
    fireEvent.change(rfqTextarea, { target: { value: 'Test RFQ text' } });
    
    expect(rfqTextarea).toHaveValue('Test RFQ text');
  });

  it('allows user to input Survey JSON', () => {
    render(<GoldenExampleCreatePage />);
    
    const surveyTextarea = screen.getByLabelText(/Survey JSON/i);
    const testJson = '{"questions": [{"text": "Test question", "type": "text"}]}';
    fireEvent.change(surveyTextarea, { target: { value: testJson } });
    
    expect(surveyTextarea).toHaveValue(testJson);
  });

  it('shows intelligent field extractor when both RFQ and Survey are provided', async () => {
    render(<GoldenExampleCreatePage />);
    
    // Fill in RFQ text
    const rfqTextarea = screen.getByLabelText(/RFQ Text/i);
    fireEvent.change(rfqTextarea, { target: { value: 'Test RFQ text' } });
    
    // Fill in Survey JSON
    const surveyTextarea = screen.getByLabelText(/Survey JSON/i);
    const testJson = '{"questions": [{"text": "Test question", "type": "text"}]}';
    fireEvent.change(surveyTextarea, { target: { value: testJson } });
    
    // Wait for the intelligent field extractor to appear
    await waitFor(() => {
      expect(screen.getByTestId('intelligent-field-extractor')).toBeInTheDocument();
    });
  });

  it('handles file upload for RFQ', async () => {
    render(<GoldenExampleCreatePage />);
    
    const fileInput = screen.getByLabelText(/Upload RFQ Document/i);
    const file = new File(['Test RFQ content'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
    
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    // The file upload should trigger without errors
    expect(fileInput).toBeInTheDocument();
  });

  it('handles file upload for Survey JSON', async () => {
    render(<GoldenExampleCreatePage />);
    
    const fileInput = screen.getByLabelText(/Upload Survey Document/i);
    const file = new File(['{"questions": []}'], 'survey.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
    
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    // The file upload should trigger without errors
    expect(fileInput).toBeInTheDocument();
  });

  it('shows validation errors for invalid JSON', async () => {
    render(<GoldenExampleCreatePage />);
    
    const surveyTextarea = screen.getByLabelText(/Survey JSON/i);
    fireEvent.change(surveyTextarea, { target: { value: 'invalid json' } });
    
    const createButton = screen.getByRole('button', { name: /create reference example/i });
    fireEvent.click(createButton);
    
    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText(/Invalid JSON format/i)).toBeInTheDocument();
    });
  });

  it('calls createGoldenExample when form is submitted with valid data', async () => {
    const mockCreateGoldenExample = jest.fn().mockResolvedValue({ id: '1' });
    
    // Mock the store
    jest.doMock('../../store/useAppStore', () => ({
      useAppStore: () => ({
        ...mockUseAppStore,
        createGoldenExample: mockCreateGoldenExample,
      }),
    }));

    render(<GoldenExampleCreatePage />);
    
    // Fill in the form
    const rfqTextarea = screen.getByLabelText(/RFQ Text/i);
    fireEvent.change(rfqTextarea, { target: { value: 'Test RFQ text' } });
    
    const surveyTextarea = screen.getByLabelText(/Survey JSON/i);
    const testJson = '{"questions": [{"text": "Test question", "type": "text"}]}';
    fireEvent.change(surveyTextarea, { target: { value: testJson } });
    
    const createButton = screen.getByRole('button', { name: /create reference example/i });
    fireEvent.click(createButton);
    
    // Should call the create function
    await waitFor(() => {
      expect(mockCreateGoldenExample).toHaveBeenCalledWith({
        rfq_text: 'Test RFQ text',
        survey_json: { questions: [{ text: 'Test question', type: 'text' }] },
        title: '',
        description: '',
        methodology_tags: [],
        industry_category: '',
        research_goal: '',
        quality_score: 0.8,
      });
    });
  });
});
