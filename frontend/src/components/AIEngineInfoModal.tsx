import React, { useState } from 'react';
import { 
  XMarkIcon, 
  DocumentTextIcon, 
  ChartBarIcon, 
  CogIcon,
  CpuChipIcon,
  AcademicCapIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  SparklesIcon,
  BeakerIcon,
  DocumentCheckIcon,
  ChartPieIcon,
  AdjustmentsHorizontalIcon
} from '@heroicons/react/24/outline';

interface AIEngineInfoModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const TabButton: React.FC<{ 
  tab: 'technical' | 'guide'; 
  label: string; 
  icon: React.ComponentType<{ className?: string }>; 
  activeTab: 'technical' | 'guide'; 
  onClick: (tab: 'technical' | 'guide') => void 
}> = ({ tab, label, icon: Icon, activeTab, onClick }) => (
  <button
    onClick={() => onClick(tab)}
    className={`flex items-center justify-center sm:justify-start space-x-2 px-4 py-3 rounded-lg font-medium transition-all duration-200 w-full sm:w-auto ${
      activeTab === tab
        ? 'bg-blue-100 text-blue-700 border-2 border-blue-200 shadow-sm'
        : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50 border-2 border-transparent'
    }`}
  >
    <Icon className="h-5 w-5 flex-shrink-0" />
    <span className="text-sm sm:text-base">{label}</span>
  </button>
);

