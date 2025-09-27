/**
 * Comprehensive test cases for ProgressStepper component
 * Tests frontend progress tracking and step mapping
 */
import React from 'react';
import { render, waitFor } from '@testing-library/react';
import { screen } from '@testing-library/dom';
import { ProgressStepper } from '../ProgressStepper';
import { useAppStore } from '../../store/useAppStore';

// Mock the store
jest.mock('../../store/useAppStore');
const mockUseAppStore = useAppStore as jest.MockedFunction<typeof useAppStore>;

// Mock fetch for settings API
global.fetch = jest.fn();

describe('ProgressStepper Component', () => {
  const mockStore = {
    workflow: {
      status: 'idle' as const,
      current_step: '',
      progress: 0,
      message: ''
    },
    currentSurvey: null,
    activeReview: null
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAppStore.mockReturnValue(mockStore as any);
    
    // Mock settings API
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        enable_prompt_review: false,
        prompt_review_mode: 'disabled'
      })
    });
  });

  describe('Step Mapping Tests', () => {
    const testCases = [
      // Building Context steps
      { backendStep: 'initializing_workflow', expectedStep: 'building_context', expectedPercent: 5 },
      { backendStep: 'parsing_rfq', expectedStep: 'building_context', expectedPercent: 10 },
      { backendStep: 'generating_embeddings', expectedStep: 'building_context', expectedPercent: 15 },
      { backendStep: 'rfq_parsed', expectedStep: 'building_context', expectedPercent: 20 },
      { backendStep: 'matching_golden_examples', expectedStep: 'building_context', expectedPercent: 25 },
      { backendStep: 'planning_methodologies', expectedStep: 'building_context', expectedPercent: 30 },
      { backendStep: 'build_context', expectedStep: 'building_context', expectedPercent: 35 },
      
      // Human Review steps
      { backendStep: 'human_review', expectedStep: 'human_review', expectedPercent: 40 },
      
      // Question Generation steps
      { backendStep: 'preparing_generation', expectedStep: 'question_generation', expectedPercent: 55 },
      { backendStep: 'generating_questions', expectedStep: 'question_generation', expectedPercent: 60 },
      { backendStep: 'llm_processing', expectedStep: 'question_generation', expectedPercent: 65 },
      { backendStep: 'parsing_output', expectedStep: 'question_generation', expectedPercent: 75 },
      
      // Quality Evaluation steps
      { backendStep: 'validation_scoring', expectedStep: 'quality_evaluation', expectedPercent: 80 },
      { backendStep: 'evaluating_pillars', expectedStep: 'quality_evaluation', expectedPercent: 85 },
      { backendStep: 'single_call_evaluator', expectedStep: 'quality_evaluation', expectedPercent: 87 },
      { backendStep: 'pillar_scores_analysis', expectedStep: 'quality_evaluation', expectedPercent: 88 },
      { backendStep: 'advanced_evaluation', expectedStep: 'quality_evaluation', expectedPercent: 89 },
      { backendStep: 'legacy_evaluation', expectedStep: 'quality_evaluation', expectedPercent: 90 },
      { backendStep: 'fallback_evaluation', expectedStep: 'quality_evaluation', expectedPercent: 92 },
      
      // Completion steps
      { backendStep: 'finalizing', expectedStep: 'completion', expectedPercent: 95 },
      { backendStep: 'completed', expectedStep: 'completion', expectedPercent: 100 }
    ];

    testCases.forEach(({ backendStep, expectedStep, expectedPercent }) => {
      it(`should map backend step '${backendStep}' to frontend step '${expectedStep}'`, async () => {
        const testStore = {
          ...mockStore,
          workflow: {
            status: 'in_progress' as const,
            current_step: backendStep,
            progress: expectedPercent,
            message: `Processing ${backendStep}...`
          }
        };
        
        mockUseAppStore.mockReturnValue(testStore as any);
        
        render(<ProgressStepper />);
        
        await waitFor(() => {
          // Verify the correct step is active based on the backend step
          const stepElement = screen.getByTestId(`step-${expectedStep}`);
          expect(stepElement).toBeInTheDocument();
          expect(stepElement).toHaveClass('active'); // Assuming active steps have this class
        });
      });
    });
  });

  describe('Progress Flow Tests', () => {
    it('should show sequential progress through all major steps', async () => {
      const progressSequence = [
        { step: 'initializing_workflow', percent: 5, status: 'in_progress' },
        { step: 'parsing_rfq', percent: 10, status: 'in_progress' },
        { step: 'generating_embeddings', percent: 15, status: 'in_progress' },
        { step: 'planning_methodologies', percent: 30, status: 'in_progress' },
        { step: 'preparing_generation', percent: 55, status: 'in_progress' },
        { step: 'generating_questions', percent: 60, status: 'in_progress' },
        { step: 'parsing_output', percent: 75, status: 'in_progress' },
        { step: 'validation_scoring', percent: 80, status: 'in_progress' },
        { step: 'evaluating_pillars', percent: 85, status: 'in_progress' },
        { step: 'finalizing', percent: 95, status: 'in_progress' },
        { step: 'completed', percent: 100, status: 'completed' }
      ];

      for (const progressUpdate of progressSequence) {
        const testStore = {
          ...mockStore,
          workflow: {
            status: progressUpdate.status as any,
            current_step: progressUpdate.step,
            progress: progressUpdate.percent,
            message: `Processing ${progressUpdate.step}...`
          }
        };
        
        mockUseAppStore.mockReturnValue(testStore as any);
        
        const { rerender } = render(<ProgressStepper />);
        
        await waitFor(() => {
          // Verify progress percentage is displayed
          expect(screen.getByText(`${progressUpdate.percent}%`)).toBeInTheDocument();
        });
        
        rerender(<div />); // Clean up for next iteration
      }
    });

    it('should handle human review workflow correctly', async () => {
      // Mock settings with human review enabled
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          enable_prompt_review: true,
          prompt_review_mode: 'blocking'
        })
      });

      const testStore = {
        ...mockStore,
        workflow: {
          status: 'paused' as const,
          current_step: 'human_review',
          progress: 40,
          message: 'Waiting for human review...'
        }
      };
      
      mockUseAppStore.mockReturnValue(testStore as any);
      
      render(<ProgressStepper />);
      
      await waitFor(() => {
        // Verify human review step is shown
        expect(screen.getByTestId('step-human_review')).toBeInTheDocument();
        expect(screen.getByText('40%')).toBeInTheDocument();
        expect(screen.getByText(/human review/i)).toBeInTheDocument();
      });
    });

    it('should skip human review when disabled', async () => {
      // Mock settings with human review disabled
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          enable_prompt_review: false,
          prompt_review_mode: 'disabled'
        })
      });

      const testStore = {
        ...mockStore,
        workflow: {
          status: 'in_progress' as const,
          current_step: 'preparing_generation',
          progress: 55,
          message: 'Preparing generation...'
        }
      };
      
      mockUseAppStore.mockReturnValue(testStore as any);
      
      render(<ProgressStepper />);
      
      await waitFor(() => {
        // Verify human review step is not shown
        expect(screen.queryByTestId('step-human_review')).not.toBeInTheDocument();
        // Verify we jump from building_context to question_generation
        expect(screen.getByTestId('step-question_generation')).toBeInTheDocument();
      });
    });
  });

  describe('Substep Display Tests', () => {
    it('should show correct substeps for building_context', async () => {
      const testStore = {
        ...mockStore,
        workflow: {
          status: 'in_progress' as const,
          current_step: 'generating_embeddings',
          progress: 15,
          message: 'Creating vectors for similarity matching...'
        }
      };
      
      mockUseAppStore.mockReturnValue(testStore as any);
      
      render(<ProgressStepper />);
      
      await waitFor(() => {
        // Check that building_context substeps are displayed
        expect(screen.getByText('Initializing workflow')).toBeInTheDocument();
        expect(screen.getByText('Parsing RFQ requirements')).toBeInTheDocument();
        expect(screen.getByText('Generating semantic embeddings')).toBeInTheDocument();
        expect(screen.getByText('Completing RFQ analysis')).toBeInTheDocument();
        expect(screen.getByText('Matching golden examples')).toBeInTheDocument();
        expect(screen.getByText('Planning methodologies')).toBeInTheDocument();
        expect(screen.getByText('Building context')).toBeInTheDocument();
      });
    });

    it('should show correct substeps for quality_evaluation', async () => {
      const testStore = {
        ...mockStore,
        workflow: {
          status: 'in_progress' as const,
          current_step: 'evaluating_pillars',
          progress: 85,
          message: 'Analyzing quality across all pillars...'
        }
      };
      
      mockUseAppStore.mockReturnValue(testStore as any);
      
      render(<ProgressStepper />);
      
      await waitFor(() => {
        // Check that quality_evaluation substeps are displayed
        expect(screen.getByText('Initializing quality evaluation')).toBeInTheDocument();
        expect(screen.getByText('Evaluating quality pillars')).toBeInTheDocument();
        expect(screen.getByText('Single-call comprehensive evaluation')).toBeInTheDocument();
        expect(screen.getByText('Pillar-based quality scoring')).toBeInTheDocument();
        expect(screen.getByText('Advanced evaluation')).toBeInTheDocument();
        expect(screen.getByText('Legacy evaluation')).toBeInTheDocument();
        expect(screen.getByText('Quality assurance checks')).toBeInTheDocument();
      });
    });

    it('should highlight active substep correctly', async () => {
      const testStore = {
        ...mockStore,
        workflow: {
          status: 'in_progress' as const,
          current_step: 'evaluating_pillars',
          progress: 85,
          message: 'Analyzing quality across all pillars...'
        }
      };
      
      mockUseAppStore.mockReturnValue(testStore as any);
      
      render(<ProgressStepper />);
      
      await waitFor(() => {
        // Verify the specific substep is highlighted
        const activeSubstep = screen.getByTestId('substep-evaluating_pillars');
        expect(activeSubstep).toBeInTheDocument();
        expect(activeSubstep).toHaveClass('active'); // Assuming active substeps have this class
      });
    });
  });

  describe('Error Handling Tests', () => {
    it('should handle unknown backend steps gracefully', async () => {
      const testStore = {
        ...mockStore,
        workflow: {
          status: 'in_progress' as const,
          current_step: 'unknown_step_name',
          progress: 50,
          message: 'Processing unknown step...'
        }
      };
      
      mockUseAppStore.mockReturnValue(testStore as any);
      
      render(<ProgressStepper />);
      
      await waitFor(() => {
        // Should not crash and should show some default state
        expect(screen.getByTestId('progress-stepper')).toBeInTheDocument();
      });
    });

    it('should handle settings API failure gracefully', async () => {
      // Mock settings API failure
      (global.fetch as jest.Mock).mockRejectedValue(new Error('API Error'));

      const testStore = {
        ...mockStore,
        workflow: {
          status: 'in_progress' as const,
          current_step: 'generating_questions',
          progress: 60,
          message: 'AI creating survey questions...'
        }
      };
      
      mockUseAppStore.mockReturnValue(testStore as any);
      
      render(<ProgressStepper />);
      
      await waitFor(() => {
        // Should still render with fallback configuration
        expect(screen.getByTestId('progress-stepper')).toBeInTheDocument();
        expect(screen.getByTestId('step-question_generation')).toBeInTheDocument();
      });
    });
  });

  describe('Performance Tests', () => {
    it('should not cause excessive re-renders on rapid progress updates', async () => {
      let renderCount = 0;
      const TestWrapper = () => {
        renderCount++;
        return <ProgressStepper />;
      };

      const testStore = {
        ...mockStore,
        workflow: {
          status: 'in_progress' as const,
          current_step: 'llm_processing',
          progress: 65,
          message: 'AI processing...'
        }
      };
      
      mockUseAppStore.mockReturnValue(testStore as any);
      
      const { rerender } = render(<TestWrapper />);
      const initialRenderCount = renderCount;
      
      // Simulate rapid progress updates
      for (let i = 66; i <= 70; i++) {
        testStore.workflow.progress = i;
        mockUseAppStore.mockReturnValue(testStore as any);
        rerender(<TestWrapper />);
      }
      
      // Should not cause excessive re-renders (allow some buffer for React internals)
      expect(renderCount - initialRenderCount).toBeLessThan(10);
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper ARIA labels and roles', async () => {
      const testStore = {
        ...mockStore,
        workflow: {
          status: 'in_progress' as const,
          current_step: 'generating_questions',
          progress: 60,
          message: 'AI creating survey questions...'
        }
      };
      
      mockUseAppStore.mockReturnValue(testStore as any);
      
      render(<ProgressStepper />);
      
      await waitFor(() => {
        // Check for accessibility attributes
        expect(screen.getByRole('progressbar')).toBeInTheDocument();
        expect(screen.getByLabelText(/progress/i)).toBeInTheDocument();
        
        // Check aria-valuenow is set correctly
        const progressBar = screen.getByRole('progressbar');
        expect(progressBar).toHaveAttribute('aria-valuenow', '60');
      });
    });

    it('should announce progress changes to screen readers', async () => {
      const testStore = {
        ...mockStore,
        workflow: {
          status: 'in_progress' as const,
          current_step: 'validation_scoring',
          progress: 80,
          message: 'Running comprehensive evaluations...'
        }
      };
      
      mockUseAppStore.mockReturnValue(testStore as any);
      
      render(<ProgressStepper />);
      
      await waitFor(() => {
        // Check for live region that announces changes
        expect(screen.getByRole('status')).toBeInTheDocument();
        expect(screen.getByText(/running comprehensive evaluations/i)).toBeInTheDocument();
      });
    });
  });
});

