# Section-Level Comment Display Fix

**Date**: 2024-11-16  
**Issue**: Section-level annotation comments were not being displayed in the survey diff viewer after regeneration

## Problem

After survey regeneration with annotations, the "Show only comment-driven changes" checkbox would not appear if the LLM didn't populate `comments_addressed`. Additionally, even when section-level comments were tracked, they weren't being displayed in the diff viewer UI.

### Symptoms
1. ❌ Checkbox for "Show only comment-driven changes" not appearing
2. ❌ Section-level comments tracked but not displayed
3. ⚠️ Only question-level comments were visible in the diff view

## Root Causes

### Backend Issue
The `comments_addressed` field was only populated if the LLM explicitly included it in the response. If the LLM didn't provide this field, the frontend checkbox wouldn't appear, even though `used_annotation_comment_ids` contained the correct annotation data.

### Frontend Issue
While section-level comments were being tracked and used for filtering, they weren't being **displayed** in the UI. The diff viewer only showed question-level comments.

## Solution

### 1. Backend Fix: Auto-construct `comments_addressed`

**File**: `src/services/workflow_service.py`

Added fallback logic to construct `comments_addressed` from `used_annotation_comment_ids` when the LLM doesn't provide it:

```python
# Lines 684-710
elif used_annotation_ids:
    # Fallback: If LLM didn't provide comments_addressed but we have used_annotation_comment_ids,
    # construct comments_addressed from annotation IDs so frontend checkbox is enabled
    constructed_comments = []
    
    # Question annotations
    if used_annotation_ids.get("question_annotations"):
        for q_id in used_annotation_ids["question_annotations"]:
            parent_version = survey.version - 1 if survey.version > 1 else 1
            constructed_comments.append(f"COMMENT-Q{q_id}-V{parent_version}")
    
    # Section annotations
    if used_annotation_ids.get("section_annotations"):
        for s_id in used_annotation_ids["section_annotations"]:
            parent_version = survey.version - 1 if survey.version > 1 else 1
            constructed_comments.append(f"COMMENT-S{s_id}-V{parent_version}")
    
    # Survey annotations
    if used_annotation_ids.get("survey_annotations"):
        for _ in used_annotation_ids["survey_annotations"]:
            parent_version = survey.version - 1 if survey.version > 1 else 1
            constructed_comments.append(f"COMMENT-SURVEY-V{parent_version}")
    
    if constructed_comments:
        survey.comments_addressed = constructed_comments
        logger.info(f"✅ [WorkflowService] Constructed comments_addressed from annotation IDs: {len(constructed_comments)} comment IDs")
```

**Result**: The `comments_addressed` field is now always populated when annotations are used, ensuring the frontend checkbox appears.

### 2. Frontend Fix: Display Section Comments

**File**: `frontend/src/components/SurveyDiffViewer.tsx`

#### Added Helper Function (Lines 287-319)
```typescript
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
```

#### Added Section Comment Display (Lines 760-788)
Section comments are now displayed in a purple banner at the top of each expanded section, before the questions:

```tsx
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
```

## Comment ID Format

The system uses structured comment IDs for tracking:

- **Question comments**: `COMMENT-Q{question_id}-V{version}`
  - Example: `COMMENT-Q123-V1`
- **Section comments**: `COMMENT-S{section_id}-V{version}`
  - Example: `COMMENT-S3-V1`
- **Survey comments**: `COMMENT-SURVEY-V{version}`
  - Example: `COMMENT-SURVEY-V1`

## Testing

### Build Verification
```bash
cd frontend && npm run build
```
✅ Build successful with no TypeScript errors (only pre-existing warnings)
✅ File size increase: +172 B (expected)

### Expected Behavior

1. **Checkbox Always Visible**: When annotations are used during regeneration, the "Show only comment-driven changes" checkbox will always appear in the diff viewer

2. **Section Comments Displayed**: When a section has annotation comments:
   - Purple banner appears at the top of the expanded section
   - Shows "📋 Section-Level Annotation Comments:" header
   - Displays each comment with a 💬 emoji
   - Shows the comment ID for debugging

3. **Question Comments**: Continue to work as before, shown above each question

4. **Filtering**: The "Show only comment-driven changes" checkbox filters to show:
   - Sections with section-level comments
   - Questions with question-level comments
   - All questions within commented sections

## Visual Design

### Section Comment Banner
- **Background**: Purple (`bg-purple-50`)
- **Border**: Purple bottom border (`border-purple-200`)
- **Icon**: 💬 emoji
- **Layout**: 
  - Header with 📋 emoji
  - Comment text in white rounded box with purple border
  - Comment ID in small purple monospace text

### Consistency
- Matches existing question comment styling
- Uses same purple color scheme for annotation-driven changes
- Maintains visual hierarchy (section → questions)

## Files Modified

1. **Backend**:
   - `src/services/workflow_service.py` (lines 681-710)

2. **Frontend**:
   - `frontend/src/components/SurveyDiffViewer.tsx` (lines 287-319, 760-788)

## Impact

- ✅ Section-level comments now fully visible and functional
- ✅ Checkbox always appears when annotations are used
- ✅ Better feedback loop for annotators
- ✅ Complete annotation tracking from backend to frontend
- ✅ No breaking changes to existing functionality

## Future Enhancements

Potential improvements:
1. Add survey-level comment display (similar to section comments)
2. Add comment highlighting/linking from diff to annotation panel
3. Show comment resolution status (addressed vs. unaddressed)
4. Add comment author and timestamp information