const TechnicalFeaturesTab: React.FC = () => (
  <div className="space-y-8">
    {/* System Architecture */}
    <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6">
      <div className="flex items-start space-x-3">
        <CpuChipIcon className="h-6 w-6 text-blue-600 mt-1" />
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">System Architecture</h3>
          <p className="text-gray-700 leading-relaxed mb-4">
            Enterprise-grade AI survey generation powered by GPT-5 with advanced RAG retrieval and real-time orchestration.
          </p>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <h4 className="font-semibold text-gray-900 mb-2">AI & Processing</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• GPT-5 via Replicate API for generation</li>
                <li>• LangGraph workflow orchestration (7-node state graph)</li>
                <li>• Sentence Transformers for embeddings (all-MiniLM-L6-v2)</li>
                <li>• WebSocket real-time progress tracking</li>
              </ul>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <h4 className="font-semibold text-gray-900 mb-2">Data & Storage</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• PostgreSQL + pgvector for vector similarity search</li>
                <li>• Redis for caching (graceful fallback)</li>
                <li>• 24 service classes in backend</li>
                <li>• 16 API routers with RESTful endpoints</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>

    {/* Multi-Level RAG System */}
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-center space-x-3 mb-4">
        <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
          <SparklesIcon className="h-5 w-5 text-purple-600" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900">Multi-Level RAG System</h3>
      </div>
      <div className="grid md:grid-cols-3 gap-4">
        <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
          <div className="flex items-center space-x-2 mb-2">
            <div className="w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center">
              <span className="text-xs font-bold text-purple-600">1</span>
            </div>
            <h4 className="font-semibold text-gray-900">Tier 1: Golden Pairs</h4>
          </div>
          <p className="text-sm text-gray-600">
            Complete RFQ-Survey pairs with semantic similarity + methodology matching. Highest priority for retrieval.
          </p>
        </div>
        <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
          <div className="flex items-center space-x-2 mb-2">
            <div className="w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center">
              <span className="text-xs font-bold text-purple-600">2</span>
            </div>
            <h4 className="font-semibold text-gray-900">Tier 2: Golden Sections</h4>
          </div>
          <p className="text-sm text-gray-600">
            Extracted sections from high-quality surveys with methodology tags and industry keywords.
          </p>
        </div>
        <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
          <div className="flex items-center space-x-2 mb-2">
            <div className="w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center">
              <span className="text-xs font-bold text-purple-600">3</span>
            </div>
            <h4 className="font-semibold text-gray-900">Tier 3: Golden Questions</h4>
          </div>
          <p className="text-sm text-gray-600">
            Individual question templates with pattern matching and quality scoring.
          </p>
        </div>
      </div>
    </div>

    {/* 5-Pillar Evaluation Framework */}
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-center space-x-3 mb-4">
        <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
          <ChartPieIcon className="h-5 w-5 text-green-600" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900">5-Pillar Evaluation Framework</h3>
      </div>
      <div className="grid md:grid-cols-5 gap-4">
        <div className="text-center">
          <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
            <span className="text-sm font-bold text-green-600">20%</span>
          </div>
          <h4 className="font-semibold text-gray-900 text-sm">Content Validity</h4>
          <p className="text-xs text-gray-600">Research objective coverage</p>
        </div>
        <div className="text-center">
          <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
            <span className="text-sm font-bold text-green-600">25%</span>
          </div>
          <h4 className="font-semibold text-gray-900 text-sm">Methodological Rigor</h4>
          <p className="text-xs text-gray-600">Research best practices</p>
        </div>
        <div className="text-center">
          <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
            <span className="text-sm font-bold text-green-600">25%</span>
          </div>
          <h4 className="font-semibold text-gray-900 text-sm">Clarity & Comprehensibility</h4>
          <p className="text-xs text-gray-600">Question clarity</p>
        </div>
        <div className="text-center">
          <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
            <span className="text-sm font-bold text-green-600">20%</span>
          </div>
          <h4 className="font-semibold text-gray-900 text-sm">Structural Coherence</h4>
          <p className="text-xs text-gray-600">Survey organization</p>
        </div>
        <div className="text-center">
          <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
            <span className="text-sm font-bold text-green-600">10%</span>
          </div>
          <h4 className="font-semibold text-gray-900 text-sm">Deployment Readiness</h4>
          <p className="text-xs text-gray-600">Ready to deploy</p>
        </div>
      </div>
    </div>

    {/* Advanced Features */}
    <div className="grid md:grid-cols-2 gap-6">
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
            <BeakerIcon className="h-5 w-5 text-orange-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Annotation & Feedback</h3>
        </div>
        <ul className="text-sm text-gray-600 space-y-2">
          <li>• Multi-level annotations (Survey, Section, Question)</li>
          <li>• AI-powered annotation service with confidence scoring</li>
          <li>• Annotation → RAG sync (feedback loop)</li>
          <li>• Annotation Insights Dashboard</li>
        </ul>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center">
            <DocumentCheckIcon className="h-5 w-5 text-indigo-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">QNR Labeling System</h3>
        </div>
        <ul className="text-sm text-gray-600 space-y-2">
          <li>• 7-section structure with mandatory labels</li>
          <li>• Deterministic pattern matching</li>
          <li>• Methodology-specific label detection</li>
          <li>• Quality regression tracking</li>
        </ul>
      </div>
    </div>

    {/* Additional Features */}
    <div className="bg-gray-50 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
        <AdjustmentsHorizontalIcon className="h-5 w-5 text-gray-600" />
        <span>Additional Capabilities</span>
      </h3>
      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <h4 className="font-semibold text-gray-900 mb-2">Document Intelligence</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• Advanced .docx parsing with field extraction</li>
            <li>• AI-powered RFQ auto-generation from surveys</li>
            <li>• Intelligent field extraction service</li>
            <li>• Document upload workflow with cancellation</li>
          </ul>
        </div>
        <div>
          <h4 className="font-semibold text-gray-900 mb-2">Monitoring & Analytics</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• LLM audit tracking (tokens, costs, latency)</li>
            <li>• Human-in-the-loop prompt review</li>
            <li>• Export system (DOCX/PDF with structured rendering)</li>
            <li>• Real-time WebSocket progress updates</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
);