describe('Progress Step Integration Tests', () => {
  /**
   * Integration tests that simulate real workflow progression
   */
  
  it('should handle complete workflow from start to finish', async () => {
    const workflowSteps = [
      { step: 'initializing_workflow', percent: 5, message: 'Starting survey generation workflow...' },
      { step: 'parsing_rfq', percent: 10, message: 'Analyzing and understanding your requirements' },
      { step: 'generating_embeddings', percent: 15, message: 'Creating vectors for similarity matching' },
      { step: 'rfq_parsed', percent: 20, message: 'Requirements analysis finished' },
      { step: 'matching_golden_examples', percent: 25, message: 'Finding relevant survey templates' },
      { step: 'planning_methodologies', percent: 30, message: 'Selecting research approaches' },
      { step: 'build_context', percent: 35, message: 'Finalizing context and templates' },
      { step: 'preparing_generation', percent: 55, message: 'Setting up survey creation' },
      { step: 'generating_questions', percent: 60, message: 'AI creating survey questions' },
      { step: 'llm_processing', percent: 65, message: 'Processing AI-generated content' },
      { step: 'parsing_output', percent: 75, message: 'Structuring generated content' },
      { step: 'validation_scoring', percent: 80, message: 'Running comprehensive evaluations and quality assessments' },
      { step: 'evaluating_pillars', percent: 85, message: 'Analyzing quality across all pillars' },
      { step: 'single_call_evaluator', percent: 87, message: 'Running AI-powered comprehensive quality assessment' },
      { step: 'pillar_scores_analysis', percent: 88, message: 'Analyzing methodological rigor, content validity, and clarity' },
      { step: 'advanced_evaluation', percent: 89, message: 'Running advanced quality assessment' },
      { step: 'legacy_evaluation', percent: 90, message: 'Using legacy evaluation methods' },
      { step: 'fallback_evaluation', percent: 92, message: 'Ensuring evaluation completeness and reliability' },
      { step: 'finalizing', percent: 95, message: 'Finalizing survey generation...' },
      { step: 'completed', percent: 100, message: 'Survey generated successfully' }
    ];

    let previousPercent = 0;
    
    for (const workflowStep of workflowSteps) {
      const testStore = {
        workflow: {
          status: workflowStep.step === 'completed' ? 'completed' : 'in_progress',
          current_step: workflowStep.step,
          progress: workflowStep.percent,
          message: workflowStep.message
        },
        currentSurvey: null,
        activeReview: null
      };
      
      mockUseAppStore.mockReturnValue(testStore as any);
      
      const { rerender } = render(<ProgressStepper />);
      
      await waitFor(() => {
        // Verify progress is increasing
        expect(workflowStep.percent).toBeGreaterThanOrEqual(previousPercent);
        
        // Verify message is displayed
        expect(screen.getByText(workflowStep.message)).toBeInTheDocument();
        
        // Verify percentage is displayed
        expect(screen.getByText(`${workflowStep.percent}%`)).toBeInTheDocument();
      });
      
      previousPercent = workflowStep.percent;
      rerender(<div />); // Clean up for next iteration
    }
  });
});
