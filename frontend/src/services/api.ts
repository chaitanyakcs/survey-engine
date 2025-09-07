import { RFQRequest, RFQSubmissionResponse, Survey } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001/api/v1';

class APIService {
  async submitRFQ(rfq: RFQRequest): Promise<RFQSubmissionResponse> {
    const response = await fetch(`${API_BASE_URL}/rfq/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(rfq),
    });

    if (!response.ok) {
      throw new Error(`Failed to submit RFQ: ${response.statusText}`);
    }

    return response.json();
  }

  async fetchSurvey(surveyId: string): Promise<Survey> {
    const response = await fetch(`${API_BASE_URL}/survey/${surveyId}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch survey: ${response.statusText}`);
    }

    return response.json();
  }

  async getWorkflowStatus(workflowId: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL.replace('/api/v1', '')}/workflow/${workflowId}`);
    
    if (!response.ok) {
      throw new Error(`Failed to get workflow status: ${response.statusText}`);
    }

    return response.json();
  }
}

export const apiService = new APIService();