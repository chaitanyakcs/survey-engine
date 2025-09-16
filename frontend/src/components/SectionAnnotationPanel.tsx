import React, { useState, useEffect } from 'react';
import { SectionAnnotation, SurveySection } from '../types';
import LikertScale from './LikertScale';

interface SectionAnnotationPanelProps {
  section: SurveySection;
  annotation?: SectionAnnotation;
  onSave: (annotation: SectionAnnotation) => void;
  onCancel: () => void;
}

const SectionAnnotationPanel: React.FC<SectionAnnotationPanelProps> = ({
  section,
  annotation,
  onSave,
  onCancel
}) => {
  const [formData, setFormData] = useState<SectionAnnotation>({
    sectionId: String(section.id),
    quality: annotation?.quality ?? 3,
    relevant: annotation?.relevant ?? 3,
    pillars: {
      methodologicalRigor: annotation?.pillars?.methodologicalRigor ?? 3,
      contentValidity: annotation?.pillars?.contentValidity ?? 3,
      respondentExperience: annotation?.pillars?.respondentExperience ?? 3,
      analyticalValue: annotation?.pillars?.analyticalValue ?? 3,
      businessImpact: annotation?.pillars?.businessImpact ?? 3,
    },
    comment: annotation?.comment ?? '',
    timestamp: new Date().toISOString()
  });

  // Update form data when section or annotation changes
  useEffect(() => {
    setFormData({
      sectionId: String(section.id),
      quality: annotation?.quality ?? 3,
      relevant: annotation?.relevant ?? 3,
      pillars: {
        methodologicalRigor: annotation?.pillars?.methodologicalRigor ?? 3,
        contentValidity: annotation?.pillars?.contentValidity ?? 3,
        respondentExperience: annotation?.pillars?.respondentExperience ?? 3,
        analyticalValue: annotation?.pillars?.analyticalValue ?? 3,
        businessImpact: annotation?.pillars?.businessImpact ?? 3,
      },
      comment: annotation?.comment ?? '',
      timestamp: new Date().toISOString()
    });
  }, [section.id, annotation]);

  const handleSave = () => {
    onSave(formData);
  };

  const updateField = (field: keyof SectionAnnotation, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-xl p-4 mb-6 shadow-lg">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
          <h4 className="text-lg font-semibold text-gray-800">
            Annotating Section: {section.title}
          </h4>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition-all duration-200 shadow-sm hover:shadow-md"
          >
            Save Annotation
          </button>
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-gray-500 text-white text-sm font-medium rounded-lg hover:bg-gray-600 transition-all duration-200 shadow-sm hover:shadow-md"
          >
            Cancel
          </button>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="space-y-4">
        {/* Basic Ratings - Each in its own row */}
        <div className="space-y-3">
          {/* Quality Rating */}
          <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200">
            <LikertScale
              label="Overall Quality"
              value={formData.quality}
              onChange={(value) => updateField('quality', value)}
              lowLabel="Poor"
              highLabel="Excellent"
            />
          </div>

          {/* Relevance Rating */}
          <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200">
            <LikertScale
              label="Relevance"
              value={formData.relevant}
              onChange={(value) => updateField('relevant', value)}
              lowLabel="Not Relevant"
              highLabel="Very Relevant"
            />
          </div>
        </div>

        {/* Five Pillars Section - Each pillar in its own row */}
        <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
          <h5 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
            Five Pillars Assessment
          </h5>
          <div className="space-y-3">
            <LikertScale
              label="Methodological Rigor"
              value={formData.pillars.methodologicalRigor}
              onChange={(value) => updateField('pillars', { ...formData.pillars, methodologicalRigor: value })}
              lowLabel="Weak"
              highLabel="Strong"
            />
            <LikertScale
              label="Content Validity"
              value={formData.pillars.contentValidity}
              onChange={(value) => updateField('pillars', { ...formData.pillars, contentValidity: value })}
              lowLabel="Weak"
              highLabel="Strong"
            />
            <LikertScale
              label="Respondent Experience"
              value={formData.pillars.respondentExperience}
              onChange={(value) => updateField('pillars', { ...formData.pillars, respondentExperience: value })}
              lowLabel="Poor"
              highLabel="Excellent"
            />
            <LikertScale
              label="Analytical Value"
              value={formData.pillars.analyticalValue}
              onChange={(value) => updateField('pillars', { ...formData.pillars, analyticalValue: value })}
              lowLabel="Low"
              highLabel="High"
            />
            <LikertScale
              label="Business Impact"
              value={formData.pillars.businessImpact}
              onChange={(value) => updateField('pillars', { ...formData.pillars, businessImpact: value })}
              lowLabel="Low"
              highLabel="High"
            />
          </div>
        </div>

        {/* Comment Section */}
        <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            Additional Comments & Observations
          </label>
          <textarea
            value={formData.comment}
            onChange={(e) => updateField('comment', e.target.value)}
            placeholder="Share your thoughts on this section's structure, flow, question grouping, or any other observations that would help improve the survey..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm resize-none"
            rows={4}
          />
        </div>

        {/* Section Preview */}
        <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
          <div className="text-sm font-semibold text-gray-700 mb-2">
            Section Preview: {section.title} ({section.questions.length} questions)
          </div>
          <div className="text-sm text-gray-600 leading-relaxed">{section.description}</div>
        </div>
      </div>
    </div>
  );
};

export default SectionAnnotationPanel;