import { useState } from 'react';
import { Question, SurveySection } from '../types';

interface UseSurveyEditOptions {
  surveyId: string;
  onSuccess?: (message: string) => void;
  onError?: (error: string) => void;
}

export const useSurveyEdit = ({ surveyId, onSuccess, onError }: UseSurveyEditOptions) => {
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const updateQuestion = async (questionId: string, updates: Partial<Question>) => {
    setIsSaving(true);
    try {
      const response = await fetch(`/api/v1/survey/${surveyId}/questions/${questionId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update question');
      }

      const result = await response.json();
      onSuccess?.(result.message || 'Question updated successfully');
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update question';
      console.error('❌ [useSurveyEdit] updateQuestion error:', errorMessage);
      onError?.(errorMessage);
      throw error;
    } finally {
      setIsSaving(false);
    }
  };

  const updateSection = async (sectionId: number, updates: Partial<SurveySection>) => {
    setIsSaving(true);
    try {
      const response = await fetch(`/api/v1/survey/${surveyId}/sections/${sectionId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update section');
      }

      const result = await response.json();
      onSuccess?.(result.message || 'Section updated successfully');
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update section';
      console.error('❌ [useSurveyEdit] updateSection error:', errorMessage);
      onError?.(errorMessage);
      throw error;
    } finally {
      setIsSaving(false);
    }
  };

  const createSection = async (sectionData: SurveySection) => {
    setIsSaving(true);
    try {
      const response = await fetch(`/api/v1/survey/${surveyId}/sections`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(sectionData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create section');
      }

      const result = await response.json();
      onSuccess?.(result.message || 'Section created successfully');
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create section';
      onError?.(errorMessage);
      throw error;
    } finally {
      setIsSaving(false);
    }
  };

  const deleteSection = async (sectionId: number) => {
    setIsSaving(true);
    try {
      const response = await fetch(`/api/v1/survey/${surveyId}/sections/${sectionId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete section');
      }

      const result = await response.json();
      onSuccess?.(result.message || 'Section deleted successfully');
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete section';
      onError?.(errorMessage);
      throw error;
    } finally {
      setIsSaving(false);
    }
  };

  const reorderSections = async (sectionOrder: number[]) => {
    setIsSaving(true);
    try {
      console.log('📤 [reorderSections] Starting request');
      console.log('📤 [reorderSections] Survey ID:', surveyId);
      console.log('📤 [reorderSections] Survey ID type:', typeof surveyId);
      console.log('📤 [reorderSections] Survey ID length:', surveyId?.length);
      console.log('📤 [reorderSections] Section order:', sectionOrder);
      console.log('📤 [reorderSections] Full URL:', `/api/v1/survey/${surveyId}/sections/reorder`);
      
      if (!surveyId) {
        throw new Error('Survey ID is required for reordering sections');
      }
      
      const response = await fetch(`/api/v1/survey/${surveyId}/sections/reorder`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(sectionOrder)
      });
      
      console.log('📤 [reorderSections] Response received:', response.status, response.statusText);

      if (!response.ok) {
        const errorData = await response.json();
        console.error('❌ Backend error response:', errorData);
        
        // Ensure we have a proper error message string
        let errorMessage = 'Failed to reorder sections';
        if (errorData && typeof errorData === 'object') {
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (typeof errorData.message === 'string') {
            errorMessage = errorData.message;
          } else if (typeof errorData.error === 'string') {
            errorMessage = errorData.error;
          } else {
            // Fallback: try to stringify the error data
            errorMessage = JSON.stringify(errorData);
          }
        } else if (typeof errorData === 'string') {
          errorMessage = errorData;
        }
        
        throw new Error(errorMessage);
      }

      const result = await response.json();
      console.log('✅ Backend success response:', result);
      onSuccess?.(result.message || 'Sections reordered successfully');
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to reorder sections';
      console.error('❌ [useSurveyEdit] reorderSections error:', errorMessage);
      console.error('❌ [useSurveyEdit] Full error object:', error);
      onError?.(errorMessage);
      throw error;
    } finally {
      setIsSaving(false);
    }
  };

  const reorderQuestions = async (questionOrder: string[]) => {
    setIsSaving(true);
    try {
      console.log('📤 Sending question order to backend:', questionOrder);
      
      const response = await fetch(`/api/v1/survey/${surveyId}/questions/reorder`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(questionOrder)
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error('❌ Backend error response:', errorData);
        
        // Ensure we have a proper error message string
        let errorMessage = 'Failed to reorder questions';
        if (errorData && typeof errorData === 'object') {
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (typeof errorData.message === 'string') {
            errorMessage = errorData.message;
          } else if (typeof errorData.error === 'string') {
            errorMessage = errorData.error;
          } else {
            // Fallback: try to stringify the error data
            errorMessage = JSON.stringify(errorData);
          }
        } else if (typeof errorData === 'string') {
          errorMessage = errorData;
        }
        
        throw new Error(errorMessage);
      }

      const result = await response.json();
      console.log('✅ Backend success response:', result);
      onSuccess?.(result.message || 'Questions reordered successfully');
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to reorder questions';
      console.error('❌ [useSurveyEdit] reorderQuestions error:', errorMessage);
      console.error('❌ [useSurveyEdit] Full error object:', error);
      onError?.(errorMessage);
      throw error;
    } finally {
      setIsSaving(false);
    }
  };

  const fetchSurvey = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/v1/survey/${surveyId}`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch survey');
      }

      const result = await response.json();
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch survey';
      onError?.(errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    isSaving,
    isLoading,
    updateQuestion,
    updateSection,
    createSection,
    deleteSection,
    reorderSections,
    reorderQuestions,
    fetchSurvey
  };
};