const ResearchersGuideTab: React.FC = () => (
  <div className="space-y-8">
    {/* Getting Started */}
    <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-6">
      <div className="flex items-start space-x-3">
        <AcademicCapIcon className="h-6 w-6 text-green-600 mt-1" />
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Getting Started</h3>
          <p className="text-gray-700 leading-relaxed mb-4">
            Follow these steps to maximize survey generation quality and system learning.
          </p>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                <DocumentTextIcon className="h-4 w-4 text-blue-600 mr-2" />
                1. Input High-Quality RFQs
              </h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Upload detailed DOCX documents</li>
                <li>• Use Enhanced RFQ Editor for structured input</li>
                <li>• Fill in industry, methodology, target segments</li>
                <li>• Include specific research objectives</li>
              </ul>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                <SparklesIcon className="h-4 w-4 text-purple-600 mr-2" />
                2. Create Golden Examples
              </h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Upload your best survey .docx files</li>
                <li>• Use AI field extraction for metadata</li>
                <li>• Add methodology tags consistently</li>
                <li>• Mark as verified for priority retrieval</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>

    {/* Golden Examples - Most Important */}
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
      <div className="flex items-center space-x-3 mb-4">
        <div className="w-8 h-8 bg-yellow-100 rounded-lg flex items-center justify-center">
          <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900">Creating Golden Examples (Most Important)</h3>
      </div>
      <div className="bg-white rounded-lg p-4 border border-yellow-200">
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-semibold text-gray-900 mb-3">Step-by-Step Process:</h4>
            <ol className="text-sm text-gray-700 space-y-2">
              <li className="flex items-start">
                <span className="bg-yellow-100 text-yellow-800 text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center mr-3 mt-0.5">1</span>
                Upload your best survey .docx files via Golden Examples page
              </li>
              <li className="flex items-start">
                <span className="bg-yellow-100 text-yellow-800 text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center mr-3 mt-0.5">2</span>
                Use AI field extraction to auto-populate metadata
              </li>
              <li className="flex items-start">
                <span className="bg-yellow-100 text-yellow-800 text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center mr-3 mt-0.5">3</span>
                Add methodology tags (Van Westendorp, MaxDiff, etc.)
              </li>
              <li className="flex items-start">
                <span className="bg-yellow-100 text-yellow-800 text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center mr-3 mt-0.5">4</span>
                Set industry classification and research goal
              </li>
              <li className="flex items-start">
                <span className="bg-yellow-100 text-yellow-800 text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center mr-3 mt-0.5">5</span>
                Mark as verified to boost retrieval priority
              </li>
            </ol>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-3">Best Practices:</h4>
            <ul className="text-sm text-gray-700 space-y-2">
              <li className="flex items-start">
                <CheckCircleIcon className="h-4 w-4 text-green-500 mr-2 mt-0.5" />
                Aim for 10+ golden examples per methodology type
              </li>
              <li className="flex items-start">
                <CheckCircleIcon className="h-4 w-4 text-green-500 mr-2 mt-0.5" />
                Use consistent methodology tags across examples
              </li>
              <li className="flex items-start">
                <CheckCircleIcon className="h-4 w-4 text-green-500 mr-2 mt-0.5" />
                Include diverse industry examples
              </li>
              <li className="flex items-start">
                <CheckCircleIcon className="h-4 w-4 text-green-500 mr-2 mt-0.5" />
                Quality over quantity - only upload excellent surveys
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    {/* Improving Survey Quality */}
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-center space-x-3 mb-4">
        <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
          <ChartBarIcon className="h-5 w-5 text-blue-600" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900">Improving Survey Quality</h3>
      </div>
      <div className="grid md:grid-cols-3 gap-4">
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <h4 className="font-semibold text-gray-900 mb-2">Review & Edit</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• Review AI-generated surveys carefully</li>
            <li>• Edit questions for clarity and accuracy</li>
            <li>• Adjust question order and flow</li>
            <li>• Validate methodology compliance</li>
          </ul>
        </div>
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <h4 className="font-semibold text-gray-900 mb-2">Add Annotations</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• Rate question quality (1-5 scale)</li>
            <li>• Add methodology labels</li>
            <li>• Mark questions as verified</li>
            <li>• Annotations feed back into RAG</li>
          </ul>
        </div>
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <h4 className="font-semibold text-gray-900 mb-2">Track Progress</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• Use Annotation Insights Dashboard</li>
            <li>• Monitor pillar scores over time</li>
            <li>• Review LLM audit for costs</li>
            <li>• Adjust settings based on results</li>
          </ul>
        </div>
      </div>
    </div>

    {/* Managing Rules */}
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-center space-x-3 mb-4">
        <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
          <CogIcon className="h-5 w-5 text-purple-600" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900">Managing Rules</h3>
      </div>
      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <h4 className="font-semibold text-gray-900 mb-2">Methodology Rules</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• Add Van Westendorp pricing study rules</li>
            <li>• Configure MaxDiff methodology requirements</li>
            <li>• Set up conjoint analysis guidelines</li>
            <li>• Define brand tracking standards</li>
          </ul>
        </div>
        <div>
          <h4 className="font-semibold text-gray-900 mb-2">Quality Rules</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• Create pillar-based quality rules</li>
            <li>• Customize system prompts for your style</li>
            <li>• Set industry-specific requirements</li>
            <li>• Rules apply during generation & validation</li>
          </ul>
        </div>
      </div>
    </div>

    {/* Understanding the Workflow */}
    <div className="bg-gray-50 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
        <ArrowRightIcon className="h-5 w-5 text-gray-600" />
        <span>Understanding the Workflow</span>
      </h3>
      <div className="grid md:grid-cols-7 gap-2">
        <div className="text-center">
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
            <span className="text-xs font-bold text-blue-600">1</span>
          </div>
          <h4 className="font-semibold text-gray-900 text-xs">RFQ Parsing</h4>
          <p className="text-xs text-gray-600">Extract & embed</p>
        </div>
        <div className="text-center">
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
            <span className="text-xs font-bold text-blue-600">2</span>
          </div>
          <h4 className="font-semibold text-gray-900 text-xs">Golden Retrieval</h4>
          <p className="text-xs text-gray-600">3-tier RAG</p>
        </div>
        <div className="text-center">
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
            <span className="text-xs font-bold text-blue-600">3</span>
          </div>
          <h4 className="font-semibold text-gray-900 text-xs">Context Building</h4>
          <p className="text-xs text-gray-600">Rules & examples</p>
        </div>
        <div className="text-center">
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
            <span className="text-xs font-bold text-blue-600">4</span>
          </div>
          <h4 className="font-semibold text-gray-900 text-xs">GPT-5 Generation</h4>
          <p className="text-xs text-gray-600">Enhanced prompts</p>
        </div>
        <div className="text-center">
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
            <span className="text-xs font-bold text-blue-600">5</span>
          </div>
          <h4 className="font-semibold text-gray-900 text-xs">5-Pillar Evaluation</h4>
          <p className="text-xs text-gray-600">Quality assessment</p>
        </div>
        <div className="text-center">
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
            <span className="text-xs font-bold text-blue-600">6</span>
          </div>
          <h4 className="font-semibold text-gray-900 text-xs">Label Detection</h4>
          <p className="text-xs text-gray-600">QNR taxonomy</p>
        </div>
        <div className="text-center">
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
            <span className="text-xs font-bold text-blue-600">7</span>
          </div>
          <h4 className="font-semibold text-gray-900 text-xs">Export Ready</h4>
          <p className="text-xs text-gray-600">DOCX/PDF</p>
        </div>
      </div>
    </div>

    {/* Call to Action */}
    <div className="bg-gradient-to-r from-green-600 to-blue-600 rounded-lg p-6 text-white">
      <h3 className="text-lg font-semibold mb-2">Start Building Better Surveys Today!</h3>
      <p className="text-green-100 mb-4">
        The more you use the system and create golden examples, the better it becomes at understanding your specific research needs.
      </p>
      <div className="flex flex-wrap gap-2">
        <span className="bg-white bg-opacity-20 px-3 py-1 rounded-full text-sm">
          Upload DOCX files
        </span>
        <span className="bg-white bg-opacity-20 px-3 py-1 rounded-full text-sm">
          Create Golden Examples
        </span>
        <span className="bg-white bg-opacity-20 px-3 py-1 rounded-full text-sm">
          Add Annotations
        </span>
        <span className="bg-white bg-opacity-20 px-3 py-1 rounded-full text-sm">
          Monitor Quality
        </span>
      </div>
    </div>
  </div>
);

