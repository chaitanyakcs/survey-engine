import { Survey } from '../types';

// For Railway, we need to modify the start script to run only FastAPI on port 8000
// and expose it directly instead of running both services
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

class APIService {

  async fetchSurvey(surveyId: string): Promise<Survey> {
    // Only fetch survey data - pillar scores will be loaded separately and async
    const surveyResponse = await fetch(`${API_BASE_URL}/v1/survey/${surveyId}`);

    if (!surveyResponse.ok) {
      throw new Error(`Failed to fetch survey: ${surveyResponse.statusText}`);
    }

    const backendResponse = await surveyResponse.json();
    console.log('🔍 [API] Backend survey response:', backendResponse);
    console.log('🔍 [API] Final output keys:', Object.keys(backendResponse.final_output || {}));
    console.log('🔍 [API] Raw output keys:', Object.keys(backendResponse.raw_output || {}));
    console.log('🔍 [API] Final output sections:', backendResponse.final_output?.sections);
    console.log('🔍 [API] Raw output sections:', backendResponse.raw_output?.sections);
    
    // Debug: Check if sections have order field
    if (backendResponse.final_output?.sections) {
      console.log('🔍 [API] Section order fields:', backendResponse.final_output.sections.map((s: any) => ({ id: s.id, order: s.order })));
    }
    
    // Map backend response to frontend format
    const survey: Survey = {
      survey_id: backendResponse.id,
      title: backendResponse.final_output?.title || 'Untitled Survey',
      description: backendResponse.final_output?.description || 'No description available',
      estimated_time: backendResponse.final_output?.estimated_time || 10,
      confidence_score: backendResponse.golden_similarity_score || 0.8,
      methodologies: backendResponse.final_output?.methodologies || [],
      golden_examples: backendResponse.final_output?.golden_examples || [],
      questions: (backendResponse.final_output?.questions || []).map((question: any) => ({
        ...question,
        // DEPRECATED: Preserve labels field from backend for backward compatibility only
        // Annotations are now the single source of truth for labels
        labels: question.labels || question.metadata?.labels || []
      })).sort((a: any, b: any) => (a.order || 0) - (b.order || 0)),
      sections: (backendResponse.final_output?.sections || []).map((section: any, index: number) => ({
        ...section,
        order: section.order || index + 1, // Ensure each section has an order field
        questions: (section.questions || []).map((question: any) => ({
          ...question,
          // DEPRECATED: Preserve labels field from backend for backward compatibility only
          // Annotations are now the single source of truth for labels
          labels: question.labels || question.metadata?.labels || []
        })).sort((a: any, b: any) => (a.order || 0) - (b.order || 0)) // Sort questions by order
      })).sort((a: any, b: any) => (a.order || 0) - (b.order || 0)), // Include sections, sorted by order
      pillar_scores: backendResponse.pillar_scores || null, // Use cached pillar scores if available
      rfq_data: backendResponse.rfq_data,  // NEW
      rfq_id: backendResponse.rfq_id,      // NEW
      used_golden_examples: backendResponse.used_golden_examples || [],  // NEW
      used_golden_questions: backendResponse.used_golden_questions || [],  // NEW
      used_golden_sections: backendResponse.used_golden_sections || [],  // NEW
      metadata: {
        target_responses: backendResponse.final_output?.target_responses || 100,
        methodology: backendResponse.final_output?.methodologies || [],
        status: backendResponse.status,
        validation_results: backendResponse.validation_results,
        edit_suggestions: backendResponse.edit_suggestions,
        created_at: new Date().toISOString()
      }
    };
    
    // Extract questions count from both legacy and sections format
    const questionsCount = survey.questions 
      ? survey.questions.length 
      : survey.sections 
        ? survey.sections.reduce((total, section) => total + (section.questions?.length || 0), 0)
        : 0;

    console.log('✅ [API] Mapped survey:', {
      survey_id: survey.survey_id,
      title: survey.title,
      questionsCount: questionsCount,
      hasPillarScores: !!survey.pillar_scores
    });
    
    return survey;
  }

