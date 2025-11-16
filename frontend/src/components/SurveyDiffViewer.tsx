import React, { useState, useMemo, useCallback } from 'react';
import { SurveyDiff } from '../types';
import { 
  ChevronDownIcon, 
  ChevronRightIcon, 
  PlusIcon, 
  MinusIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

interface SurveyDiffViewerProps {
  diff: SurveyDiff;
  onClose?: () => void;
  isModal?: boolean;
}

export const SurveyDiffViewer: React.FC<SurveyDiffViewerProps> = ({ 
  diff, 
  onClose,
  isModal = false 
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<number>>(new Set());
  const [showOnlyChanges, setShowOnlyChanges] = useState(false);
  const [showOnlyCommentChanges, setShowOnlyCommentChanges] = useState(false);

  // State for annotation comments
  const [annotationComments, setAnnotationComments] = React.useState<Record<string, string>>({});
  const [loadingAnnotations, setLoadingAnnotations] = React.useState(false);

  // Fetch actual annotation comments
  React.useEffect(() => {
    const fetchAnnotations = async () => {
      if (loadingAnnotations) return;
      
      console.log('🔍 Attempting to fetch annotations...');
      console.log('🔍 Survey1 (new):', diff.survey1_info.id, 'v' + diff.survey1_info.version);
      console.log('🔍 Survey2 (old):', diff.survey2_info.id, 'v' + diff.survey2_info.version);
      console.log('🔍 Comment IDs to match:', diff.survey1_info.comments_addressed);
      
      try {
        setLoadingAnnotations(true);
        
        // Try multiple survey IDs - annotations might be on parent versions
        const surveyIdsToTry = [
          diff.survey2_info.id, 
          diff.survey1_info.id
        ];
        
        // Also try to get parent survey IDs from the current survey
        try {
          const currentSurveyResponse = await fetch(`http://localhost:8000/api/v1/surveys/${diff.survey1_info.id}`);
          if (currentSurveyResponse.ok) {
            const currentSurveyData = await currentSurveyResponse.json();
            if (currentSurveyData.parent_survey_id) {
              console.log('🔍 Found parent survey ID:', currentSurveyData.parent_survey_id);
              surveyIdsToTry.push(currentSurveyData.parent_survey_id);
            }
            if (currentSurveyData.parentSurveyId) {
              console.log('🔍 Found parentSurveyId:', currentSurveyData.parentSurveyId);
              surveyIdsToTry.push(currentSurveyData.parentSurveyId);
            }
          }
        } catch (e) {
          console.log('Could not fetch parent survey info');
        }
        
        console.log('🔍 Will try these survey IDs:', surveyIdsToTry);
        let foundAnnotations = false;
        
        for (const surveyId of surveyIdsToTry) {
          const url = `/api/v1/surveys/${surveyId}/annotations`;
          console.log('🔍 Trying URL:', url);
          
          const response = await fetch(url);
          console.log('📡 Response status:', response.status);
          
          if (response.ok) {
            const data = await response.json();
            console.log('✅ Found annotations data:', data);
            
            // Map comment IDs to comment text
            const commentMap: Record<string, string> = {};
            
            // Question annotations
            if (data.question_annotations && data.question_annotations.length > 0) {
              console.log('📝 Processing', data.question_annotations.length, 'question annotations');
              data.question_annotations.forEach((ann: any) => {
                // Try multiple version formats
                const versions = [diff.survey2_info.version, diff.survey1_info.version, 1];
                versions.forEach(v => {
                  const commentId = `COMMENT-Q${ann.question_id}-V${v}`;
                  const commentText = ann.comment_text || ann.comment || '';
                  if (commentText) {
                    console.log(`  → ${commentId}: "${commentText.substring(0, 50)}..."`);
                    commentMap[commentId] = commentText;
                  }
                });
              });
            }
            
            // Section annotations
            if (data.section_annotations && data.section_annotations.length > 0) {
              console.log('📋 Processing', data.section_annotations.length, 'section annotations');
              data.section_annotations.forEach((ann: any) => {
                const versions = [diff.survey2_info.version, diff.survey1_info.version, 1];
                versions.forEach(v => {
                  const commentId = `COMMENT-S${ann.section_id}-V${v}`;
                  const commentText = ann.comment_text || ann.comment || '';
                  if (commentText) {
                    console.log(`  → ${commentId}: "${commentText.substring(0, 50)}..."`);
                    commentMap[commentId] = commentText;
                  }
                });
              });
            }
            
            // Survey annotations
            if (data.survey_annotations && data.survey_annotations.length > 0) {
              console.log('📄 Processing', data.survey_annotations.length, 'survey annotations');
              data.survey_annotations.forEach((ann: any) => {
                const versions = [diff.survey2_info.version, diff.survey1_info.version, 1];
                versions.forEach(v => {
                  const commentId = `COMMENT-SURVEY-V${v}`;
                  const commentText = ann.comment_text || ann.comment || '';
                  if (commentText) {
                    console.log(`  → ${commentId}: "${commentText.substring(0, 50)}..."`);
                    commentMap[commentId] = commentText;
                  }
                });
              });
            }
            
            if (Object.keys(commentMap).length > 0) {
              console.log('✅ Successfully mapped', Object.keys(commentMap).length, 'comments');
              console.log('✅ Comment map keys:', Object.keys(commentMap));
              setAnnotationComments(commentMap);
              foundAnnotations = true;
              break; // Found annotations, stop trying
            }
          }
        }
        
        if (!foundAnnotations) {
          console.warn('⚠️ No annotations found for either survey version');
        }
      } catch (error) {
        console.error('❌ Error fetching annotations:', error);
      } finally {
        setLoadingAnnotations(false);
      }
    };
    
    fetchAnnotations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [diff.survey1_info?.id, diff.survey2_info?.id]);

  const toggleSection = (sectionId: number) => {
    setExpandedSections(prev => {
      const next = new Set(prev);
      if (next.has(sectionId)) {
        next.delete(sectionId);
      } else {
        next.add(sectionId);
      }
      return next;
    });
  };

  // Group questions by section
  const questionsBySection = useMemo(() => {
    const grouped: Record<number, typeof diff.questions> = {};
    diff.questions.forEach(q => {
      const sectionId = q.section_id || 0;
      if (!grouped[sectionId]) {
        grouped[sectionId] = [];
      }
      grouped[sectionId].push(q);
    });
    return grouped;
  }, [diff]);

  // Build mapping of comment IDs to question/section IDs for filtering
  // Use linked_question data when available (more reliable), fall back to parsing comment IDs
  const commentDrivenChanges = useMemo(() => {
    const commentQuestionIds = new Set<string>();
    const commentSectionIds = new Set<number>();
    
    // First, use linked_question data from comment_action_status (most reliable)
    if (diff.comment_action_status?.addressed_comments) {
      diff.comment_action_status.addressed_comments.forEach((comment) => {
        // If we have a linked question, use its ID directly
        if (comment.linked_question?.id) {
          commentQuestionIds.add(comment.linked_question.id);
        }
        // Also track section-level comments
        if (comment.section_id) {
          commentSectionIds.add(comment.section_id);
        }
      });
    }
    
    // Fallback: Parse comment IDs if comment_action_status is not available
    if (commentQuestionIds.size === 0 && diff.survey1_info.comments_addressed) {
      diff.survey1_info.comments_addressed.forEach((commentId: string) => {
        // Parse COMMENT-Q{question_id}-V{version} or COMMENT-S{section_id}-V{version}
        if (commentId.startsWith('COMMENT-Q')) {
          const match = commentId.match(/COMMENT-Q([^-]+)-/);
          if (match) {
            const oldQuestionId = match[1];
            // Try to find the new question ID by matching old question ID in the diff
            diff.questions.forEach((q) => {
              // Check if this question was modified and the old question ID matches
              if (q.status === 'modified' && q.question2?.id === oldQuestionId) {
                commentQuestionIds.add(q.question1?.id || q.id);
              }
              // Check if this question was added (might be related to the comment)
              // We'll be conservative and only match if we can find a direct link
            });
          }
        } else if (commentId.startsWith('COMMENT-S') && !commentId.startsWith('COMMENT-SURVEY')) {
          const match = commentId.match(/COMMENT-S(\d+)-/);
          if (match) {
            commentSectionIds.add(parseInt(match[1]));
          }
        }
      });
    }
    
    return { questionIds: commentQuestionIds, sectionIds: commentSectionIds };
  }, [diff.comment_action_status, diff.survey1_info.comments_addressed, diff.questions]);

  // Check if a question was changed due to comments
  // Check both the question.id and question.question1?.id (for added/modified questions)
  const isCommentDriven = useCallback((question: { id: string; question1?: { id?: string } | null }) => {
    const questionId = question.id;
    const newQuestionId = question.question1?.id;
    return commentDrivenChanges.questionIds.has(questionId) || 
           (newQuestionId && commentDrivenChanges.questionIds.has(newQuestionId));
  }, [commentDrivenChanges]);

  // Get comments associated with a question
  const getQuestionComments = useCallback((question: { id: string; question1?: { id?: string } | null; question2?: { id?: string } | null }) => {
    const comments: Array<{ comment_text: string; comment_id: string }> = [];
    
    // First try: Check if comment_action_status has full comment data
    if (diff.comment_action_status?.addressed_comments) {
      const questionId = question.id;
      const newQuestionId = question.question1?.id;
      const oldQuestionId = question.question2?.id;
      
      const matchingComments = diff.comment_action_status.addressed_comments.filter(comment => {
        const linkedId = comment.linked_question?.id;
        return linkedId === questionId || 
               linkedId === newQuestionId || 
               linkedId === oldQuestionId ||
               comment.question_id === questionId ||
               comment.question_id === newQuestionId ||
               comment.question_id === oldQuestionId;
      });
      
      if (matchingComments.length > 0) {
        return matchingComments.map(c => ({
          comment_text: c.comment_text || 'No comment text',
          comment_id: c.comment_id
        }));
      }
    }
    
    // Second try: Use fetched annotations to match comment IDs
    if (diff.survey1_info.comments_addressed && annotationComments) {
      const oldQuestionId = question.question2?.id;
      
      diff.survey1_info.comments_addressed.forEach(commentId => {
        // Check if this comment ID matches this question
        if (commentId.includes(`-Q${oldQuestionId}-`)) {
          const commentText = annotationComments[commentId];
          if (commentText) {
            comments.push({ comment_text: commentText, comment_id: commentId });
          }
        }
      });
    }
    
    return comments;
  }, [diff.comment_action_status, diff.survey1_info.comments_addressed, annotationComments]);

  // Get comments associated with a section
  const getSectionComments = useCallback((sectionId: number) => {
    const comments: Array<{ comment_text: string; comment_id: string }> = [];
    
    // First try: Check if comment_action_status has full comment data
    if (diff.comment_action_status?.addressed_comments) {
      const matchingComments = diff.comment_action_status.addressed_comments.filter(comment => {
        return comment.section_id === sectionId;
      });
      
      if (matchingComments.length > 0) {
        return matchingComments.map(c => ({
          comment_text: c.comment_text || 'No comment text',
          comment_id: c.comment_id
        }));
      }
    }
    
    // Second try: Use fetched annotations to match comment IDs
    if (diff.survey1_info.comments_addressed && annotationComments) {
      diff.survey1_info.comments_addressed.forEach(commentId => {
        // Check if this comment ID matches this section (COMMENT-S{section_id}-V{version})
        if (commentId.includes(`-S${sectionId}-`)) {
          const commentText = annotationComments[commentId];
          if (commentText) {
            comments.push({ comment_text: commentText, comment_id: commentId });
          }
        }
      });
    }
    
    return comments;
  }, [diff.comment_action_status, diff.survey1_info.comments_addressed, annotationComments]);

  // Filter sections/questions if showOnlyChanges is true
  const visibleSections = useMemo(() => {
    if (!showOnlyChanges && !showOnlyCommentChanges) return diff.sections;
    if (showOnlyCommentChanges) {
      // Show only sections that have comment-driven changes
      return diff.sections.filter(s => {
        // Check if section itself was commented on
        if (commentDrivenChanges.sectionIds.has(s.id)) return true;
        // Check if any question in this section is comment-driven
        const sectionQuestions = questionsBySection[s.id] || [];
        return sectionQuestions.some(q => isCommentDriven(q));
      });
    }
    return diff.sections.filter(s => s.status !== 'preserved');
  }, [diff.sections, showOnlyChanges, showOnlyCommentChanges, commentDrivenChanges, questionsBySection, isCommentDriven]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'added':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'removed':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'modified':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'preserved':
        return 'bg-gray-50 border-gray-200 text-gray-600';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'added':
        return <PlusIcon className="w-4 h-4 text-green-600" />;
      case 'removed':
        return <MinusIcon className="w-4 h-4 text-red-600" />;
      case 'modified':
        return <ArrowPathIcon className="w-4 h-4 text-yellow-600" />;
      default:
        return null;
    }
  };

  const renderQuestionDiff = (question: typeof diff.questions[0]) => {
    const hasComment = isCommentDriven(question);
    const comments = getQuestionComments(question);
    
    if (question.status === 'added') {
      return (
        <div className={`border-l-4 ${hasComment ? 'border-purple-500' : 'border-green-500'} ${getStatusColor(question.status)}`}>
          {/* Comment Display */}
          {hasComment && (
            <div className="p-4 bg-purple-50 border-b border-purple-200">
              {comments.length > 0 ? (
                comments.map((comment, idx) => (
                  <div key={idx} className="mb-3 last:mb-0">
                    <div className="flex items-start gap-3">
                      <span className="text-purple-600 text-xl mt-0.5">💬</span>
                      <div className="flex-1">
                        <div className="text-xs font-semibold text-purple-900 mb-2 uppercase tracking-wide">Annotation Comment:</div>
                        <div className="text-sm text-gray-800 bg-white p-3 rounded-lg border border-purple-300 shadow-sm leading-relaxed">
                          {comment.comment_text}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="flex items-start gap-3">
                  <span className="text-purple-600 text-xl mt-0.5">💬</span>
                  <div className="flex-1">
                    <div className="text-xs font-semibold text-purple-900 mb-1">Modified based on annotation feedback</div>
                    <div className="text-xs text-purple-700 italic">
                      This question was added in response to annotations, but the original comment text is not available.
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
          
          <div className="grid grid-cols-2 gap-4 p-3">
            {/* Left side - Empty for added questions */}
            <div className="text-sm text-gray-400 italic flex items-center justify-center">
              (New question)
            </div>
            
            {/* Right side - New question */}
            <div className="bg-green-50 border border-green-200 rounded p-3">
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 flex-shrink-0">
                  Added
                </span>
                {hasComment && (
                  <span className="px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800 flex-shrink-0" title="Changed due to comment feedback">
                    💬 Comment
                  </span>
                )}
              </div>
              <div className="font-medium text-gray-900">{question.question1?.text || 'New question'}</div>
              {question.question1?.type && (
                <div className="text-xs text-gray-600 mt-2">
                  <span className="font-medium">Type:</span> {question.question1.type}
                </div>
              )}
              {question.question1?.options && question.question1.options.length > 0 && (
                <div className="text-xs text-gray-600 mt-2">
                  <div className="font-medium mb-1">Options:</div>
                  <ul className="list-disc list-inside space-y-0.5 ml-2">
                    {question.question1.options.map((option, idx) => (
                      <li key={idx}>{option}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      );
    }

    if (question.status === 'removed') {
      return (
        <div className={`border-l-4 border-red-500 ${getStatusColor(question.status)}`}>
          <div className="grid grid-cols-2 gap-4 p-3">
            {/* Left side - Old question */}
            <div className="bg-red-50 border border-red-200 rounded p-3">
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className="px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800 flex-shrink-0">
                  Removed
                </span>
              </div>
              <div className="font-medium text-gray-600 line-through">{question.question2?.text || 'Removed question'}</div>
              {question.question2?.type && (
                <div className="text-xs text-gray-600 mt-2">
                  <span className="font-medium">Type:</span> {question.question2.type}
                </div>
              )}
              {question.question2?.options && question.question2.options.length > 0 && (
                <div className="text-xs text-gray-600 mt-2">
                  <div className="font-medium mb-1">Options:</div>
                  <ul className="list-disc list-inside space-y-0.5 ml-2">
                    {question.question2.options.map((option, idx) => (
                      <li key={idx}>{option}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            
            {/* Right side - Empty for removed questions */}
            <div className="text-sm text-gray-400 italic flex items-center justify-center">
              (Question removed)
            </div>
          </div>
        </div>
      );
    }

    if (question.status === 'modified') {
      return (
        <div className={`border-l-4 ${hasComment ? 'border-purple-500' : 'border-yellow-500'} ${getStatusColor(question.status)}`}>
          {/* Comment Display */}
          {hasComment && (
            <div className="p-4 bg-purple-50 border-b border-purple-200">
              {comments.length > 0 ? (
                comments.map((comment, idx) => (
                  <div key={idx} className="mb-3 last:mb-0">
                    <div className="flex items-start gap-3">
                      <span className="text-purple-600 text-xl mt-0.5">💬</span>
                      <div className="flex-1">
                        <div className="text-xs font-semibold text-purple-900 mb-2 uppercase tracking-wide">Annotation Comment:</div>
                        <div className="text-sm text-gray-800 bg-white p-3 rounded-lg border border-purple-300 shadow-sm leading-relaxed">
                          {comment.comment_text}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="flex items-start gap-3">
                  <span className="text-purple-600 text-xl mt-0.5">💬</span>
                  <div className="flex-1">
                    <div className="text-xs font-semibold text-purple-900 mb-1">Modified based on annotation feedback</div>
                    <div className="text-xs text-purple-700 italic">
                      This question was modified in response to annotations, but the original comment text is not available.
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
          
          <div className="grid grid-cols-2 gap-4 p-3">
            {/* Left side - Old question */}
            <div className="bg-gray-50 border border-gray-300 rounded p-3">
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-200 text-gray-700 flex-shrink-0">
                  Before
                </span>
              </div>
              <div className="font-medium text-gray-600">{question.question2?.text || 'Old question'}</div>
              {question.question2?.type && (
                <div className="text-xs text-gray-600 mt-2">
                  <span className="font-medium">Type:</span> {question.question2.type}
                </div>
              )}
              {question.question2?.options && question.question2.options.length > 0 && (
                <div className="text-xs text-gray-600 mt-2">
                  <div className="font-medium mb-1">Options:</div>
                  <ul className="list-disc list-inside space-y-0.5 ml-2">
                    {question.question2.options.map((option, idx) => (
                      <li key={idx}>{option}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            
            {/* Right side - New question */}
            <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className="px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800 flex-shrink-0">
                  Modified
                </span>
                {hasComment && (
                  <span className="px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800 flex-shrink-0" title="Changed due to comment feedback">
                    💬 Comment
                  </span>
                )}
              </div>
              <div className="font-medium text-gray-900">{question.question1?.text || 'New question'}</div>
              {question.question1?.type && (
                <div className="text-xs text-gray-600 mt-2">
                  <span className="font-medium">Type:</span> {question.question1.type}
                </div>
              )}
              {question.question1?.options && question.question1.options.length > 0 && (
                <div className="text-xs text-gray-600 mt-2">
                  <div className="font-medium mb-1">Options:</div>
                  <ul className="list-disc list-inside space-y-0.5 ml-2">
                    {question.question1.options.map((option, idx) => (
                      <li key={idx}>{option}</li>
                    ))}
                  </ul>
                </div>
              )}
              {question.changes.length > 0 && (
                <div className="text-xs text-blue-600 mt-2">
                  <span className="font-medium">Changes:</span> {question.changes.join(', ')}
                </div>
              )}
              {question.similarity !== null && question.similarity !== undefined && (
                <div className="text-xs text-gray-500 mt-1">
                  Similarity: {(question.similarity * 100).toFixed(1)}%
                </div>
              )}
            </div>
          </div>
        </div>
      );
    }

    // Preserved
    return (
      <div className={`border-l-4 border-gray-300 ${getStatusColor(question.status)}`}>
        <div className="grid grid-cols-2 gap-4 p-3">
          <div className="text-sm text-gray-600">
            {question.question2?.text || 'Question'}
          </div>
          <div className="text-sm text-gray-600">
            {question.question1?.text || question.question2?.text || 'Question'}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 z-[9999] w-full h-screen flex flex-col bg-gray-50">
      {/* Header with Back button */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all duration-200 group"
              >
                <svg className="h-5 w-5 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
            )}
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Survey Comparison</h1>
              <div className="text-sm text-gray-500 mt-1">
                {diff.survey1_info.title} (v{diff.survey1_info.version}) vs {diff.survey2_info.title} (v{diff.survey2_info.version})
              </div>
            </div>
          </div>

          {/* Summary Stats */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-2 bg-green-50 rounded-lg border border-green-200">
              <PlusIcon className="w-4 h-4 text-green-600" />
              <span className="text-lg font-bold text-green-600">{diff.summary.questions_added}</span>
              <span className="text-xs text-green-700">Added</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-2 bg-yellow-50 rounded-lg border border-yellow-200">
              <ArrowPathIcon className="w-4 h-4 text-yellow-600" />
              <span className="text-lg font-bold text-yellow-600">{diff.summary.questions_modified}</span>
              <span className="text-xs text-yellow-700">Modified</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-2 bg-red-50 rounded-lg border border-red-200">
              <MinusIcon className="w-4 h-4 text-red-600" />
              <span className="text-lg font-bold text-red-600">{diff.summary.questions_removed}</span>
              <span className="text-xs text-red-700">Removed</span>
            </div>
          </div>
        </div>

        {/* Regeneration Metadata */}
        {diff.regeneration_metadata && (
          <div className="mt-3 p-2 bg-purple-50 border border-purple-200 rounded">
            <div className="text-xs font-medium text-purple-900">
              Surgical Regeneration: Sections {diff.regeneration_metadata.sections_regenerated.join(', ')}
              {diff.regeneration_metadata.sections_preserved.length > 0 && (
                <> • Preserved: {diff.regeneration_metadata.sections_preserved.join(', ')}</>
              )}
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="mt-3 flex items-center gap-4 flex-wrap">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={showOnlyChanges}
              onChange={(e) => {
                setShowOnlyChanges(e.target.checked);
                if (e.target.checked) setShowOnlyCommentChanges(false);
              }}
              className="rounded border-gray-300"
            />
            <span>Show only changes</span>
          </label>
          {(diff.survey1_info.comments_addressed && diff.survey1_info.comments_addressed.length > 0) && (
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={showOnlyCommentChanges}
                onChange={(e) => {
                  setShowOnlyCommentChanges(e.target.checked);
                  if (e.target.checked) setShowOnlyChanges(false);
                }}
                className="rounded border-gray-300"
              />
              <span className="flex items-center gap-1">
                <svg className="w-4 h-4 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                Show only comment-driven changes
              </span>
            </label>
          )}
        </div>

        {/* Column Headers */}
        <div className="mt-4 grid grid-cols-2 gap-4 px-4">
          <div className="text-center font-semibold text-gray-700 text-sm">
            Previous Version (v{diff.survey2_info.version})
          </div>
          <div className="text-center font-semibold text-gray-700 text-sm">
            Current Version (v{diff.survey1_info.version})
          </div>
        </div>
      </div>

      {/* Changes Content */}
      <div className="flex-1 overflow-y-auto bg-white">
        <div className="p-6">
          {/* Sections */}
          <div className="space-y-4">
            {visibleSections.map(section => {
              const sectionQuestions = questionsBySection[section.id] || [];
              let visibleQuestions = showOnlyChanges
                ? sectionQuestions.filter(q => q.status !== 'preserved')
                : sectionQuestions;
              
              // Filter to comment-driven changes if enabled
              if (showOnlyCommentChanges) {
                visibleQuestions = visibleQuestions.filter(q => 
                  isCommentDriven(q) || 
                  commentDrivenChanges.sectionIds.has(section.id)
                );
              }
              const isExpanded = expandedSections.has(section.id);

              return (
                <div key={section.id} className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
                  <button
                    onClick={() => toggleSection(section.id)}
                    className="w-full p-4 text-left hover:bg-gray-50 flex items-center justify-between transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      {isExpanded ? (
                        <ChevronDownIcon className="w-5 h-5 text-gray-400" />
                      ) : (
                        <ChevronRightIcon className="w-5 h-5 text-gray-400" />
                      )}
                      <span className="font-semibold text-gray-900">{section.name}</span>
                      {getStatusIcon(section.status)}
                      <span className={`text-xs px-2 py-1 rounded ${getStatusColor(section.status)}`}>
                        {section.status}
                      </span>
                      {/* Show comment badge if section has comment-driven changes */}
                      {(commentDrivenChanges.sectionIds.has(section.id) || 
                        visibleQuestions.some(q => isCommentDriven(q))) && (
                        <span className="px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800" title="Contains comment-driven changes">
                          💬 Comments
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-500">
                      {visibleQuestions.length} question{visibleQuestions.length !== 1 ? 's' : ''}
                      {section.questions_changed > 0 && (
                        <span className="ml-2 text-yellow-600">({section.questions_changed} changed)</span>
                      )}
                      {showOnlyCommentChanges && visibleQuestions.some(q => isCommentDriven(q)) && (
                        <span className="ml-2 text-purple-600">({visibleQuestions.filter(q => isCommentDriven(q)).length} from comments)</span>
                      )}
                    </div>
                  </button>

                  {isExpanded && (
                    <div className="border-t border-gray-200">
                      {/* Section-level comments */}
                      {(() => {
                        const sectionComments = getSectionComments(section.id);
                        if (sectionComments.length > 0) {
                          return (
                            <div className="p-4 bg-purple-50 border-b border-purple-200">
                              <div className="mb-2 text-xs font-semibold text-purple-900 uppercase tracking-wide">
                                📋 Section-Level Annotation Comments:
                              </div>
                              {sectionComments.map((comment, idx) => (
                                <div key={idx} className="mb-3 last:mb-0">
                                  <div className="flex items-start gap-3">
                                    <span className="text-purple-600 text-xl mt-0.5">💬</span>
                                    <div className="flex-1">
                                      <div className="text-sm text-gray-800 bg-white p-3 rounded-lg border border-purple-300 shadow-sm leading-relaxed">
                                        {comment.comment_text}
                                      </div>
                                      <div className="text-xs text-purple-700 mt-1 font-mono">
                                        {comment.comment_id}
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          );
                        }
                        return null;
                      })()}

                      {visibleQuestions.length === 0 ? (
                        <div className="text-sm text-gray-500 text-center py-8">
                          No questions to display
                        </div>
                      ) : (
                        <div className="divide-y divide-gray-200">
                          {visibleQuestions.map((question, idx) => (
                            <div key={`${question.id}-${idx}`}>
                              {renderQuestionDiff(question)}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}

            {/* Error Message */}
            {diff.error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded">
                <div className="text-sm text-red-800">{diff.error}</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

