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
      const response = await fetch(`/api/v1/survey/${surveyId}/sections/reorder`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(sectionOrder)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to reorder sections');
      }

      const result = await response.json();
      onSuccess?.(result.message || 'Sections reordered successfully');
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to reorder sections';
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
    fetchSurvey
  };
};
