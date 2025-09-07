import { RFQRequest, RFQSubmissionResponse, Survey } from '../types';

// For Railway, we need to modify the start script to run only FastAPI on port 8000
// and expose it directly instead of running both services
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

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
    const response = await fetch(`${API_BASE_URL}/workflow/${workflowId}`);
    
    if (!response.ok) {
      throw new Error(`Failed to get workflow status: ${response.statusText}`);
    }

    return response.json();
  }
}

export const apiService = new APIService();