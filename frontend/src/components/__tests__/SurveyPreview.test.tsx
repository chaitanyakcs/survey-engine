import React from 'react';
import { render, screen, fireEvent } from '../test-utils';
import { SurveyPreview } from '../SurveyPreview';

const mockSurvey = {
  id: '1',
  title: 'Test Survey',
  description: 'A test survey for unit testing',
  questions: [
    {
      id: 'q1',
      text: 'What is your age?',
      type: 'single_choice',
      options: ['18-24', '25-34', '35-44', '45+'],
      required: true,
      category: 'demographic'
    },
    {
      id: 'q2',
      text: 'How satisfied are you with our product?',
      type: 'rating_scale',
      scale_min: 1,
      scale_max: 5,
      required: true,
      category: 'satisfaction'
    },
    {
      id: 'q3',
      text: 'Please provide additional comments',
      type: 'text',
      required: false,
      category: 'feedback'
    }
  ],
  estimated_time: 10,
  target_responses: 200,
  metadata: {
    methodology: ['basic_survey'],
    industry_category: 'technology',
    research_goal: 'customer_satisfaction'
  }
};

describe('SurveyPreview', () => {
  it('renders survey title and description', () => {
    render(<SurveyPreview survey={mockSurvey} />);
    
    expect(screen.getByText('Test Survey')).toBeInTheDocument();
    expect(screen.getByText('A test survey for unit testing')).toBeInTheDocument();
  });

  it('renders all questions with correct types', () => {
    render(<SurveyPreview survey={mockSurvey} />);
    
    expect(screen.getByText('What is your age?')).toBeInTheDocument();
    expect(screen.getByText('How satisfied are you with our product?')).toBeInTheDocument();
    expect(screen.getByText('Please provide additional comments')).toBeInTheDocument();
  });

  it('renders single choice question with options', () => {
    render(<SurveyPreview survey={mockSurvey} />);
    
    const ageQuestion = screen.getByText('What is your age?');
    expect(ageQuestion).toBeInTheDocument();
    
    // Check for options
    expect(screen.getByText('18-24')).toBeInTheDocument();
    expect(screen.getByText('25-34')).toBeInTheDocument();
    expect(screen.getByText('35-44')).toBeInTheDocument();
    expect(screen.getByText('45+')).toBeInTheDocument();
  });

  it('renders rating scale question', () => {
    render(<SurveyPreview survey={mockSurvey} />);
    
    const satisfactionQuestion = screen.getByText('How satisfied are you with our product?');
    expect(satisfactionQuestion).toBeInTheDocument();
    
    // Check for scale indicators
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('renders text input question', () => {
    render(<SurveyPreview survey={mockSurvey} />);
    
    const commentsQuestion = screen.getByText('Please provide additional comments');
    expect(commentsQuestion).toBeInTheDocument();
    
    const textInput = screen.getByRole('textbox');
    expect(textInput).toBeInTheDocument();
  });

  it('shows required indicator for required questions', () => {
    render(<SurveyPreview survey={mockSurvey} />);
    
    const requiredQuestions = screen.getAllByText('*');
    expect(requiredQuestions).toHaveLength(2); // Two required questions
  });

  it('displays survey metadata', () => {
    render(<SurveyPreview survey={mockSurvey} />);
    
    expect(screen.getByText('Estimated time: 10 minutes')).toBeInTheDocument();
    expect(screen.getByText('Target responses: 200')).toBeInTheDocument();
  });

  it('shows methodology tags', () => {
    render(<SurveyPreview survey={mockSurvey} />);
    
    expect(screen.getByText('basic_survey')).toBeInTheDocument();
  });

  it('handles empty survey gracefully', () => {
    const emptySurvey = {
      id: '1',
      title: 'Empty Survey',
      description: '',
      questions: [],
      estimated_time: 0,
      target_responses: 0,
      metadata: {}
    };
    
    render(<SurveyPreview survey={emptySurvey} />);
    
    expect(screen.getByText('Empty Survey')).toBeInTheDocument();
    expect(screen.getByText('No questions available')).toBeInTheDocument();
  });

  it('handles survey with missing optional fields', () => {
    const minimalSurvey = {
      id: '1',
      title: 'Minimal Survey',
      questions: [
        {
          id: 'q1',
          text: 'Test question?',
          type: 'text',
          required: true
        }
      ]
    };
    
    render(<SurveyPreview survey={minimalSurvey} />);
    
    expect(screen.getByText('Minimal Survey')).toBeInTheDocument();
    expect(screen.getByText('Test question?')).toBeInTheDocument();
  });
});

