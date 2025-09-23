# Survey Engine - AI Suggestions Component TODO

## Current State
The AI suggestions component exists but is largely static and needs to be made fully functional with proper loading states, error handling, and dynamic content generation.

## Priority Tasks

### 1. **Component Architecture & State Management**
- [ ] Add proper loading states for AI suggestion generation
- [ ] Implement error handling for failed AI requests
- [ ] Add retry mechanisms for failed suggestions
- [ ] Create suggestion caching to avoid redundant API calls
- [ ] Add suggestion history/undo functionality

### 2. **API Integration**
- [ ] Create dedicated AI suggestions API endpoint (`/api/v1/suggestions/`)
- [ ] Implement suggestion generation service in backend
- [ ] Add suggestion validation and filtering
- [ ] Create suggestion ranking/scoring system
- [ ] Add suggestion categories (methodology, question types, etc.)

### 3. **User Experience Improvements**
- [ ] Add skeleton loaders while suggestions are being generated
- [ ] Implement progressive loading (show suggestions as they're generated)
- [ ] Add suggestion preview/expand functionality
- [ ] Create suggestion comparison view
- [ ] Add suggestion feedback system (thumbs up/down)

### 4. **Dynamic Content Generation**
- [ ] Generate contextual suggestions based on:
  - Current RFQ content and context
  - Selected methodologies
  - Industry category
  - Research goals
  - Existing questions in survey
- [ ] Implement suggestion personalization based on user preferences
- [ ] Add suggestion relevance scoring

### 5. **Suggestion Types to Implement**
- [ ] **Question Suggestions**: AI-generated questions for specific topics
- [ ] **Methodology Suggestions**: Recommended research approaches
- [ ] **Question Flow Suggestions**: Optimal question ordering
- [ ] **Validation Suggestions**: Quality improvements for existing questions
- [ ] **Industry-Specific Suggestions**: Tailored recommendations by sector
- [ ] **Response Option Suggestions**: Better answer choices for questions

### 6. **Backend Services Needed**
- [ ] `SuggestionService` class for generating AI suggestions
- [ ] `SuggestionCache` for storing and retrieving suggestions
- [ ] `SuggestionRanking` for scoring suggestion relevance
- [ ] Integration with existing `PromptService` for consistent AI prompts
- [ ] Database models for storing suggestion history

### 7. **Frontend Components to Build**
- [ ] `SuggestionLoader` - Loading states and progress indicators
- [ ] `SuggestionCard` - Individual suggestion display component
- [ ] `SuggestionFilter` - Filter suggestions by type/category
- [ ] `SuggestionPreview` - Preview suggestion before applying
- [ ] `SuggestionFeedback` - User feedback collection
- [ ] `SuggestionHistory` - View previously generated suggestions

### 8. **Performance Optimizations**
- [ ] Implement lazy loading for suggestions
- [ ] Add suggestion pagination for large result sets
- [ ] Optimize API calls with debouncing
- [ ] Add suggestion preloading for better UX
- [ ] Implement suggestion background refresh

### 9. **Error Handling & Edge Cases**
- [ ] Handle API timeouts gracefully
- [ ] Show fallback suggestions when AI fails
- [ ] Handle empty suggestion results
- [ ] Add suggestion validation before display
- [ ] Implement suggestion conflict resolution

### 10. **Analytics & Monitoring**
- [ ] Track suggestion usage patterns
- [ ] Monitor suggestion acceptance rates
- [ ] Add suggestion performance metrics
- [ ] Implement A/B testing for suggestion algorithms
- [ ] Add suggestion quality scoring

## Technical Implementation Notes

### Backend API Structure
```typescript
// Suggested API endpoints
GET /api/v1/suggestions/questions?context={rfq_id}
GET /api/v1/suggestions/methodologies?industry={category}
POST /api/v1/suggestions/generate
POST /api/v1/suggestions/feedback
GET /api/v1/suggestions/history
```

### Frontend State Management
```typescript
interface SuggestionState {
  suggestions: Suggestion[];
  loading: boolean;
  error: string | null;
  filters: SuggestionFilters;
  history: SuggestionHistory[];
  feedback: SuggestionFeedback[];
}
```

### Database Schema
```sql
-- Suggestions table
CREATE TABLE suggestions (
  id UUID PRIMARY KEY,
  type VARCHAR(50) NOT NULL,
  content JSONB NOT NULL,
  context JSONB,
  relevance_score DECIMAL(3,2),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Suggestion feedback table
CREATE TABLE suggestion_feedback (
  id UUID PRIMARY KEY,
  suggestion_id UUID REFERENCES suggestions(id),
  user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
  feedback_text TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Success Metrics
- [ ] Suggestion generation time < 3 seconds
- [ ] Suggestion acceptance rate > 60%
- [ ] User satisfaction score > 4.0/5.0
- [ ] Zero critical errors in suggestion generation
- [ ] 95% uptime for suggestion API

## Dependencies
- Existing `PromptService` for AI integration
- Current `EmbeddingService` for context understanding
- `RulesService` for methodology-based suggestions
- Frontend state management (Zustand)
- Error handling utilities

## Estimated Effort
- **Backend Development**: 3-4 days
- **Frontend Development**: 2-3 days
- **Testing & QA**: 1-2 days
- **Total**: 6-9 days

## Notes
- Leverage existing AI infrastructure (Replicate, SentenceTransformers)
- Ensure suggestions align with current rules system
- Maintain consistency with existing UI/UX patterns
- Consider mobile responsiveness for suggestion display
- Plan for future ML model improvements and suggestion algorithm updates