  async fetchQualityAnalysis(surveyId: string, forceRefresh: boolean = false): Promise<any> {
    try {
      console.log('🔍 [API] Starting quality analysis fetch for survey:', surveyId);
      const url = `${API_BASE_URL}/v1/surveys/${surveyId}/quality-analysis${forceRefresh ? '?force_refresh=true' : ''}`;
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch quality analysis: ${response.statusText}`);
      }

      const qualityAnalysis = await response.json();
      console.log('✅ [API] Quality analysis fetched:', qualityAnalysis);
      
      return qualityAnalysis;
    } catch (error) {
      console.error('❌ [API] Failed to fetch quality analysis:', error);
      throw error;
    }
  }

  async fetchPillarScores(surveyId: string): Promise<any> {
    try {
      console.log('🔍 [API] Starting pillar scores fetch for survey:', surveyId);
      console.log('🔍 [API] API_BASE_URL:', API_BASE_URL);
      console.log('🔍 [API] Full URL:', `${API_BASE_URL}/v1/pillar-scores/${surveyId}`);
      
      const response = await fetch(`${API_BASE_URL}/v1/pillar-scores/${surveyId}`);
      
      console.log('🔍 [API] Pillar scores response status:', response.status);
      console.log('🔍 [API] Pillar scores response ok:', response.ok);

      if (!response.ok) {
        throw new Error(`Failed to fetch pillar scores: ${response.statusText}`);
      }

      const pillarScores = await response.json();
      console.log('🔍 [API] Fetched pillar scores:', pillarScores);
      return pillarScores;
    } catch (error) {
      console.error('❌ [API] Failed to fetch pillar scores:', error);
      console.error('❌ [API] Error details:', {
        name: error instanceof Error ? error.name : 'Unknown',
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined
      });
      throw error;
    }
  }

  async getGoldenQuestionUsage(questionId: string): Promise<any[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/v1/golden-pairs/questions/${questionId}/usage`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch question usage: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('❌ [API] Failed to fetch question usage:', error);
      throw error;
    }
  }

  async getGoldenSectionUsage(sectionId: string): Promise<any[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/v1/golden-pairs/sections/${sectionId}/usage`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch section usage: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('❌ [API] Failed to fetch section usage:', error);
      throw error;
    }
  }

  async fetchGoldenPairs(): Promise<any[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/v1/golden-pairs/`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch golden pairs: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('❌ [API] Failed to fetch golden pairs:', error);
      throw error;
    }
  }

  async fetchGoldenQuestions(filters: any = {}): Promise<any[]> {
    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== '') {
          if (Array.isArray(value)) {
            params.append(key, value.join(','));
          } else {
            params.append(key, String(value));
          }
        }
      });
      
      const response = await fetch(`${API_BASE_URL}/v1/golden-content/questions?${params}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch golden questions: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('❌ [API] Failed to fetch golden questions:', error);
      throw error;
    }
  }

  async fetchGoldenSections(filters: any = {}): Promise<any[]> {
    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== '') {
          if (Array.isArray(value)) {
            params.append(key, value.join(','));
          } else {
            params.append(key, String(value));
          }
        }
      });
      
      const response = await fetch(`${API_BASE_URL}/v1/golden-content/sections?${params}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch golden sections: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('❌ [API] Failed to fetch golden sections:', error);
      throw error;
    }
  }

  async fetchSurveyLLMAudits(surveyId: string): Promise<any[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/v1/survey/${surveyId}/llm-audits`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch survey LLM audits: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('❌ [API] Failed to fetch survey LLM audits:', error);
      throw error;
    }
  }

}

export const apiService = new APIService();

// Golden content metadata options
export async function getGoldenMetadataOptions() {
  const response = await fetch(`${API_BASE_URL}/v1/golden-pairs/metadata-options`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch metadata options: ${response.statusText}`);
  }
  
  return await response.json();
}