const AIEngineInfoModal: React.FC<AIEngineInfoModalProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<'technical' | 'guide'>('technical');
  
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-xl">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <DocumentTextIcon className="h-6 w-6 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">AI Survey Engine</h2>
                <p className="text-sm text-gray-500">v1.0.0 - Intelligent Learning System</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <XMarkIcon className="h-6 w-6 text-gray-500" />
            </button>
          </div>
          
          {/* Tab Navigation */}
          <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
            <TabButton
              tab="technical"
              label="Technical Features"
              icon={CpuChipIcon}
              activeTab={activeTab}
              onClick={setActiveTab}
            />
            <TabButton
              tab="guide"
              label="Researcher's Guide"
              icon={AcademicCapIcon}
              activeTab={activeTab}
              onClick={setActiveTab}
            />
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-6 max-h-[60vh] overflow-y-auto">
          <div className={`transition-all duration-300 ease-in-out ${activeTab === 'technical' ? 'opacity-100' : 'opacity-0 hidden'}`}>
            {activeTab === 'technical' && <TechnicalFeaturesTab />}
          </div>
          <div className={`transition-all duration-300 ease-in-out ${activeTab === 'guide' ? 'opacity-100' : 'opacity-0 hidden'}`}>
            {activeTab === 'guide' && <ResearchersGuideTab />}
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 rounded-b-xl">
          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
            >
              Got it, let's start!
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIEngineInfoModal;


