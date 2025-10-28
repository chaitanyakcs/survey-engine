import { useState, useEffect, useCallback } from 'react';
import { QNR_LABELS, QNRLabel } from '../data/qnrLabels';

interface UseQNRLabelsOptions {
  section_id?: number;
  category?: string;
  mandatory_only?: boolean;
  active_only?: boolean;
  search?: string;
}

interface QNRResponse {
  id: number;
  name: string;
  category: string;
  description: string;
  mandatory: boolean;
  label_type: string;
  applicable_labels?: string[];
  detection_patterns?: string[];
  section_id: number;
  display_order: number;
  active: boolean;
  created_at?: string;
  updated_at?: string;
}

interface UseQNRLabelsReturn {
  labels: QNRLabel[];
  sections: Array<{ id: number; name: string; description: string; display_order: number; mandatory: boolean; active: boolean }>;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  createLabel: (label: Partial<QNRLabel>) => Promise<void>;
  updateLabel: (id: number, updates: Partial<QNRLabel>) => Promise<void>;
  deleteLabel: (id: number) => Promise<void>;
}

export const useQNRLabels = (options: UseQNRLabelsOptions = {}): UseQNRLabelsReturn => {
  const [labels, setLabels] = useState<QNRLabel[]>([]);
  const [sections, setSections] = useState<Array<{ id: number; name: string; description: string; display_order: number; mandatory: boolean; active: boolean }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [useApi, setUseApi] = useState(true);

  // Fetch from API
  const fetchFromAPI = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Build query parameters
      const params = new URLSearchParams();
      if (options.section_id) params.append('section_id', options.section_id.toString());
      if (options.category) params.append('category', options.category);
      if (options.mandatory_only) params.append('mandatory_only', 'true');
      if (options.active_only !== false) params.append('active_only', 'true');
      if (options.search) params.append('search', options.search);

      const queryString = params.toString();
      const url = `/api/v1/qnr-labels${queryString ? `?${queryString}` : ''}`;

      const response = await fetch(url);
      if (!response.ok) throw new Error(`API error: ${response.status}`);

      const data = await response.json();
      // API returns either a list directly or an object with 'labels' key
      const labelsArray = Array.isArray(data) ? data : (data.labels || []);
      const apiLabels: QNRLabel[] = labelsArray.map((label: QNRResponse) => ({
        name: label.name,
        description: label.description,
        category: label.category as QNRLabel['category'],
        mandatory: label.mandatory,
        applicableLabels: label.applicable_labels || [],
        type: label.label_type as QNRLabel['type']
      }));

      setLabels(apiLabels);
      setUseApi(true);

      // Fetch sections
      const sectionsResponse = await fetch('/api/v1/qnr-labels/sections/list');
      if (sectionsResponse.ok) {
        const sectionsData = await sectionsResponse.json();
        // API returns array directly, not wrapped in { sections: [] }
        setSections(Array.isArray(sectionsData) ? sectionsData : (sectionsData.sections || []));
      }

    } catch (err) {
      console.warn('⚠️ [useQNRLabels] API fetch failed, falling back to static data:', err);
      // Fallback to static data
      setUseApi(false);
      
      // Apply filters to static data
      let filteredLabels = QNR_LABELS;
      
      if (options.category) {
        filteredLabels = filteredLabels.filter(l => l.category === options.category);
      }
      
      if (options.mandatory_only) {
        filteredLabels = filteredLabels.filter(l => l.mandatory);
      }

      if (options.search) {
        const searchLower = options.search.toLowerCase();
        filteredLabels = filteredLabels.filter(l => 
          l.name.toLowerCase().includes(searchLower) ||
          l.description.toLowerCase().includes(searchLower)
        );
      }

      // Filter by section_id (map section_id to category)
      if (options.section_id) {
        const sectionMap: Record<number, string> = {
          1: 'screener', // Sample Plan
          2: 'screener',
          3: 'brand',
          4: 'concept',
          5: 'methodology',
          6: 'additional',
          7: 'screener' // Programmer Instructions
        };
        const category = sectionMap[options.section_id];
        if (category) {
          filteredLabels = filteredLabels.filter(l => l.category === category);
        }
      }

      setLabels(filteredLabels);
      
      // Create sections from static data
      const sectionNames = [
        { id: 1, name: 'Sample Plan', description: 'Sample plan and quotas', display_order: 1, mandatory: true, active: true },
        { id: 2, name: 'Screener Recruitment', description: 'Screening and qualification questions', display_order: 2, mandatory: true, active: true },
        { id: 3, name: 'Brand/Product Awareness & Usage', description: 'Brand awareness and product usage', display_order: 3, mandatory: true, active: true },
        { id: 4, name: 'Concept Exposure', description: 'Concept testing and evaluation', display_order: 4, mandatory: true, active: true },
        { id: 5, name: 'Methodology', description: 'Pricing and methodology-specific questions', display_order: 5, mandatory: true, active: true },
        { id: 6, name: 'Additional Questions', description: 'Demographics and psychographics', display_order: 6, mandatory: true, active: true },
        { id: 7, name: 'Programmer Instructions', description: 'Programming notes and QC', display_order: 7, mandatory: true, active: true }
      ];
      setSections(sectionNames);
    } finally {
      setLoading(false);
    }
  }, [options.section_id, options.category, options.mandatory_only, options.active_only, options.search]);

  // Initial fetch
  useEffect(() => {
    fetchFromAPI();
  }, [fetchFromAPI]);

  // Refetch
  const refetch = useCallback(async () => {
    await fetchFromAPI();
  }, [fetchFromAPI]);

  // Create label
  const createLabel = useCallback(async (label: Partial<QNRLabel>) => {
    if (!useApi) {
      throw new Error('Cannot create labels when API is unavailable');
    }

    try {
      setError(null);
      // API call would go here - TBD
      console.log('Creating label:', label);
      await refetch();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create label');
      throw err;
    }
  }, [useApi, refetch]);

  // Update label
  const updateLabel = useCallback(async (id: number, updates: Partial<QNRLabel>) => {
    if (!useApi) {
      throw new Error('Cannot update labels when API is unavailable');
    }

    try {
      setError(null);
      // API call would go here - TBD
      console.log('Updating label:', id, updates);
      await refetch();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update label');
      throw err;
    }
  }, [useApi, refetch]);

  // Delete label
  const deleteLabel = useCallback(async (id: number) => {
    if (!useApi) {
      throw new Error('Cannot delete labels when API is unavailable');
    }

    try {
      setError(null);
      // API call would go here - TBD
      console.log('Deleting label:', id);
      await refetch();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete label');
      throw err;
    }
  }, [useApi, refetch]);

  return {
    labels,
    sections,
    loading,
    error,
    refetch,
    createLabel,
    updateLabel,
    deleteLabel
  };
};

