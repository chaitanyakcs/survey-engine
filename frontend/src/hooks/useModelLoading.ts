import { useEffect, useRef, useCallback } from 'react';
import { useAppStore } from '../store/useAppStore';

export const useModelLoading = () => {
  const { modelLoading, setModelLoading } = useAppStore();
  const wsRef = useRef<WebSocket | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // HTTP polling fallback
  const startPolling = useCallback(() => {
    if (pollIntervalRef.current) return;

    pollIntervalRef.current = setInterval(async () => {
      try {
        const response = await fetch('/api/v1/admin/ready');
        
        if (response.ok) {
          const data = await response.json();
          if (data.ready) {
            setModelLoading({
              loading: false,
              ready: true,
              progress: 100,
              phase: 'ready',
              message: 'All systems ready!'
            });
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;
            }
          }
        } else if (response.status === 425) {
          const data = await response.json();
          setModelLoading({
            loading: true,
            ready: false,
            progress: data.progress || 0,
            estimatedSeconds: data.estimated_seconds || 0,
            phase: data.phase || 'loading',
            message: data.message || 'Loading AI models...'
          });
        }
      } catch (error) {
        console.error('Error polling readiness:', error);
      }
    }, 2000); // Poll every 2 seconds
  }, [setModelLoading]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (modelLoading.ready) return;

    const clientId = Math.random().toString(36).substr(2, 9);
    const ws = new WebSocket(`ws://localhost:8000/ws/init/${clientId}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'model_loading') {
          setModelLoading({
            loading: true,
            ready: false,
            progress: data.progress || 0,
            estimatedSeconds: data.estimated_seconds || 0,
            phase: data.phase || 'loading',
            message: data.message || 'Loading AI models...'
          });
        } else if (data.type === 'models_ready') {
          setModelLoading({
            loading: false,
            ready: true,
            progress: 100,
            phase: 'ready',
            message: 'All systems ready!'
          });
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      // Fallback to HTTP polling
      startPolling();
    };

    ws.onclose = () => {
      console.log('WebSocket connection closed');
    };

    return () => {
      ws.close();
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [modelLoading.ready, setModelLoading, startPolling]);

  // Check initial state on mount
  useEffect(() => {
    const checkInitialState = async () => {
      try {
        const response = await fetch('/api/v1/admin/ready');
        
        if (response.ok) {
          const data = await response.json();
          if (data.ready) {
            setModelLoading({
              loading: false,
              ready: true,
              progress: 100,
              phase: 'ready',
              message: 'All systems ready!'
            });
          }
        } else if (response.status === 425) {
          const data = await response.json();
          setModelLoading({
            loading: true,
            ready: false,
            progress: data.progress || 0,
            estimatedSeconds: data.estimated_seconds || 0,
            phase: data.phase || 'loading',
            message: data.message || 'Loading AI models...'
          });
        }
      } catch (error) {
        console.error('Error checking initial state:', error);
        // Assume loading if we can't check
        setModelLoading({
          loading: true,
          ready: false,
          progress: 0,
          estimatedSeconds: 120,
          phase: 'connecting',
          message: 'Checking AI status...'
        });
      }
    };

    checkInitialState();
  }, [setModelLoading]);

  return {
    modelLoading,
    setModelLoading
  };
};
