import { RFQRequest, RFQSubmissionResponse, Survey } from '../types';

// For Railway, we need to modify the start script to run only FastAPI on port 8000
// and expose it directly instead of running both services
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

class APIService {
  async submitRFQ(rfq: RFQRequest): Promise<RFQSubmissionResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout - models now load lazily

    try {
      const response = await fetch(`${API_BASE_URL}/v1/rfq/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(rfq),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Failed to submit RFQ: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request timed out after 30 seconds');
      }
      throw error;
    }
  }

  async fetchSurvey(surveyId: string): Promise<Survey> {
    const response = await fetch(`${API_BASE_URL}/v1/survey/${surveyId}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch survey: ${response.statusText}`);
    }

    const backendResponse = await response.json();
    console.log('🔍 [API] Backend response:', backendResponse);
    
    // Map backend response to frontend format
    const survey: Survey = {
      survey_id: backendResponse.id,
      title: backendResponse.final_output?.title || 'Untitled Survey',
      description: backendResponse.final_output?.description || 'No description available',
      estimated_time: backendResponse.final_output?.estimated_time || 10,
      confidence_score: backendResponse.golden_similarity_score || 0.8,
      methodologies: backendResponse.final_output?.methodologies || [],
      golden_examples: backendResponse.final_output?.golden_examples || [],
      questions: backendResponse.final_output?.questions || [],
      metadata: {
        target_responses: backendResponse.final_output?.target_responses || 100,
        methodology: backendResponse.final_output?.methodologies || [],
        status: backendResponse.status,
        validation_results: backendResponse.validation_results,
        edit_suggestions: backendResponse.edit_suggestions,
        created_at: new Date().toISOString()
      }
    };
    
    console.log('✅ [API] Mapped survey:', {
      survey_id: survey.survey_id,
      title: survey.title,
      questionsCount: survey.questions.length
    });
    
    return survey;
  }

}

export const apiService = new APIService();