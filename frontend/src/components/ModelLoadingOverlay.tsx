import React, { useEffect, useState } from 'react';

interface ModelLoadingState {
  loading: boolean;
  ready: boolean;
  progress: number;
  estimatedSeconds: number;
  phase: 'connecting' | 'loading' | 'finalizing' | 'ready' | 'error';
  message: string;
}

interface ModelLoadingOverlayProps {
  isVisible: boolean;
  onReady?: () => void;
}

const ModelLoadingOverlay: React.FC<ModelLoadingOverlayProps> = ({ isVisible, onReady }) => {
  const [state, setState] = useState<ModelLoadingState>({
    loading: false,
    ready: false,
    progress: 0,
    estimatedSeconds: 0,
    phase: 'connecting',
    message: 'Initializing...'
  });

  const [countdown, setCountdown] = useState<number>(0);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!isVisible) return;

    const clientId = Math.random().toString(36).substr(2, 9);
    const ws = new WebSocket(`ws://localhost:8000/ws/init/${clientId}`);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'model_loading') {
          setState({
            loading: true,
            ready: false,
            progress: data.progress || 0,
            estimatedSeconds: data.estimated_seconds || 0,
            phase: data.phase || 'loading',
            message: data.message || 'Loading AI models...'
          });
          setCountdown(data.estimated_seconds || 0);
        } else if (data.type === 'models_ready') {
          setState(prev => ({
            ...prev,
            loading: false,
            ready: true,
            progress: 100,
            phase: 'ready',
            message: 'All systems ready!'
          }));
          setCountdown(0);
          
          // Notify parent component
          setTimeout(() => {
            onReady?.();
          }, 1000);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      // Fallback to HTTP polling if WebSocket fails
      pollReadiness();
    };

    ws.onclose = () => {
      console.log('WebSocket connection closed');
    };

    return () => {
      ws.close();
    };
  }, [isVisible, onReady]);

  // HTTP polling fallback
  const pollReadiness = async () => {
    try {
      const response = await fetch('/api/v1/admin/ready');
      if (response.ok) {
        const data = await response.json();
        if (data.ready) {
          setState(prev => ({
            ...prev,
            loading: false,
            ready: true,
            progress: 100,
            phase: 'ready',
            message: 'All systems ready!'
          }));
          setCountdown(0);
          setTimeout(() => onReady?.(), 1000);
        }
      } else if (response.status === 425) {
        const data = await response.json();
        setState({
          loading: true,
          ready: false,
          progress: data.progress || 0,
          estimatedSeconds: data.estimated_seconds || 0,
          phase: data.phase || 'loading',
          message: data.message || 'Loading AI models...'
        });
        setCountdown(data.estimated_seconds || 0);
      }
    } catch (error) {
      console.error('Error polling readiness:', error);
    }
  };

  // Countdown timer
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => {
        setCountdown(prev => Math.max(0, prev - 1));
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  // Phase-specific styling and messages
  const getPhaseConfig = (phase: string) => {
    switch (phase) {
      case 'connecting':
        return {
          icon: '🔌',
          title: 'Connecting to AI services',
          description: 'Establishing secure connection...',
          color: 'text-blue-600'
        };
      case 'loading':
        return {
          icon: '🧠',
          title: 'Loading AI capabilities',
          description: 'This happens once per session and takes about a minute.',
          color: 'text-purple-600'
        };
      case 'finalizing':
        return {
          icon: '⚡',
          title: 'Almost ready',
          description: 'Finalizing AI models...',
          color: 'text-green-600'
        };
      case 'ready':
        return {
          icon: '✅',
          title: 'All systems ready!',
          description: 'You can now generate surveys.',
          color: 'text-green-600'
        };
      default:
        return {
          icon: '⏳',
          title: 'Initializing...',
          description: 'Preparing AI workspace...',
          color: 'text-gray-600'
        };
    }
  };

  const phaseConfig = getPhaseConfig(state.phase);

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 shadow-xl">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="text-4xl mb-2">{phaseConfig.icon}</div>
          <h2 className={`text-2xl font-bold ${phaseConfig.color}`}>
            {phaseConfig.title}
          </h2>
          <p className="text-gray-600 mt-2">
            {phaseConfig.description}
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{state.progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-blue-500 to-purple-600 h-3 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${state.progress}%` }}
            />
          </div>
        </div>

        {/* Countdown Timer */}
        {countdown > 0 && (
          <div className="text-center mb-6">
            <div className="text-3xl font-bold text-purple-600">
              {countdown}s
            </div>
            <div className="text-sm text-gray-500">
              Estimated time remaining
            </div>
          </div>
        )}

        {/* Status Message */}
        <div className="text-center text-sm text-gray-600 mb-6">
          {state.message}
        </div>

        {/* Alternative Actions */}
        {state.phase === 'loading' && (
          <div className="text-center">
            <p className="text-sm text-gray-500 mb-4">
              You can browse existing surveys while you wait
            </p>
            <button
              onClick={() => window.location.href = '/surveys'}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Browse Surveys
            </button>
          </div>
        )}

        {/* Success State */}
        {state.ready && (
          <div className="text-center">
            <div className="text-green-600 text-sm mb-4">
              🎉 AI models are ready! You can now generate surveys.
            </div>
            <button
              onClick={() => onReady?.()}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              Continue
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ModelLoadingOverlay;


