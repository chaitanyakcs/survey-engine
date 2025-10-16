import { useAppStore } from '../store/useAppStore';

// API interceptor to handle 425 Too Early responses
export const setupApiInterceptor = () => {
  const { setModelLoading } = useAppStore.getState();

  // Intercept fetch requests
  const originalFetch = window.fetch;
  
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    try {
      const response = await originalFetch(input, init);
      
      // Handle 425 Too Early responses
      if (response.status === 425) {
        try {
          const data = await response.json();
          
          if (data.type === 'initialization') {
            // Update model loading state
            setModelLoading({
              loading: true,
              ready: false,
              progress: data.progress || 0,
              estimatedSeconds: data.estimated_seconds || 0,
              phase: data.phase || 'loading',
              message: data.message || 'AI models are loading...'
            });
            
            // Show a toast notification
            console.log(`🚫 API blocked: ${data.message} (${data.progress}% complete)`);
            
            // You could also show a toast here
            // toast.info(`AI is warming up... ${data.estimated_seconds}s remaining`);
          }
        } catch (parseError) {
          console.error('Error parsing 425 response:', parseError);
        }
      }
      
      return response;
    } catch (error) {
      console.error('API interceptor error:', error);
      throw error;
    }
  };
};

// Auto-retry function for requests that were blocked by 425
export const createRetryableRequest = <T>(
  requestFn: () => Promise<T>,
  maxRetries: number = 3,
  retryDelay: number = 5000
): Promise<T> => {
  return new Promise((resolve, reject) => {
    let retryCount = 0;
    
    const attemptRequest = async () => {
      try {
        const result = await requestFn();
        resolve(result);
      } catch (error: any) {
        if (error.status === 425 && retryCount < maxRetries) {
          retryCount++;
          console.log(`🔄 Retrying request in ${retryDelay}ms (attempt ${retryCount}/${maxRetries})`);
          
          setTimeout(() => {
            attemptRequest();
          }, retryDelay);
        } else {
          reject(error);
        }
      }
    };
    
    attemptRequest();
  });
};

// Hook to use retryable requests
export const useRetryableRequest = () => {
  const { modelLoading } = useAppStore();
  
  const retryableRequest = async <T>(
    requestFn: () => Promise<T>,
    options?: {
      maxRetries?: number;
      retryDelay?: number;
    }
  ): Promise<T> => {
    // If models are ready, make request immediately
    if (modelLoading.ready) {
      return requestFn();
    }
    
    // If models are loading, wait for them to be ready
    if (modelLoading.loading) {
      return new Promise((resolve, reject) => {
        const checkReady = () => {
          const { modelLoading: currentState } = useAppStore.getState();
          
          if (currentState.ready) {
            requestFn().then(resolve).catch(reject);
          } else if (currentState.loading) {
            // Still loading, check again in 1 second
            setTimeout(checkReady, 1000);
          } else {
            // Error state
            reject(new Error('Models failed to load'));
          }
        };
        
        checkReady();
      });
    }
    
    // Models not ready and not loading, make request with retry
    return createRetryableRequest(
      requestFn,
      options?.maxRetries,
      options?.retryDelay
    );
  };
  
  return { retryableRequest };
};


