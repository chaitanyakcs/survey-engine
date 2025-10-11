# Frontend Style Guide

## Overview

This document outlines the standardized design system implemented across the Survey Engine frontend. All components should follow these guidelines to ensure visual consistency and maintainability.

## Color Palette

### Primary Colors
- **Primary**: Amber-based colors for main actions and highlights
  - `primary-50` to `primary-900` (50 being lightest, 900 darkest)
  - Default: `primary-500` (#eab308)
  - Hover: `primary-600` (#ca8a04)

### Secondary Colors
- **Secondary**: Blue-based colors for secondary actions and information
  - `secondary-50` to `secondary-900`
  - Default: `secondary-500` (#3b82f6)
  - Hover: `secondary-600` (#2563eb)

### Semantic Colors
- **Success**: Green shades for completed states and positive actions
  - `success-500` (#22c55e) for success states
  - `success-50` (#f0fdf4) for light backgrounds

- **Error**: Red shades for failed states and destructive actions
  - `error-500` (#ef4444) for error states
  - `error-50` (#fef2f2) for light backgrounds

- **Warning**: Yellow shades for in-progress states and warnings
  - `warning-500` (#eab308) for warning states
  - `warning-50` (#fefce8) for light backgrounds

- **Info**: Gray shades for neutral information
  - `info-500` (#6b7280) for info states
  - `info-50` (#f9fafb) for light backgrounds

## Typography

### Heading Classes
Use standardized heading utility classes instead of individual Tailwind classes:

```css
.heading-1  /* text-4xl font-bold text-gray-900 */
.heading-2  /* text-3xl font-bold text-gray-900 */
.heading-3  /* text-2xl font-semibold text-gray-900 */
.heading-4  /* text-lg font-semibold text-gray-900 */
```

### Body Text Classes
```css
.body-large    /* text-lg text-gray-700 */
.body-default  /* text-base text-gray-700 */
.body-small    /* text-sm text-gray-600 */
```

### Label Classes
```css
.label-default /* text-sm font-medium text-gray-700 */
.label-small   /* text-xs font-medium text-gray-600 */
```

## Component Utilities

### Buttons

#### Primary Buttons
```css
.btn-primary     /* Large primary button */
.btn-primary-sm  /* Small primary button */
```

#### Secondary Buttons
```css
.btn-secondary     /* Large secondary button */
.btn-secondary-sm  /* Small secondary button */
```

#### Danger Buttons
```css
.btn-danger     /* Large danger button */
.btn-danger-sm  /* Small danger button */
```

#### Success Buttons
```css
.btn-success-sm  /* Small success button */
```

#### Ghost Buttons
```css
.btn-ghost  /* Ghost button with hover state */
```

### Cards

#### Card Variants
```css
.card-default      /* Standard card with border */
.card-default-sm   /* Small standard card */
.card-elevated      /* Card with shadow */
.card-elevated-sm   /* Small elevated card */
.card-highlighted   /* Highlighted card with gradient background */
.card-highlighted-sm /* Small highlighted card */
```

### Status Indicators

#### Status Classes
```css
.status-success  /* Green status indicator */
.status-error    /* Red status indicator */
.status-warning  /* Yellow status indicator */
.status-info     /* Gray status indicator */
.status-active   /* Blue active status indicator */
```

### Badges

#### Badge Variants
```css
.badge-primary    /* Primary badge */
.badge-secondary  /* Secondary badge */
.badge-success    /* Success badge */
.badge-error      /* Error badge */
.badge-warning    /* Warning badge */
.badge-info       /* Info badge */
```

### Form Inputs

#### Input Classes
```css
.input-default      /* Standard input styling */
.input-highlighted  /* Highlighted input for auto-filled fields */
.input-error        /* Error state input */
```

## Usage Guidelines

### 1. Color Usage
- **Primary actions**: Use `primary-500` for main CTAs and important elements
- **Secondary actions**: Use `secondary-500` for secondary buttons and info elements
- **Status indicators**: Use semantic colors (success, error, warning, info) based on meaning
- **Text colors**: Use gray scale for text hierarchy

### 2. Button Hierarchy
- **Primary buttons**: For main actions (Save, Submit, Generate)
- **Secondary buttons**: For secondary actions (Cancel, Back, Edit)
- **Danger buttons**: For destructive actions (Delete, Remove)
- **Success buttons**: For positive actions (Verify, Approve)
- **Ghost buttons**: For subtle actions (View, More)

### 3. Card Usage
- **Default cards**: For standard content containers
- **Elevated cards**: For important content that needs emphasis
- **Highlighted cards**: For special content or annotations

### 4. Status Indicators
- **Success**: Completed states, verified content
- **Error**: Failed states, errors, warnings
- **Warning**: In-progress states, pending actions
- **Info**: Neutral information, general status
- **Active**: Currently selected or active items

### 5. Typography Hierarchy
- **Heading-1**: Page titles, main headings
- **Heading-2**: Section titles, major headings
- **Heading-3**: Subsection titles, card titles
- **Heading-4**: Component titles, form section headers
- **Body text**: Use appropriate body classes for content
- **Labels**: Use label classes for form labels and small text

## Implementation Examples

### Button Implementation
```tsx
// Primary action button
<button className="btn-primary">
  Generate Survey
</button>

// Secondary action button
<button className="btn-secondary-sm">
  Cancel
</button>

// Danger action button
<button className="btn-danger">
  Delete Survey
</button>
```

### Card Implementation
```tsx
// Standard card
<div className="card-default">
  <h3 className="heading-4">Card Title</h3>
  <p className="body-default">Card content...</p>
</div>

// Highlighted card for annotations
<div className="card-highlighted">
  <h4 className="heading-4">Annotation Panel</h4>
  {/* Annotation content */}
</div>
```

### Status Implementation
```tsx
// Success status
<div className="status-success">
  <CheckIcon className="w-4 h-4" />
  <span>Completed</span>
</div>

// Error status
<div className="status-error">
  <XCircleIcon className="w-4 h-4" />
  <span>Failed</span>
</div>
```

### Badge Implementation
```tsx
// AI Generated badge
<div className="badge-secondary">
  <div className="w-2 h-2 bg-secondary-500 rounded-full animate-pulse"></div>
  <span>AI Generated</span>
</div>

// Success badge
<div className="badge-success">
  <CheckIcon className="w-3 h-3" />
  <span>Verified</span>
</div>
```

## Migration Guide

### Before (Inconsistent)
```tsx
// Old inconsistent styling
<div className="bg-gradient-to-br from-yellow-50 to-amber-50 border-2 border-yellow-200 rounded-xl p-6">
  <h4 className="text-lg font-semibold text-gray-800">Title</h4>
  <button className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600">
    Action
  </button>
</div>
```

### After (Standardized)
```tsx
// New standardized styling
<div className="card-highlighted">
  <h4 className="heading-4">Title</h4>
  <button className="btn-primary-sm">
    Action
  </button>
</div>
```

## Best Practices

1. **Always use utility classes** instead of individual Tailwind classes for common patterns
2. **Maintain color consistency** by using the defined color palette
3. **Use semantic colors** based on meaning, not appearance
4. **Follow the typography hierarchy** for consistent text sizing
5. **Test across different states** (hover, active, disabled) to ensure consistency
6. **Document any new patterns** that don't fit existing utilities

## Future Enhancements

- Add more button variants (outline, ghost with icons)
- Create more card variants (bordered, filled)
- Add animation utilities for consistent transitions
- Create form component utilities for complex forms
- Add responsive utilities for mobile-first design

---

This style guide should be updated as new patterns emerge and the design system evolves.

