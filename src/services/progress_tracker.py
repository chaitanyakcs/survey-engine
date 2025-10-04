"""
Centralized progress tracking system for survey generation workflow.
This ensures consistent, incremental progress percentages based on actual workflow completion.
"""

from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Centralized progress tracking that ensures consistent, incremental progress percentages.
    Each workflow step has a defined progress range, and the tracker ensures no conflicts.
    """
    
    # Define progress ranges for each workflow step
    PROGRESS_RANGES = {
        # Main survey generation workflow
        "initializing_workflow": (0, 10),
        "building_context": (10, 25),
        "preparing_generation": (25, 30),   # Updated: 25-30% for preparing generation
        "human_review": (30, 35),           # Updated: 30-35% for human review (happens before generation)
        "resuming_from_human_review": (35, 40), # Transition step after human review approval
        "generating_questions": (35, 60),   # Updated: 35-60% for Generating Questions LLM processing
        "llm_processing": (35, 60),         # Updated: 35-60% for LLM processing (same as generating_questions)
        "parsing_output": (60, 65),         # Updated: 60-65% for parsing output
        "validation_scoring": (65, 75),     # Updated: 65-75% for validation scoring
        "evaluating_pillars": (75, 85),     # Updated: 75-85% for evaluating pillars
        "finalizing": (85, 95),             # Updated: 85-95% for finalizing
        "completed": (95, 100),

        # Document parsing workflow
        "extracting_document": (0, 25),     # Document text extraction
        "processing_document": (25, 50),    # Document structure analysis
        "analyzing_document": (50, 75),     # AI analysis of content
        "parsing_complete": (75, 100),      # Document parsing completion

        # Field extraction workflow
        "analyzing_rfq": (0, 15),           # RFQ content analysis
        "analyzing_survey": (15, 25),       # Survey structure analysis
        "extracting_methodologies": (25, 40), # Methodology identification
        "classifying_industry": (40, 50),   # Industry classification
        "determining_goals": (50, 65),      # Research goals determination
        "assessing_quality": (65, 75),      # Quality assessment
        "generating_title": (75, 85),       # Title generation
        "validating_fields": (85, 95),      # Field validation
        "extraction_complete": (95, 100)    # Field extraction completion
    }
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.current_step: str | None = None
        self.current_progress = 0
        self.step_history: List[Dict[str, Any]] = []
        
    def get_step_progress(self, step: str, substep: Optional[str] = None) -> int:
        """
        Get the appropriate progress percentage for a given step.
        Ensures progress only moves forward and stays within step ranges.
        """
        if step not in self.PROGRESS_RANGES:
            logger.warning(f"⚠️ [ProgressTracker] Unknown step: {step}")
            return self.current_progress

        min_progress, max_progress = self.PROGRESS_RANGES[step]

        # If this is a new step, ensure we don't go backward
        if self.current_step != step:
            # CRITICAL FIX: Prevent backward progress movement
            new_progress = max(min_progress, self.current_progress)

            # If the new step's minimum is less than current progress, use current progress
            if new_progress > min_progress:
                logger.info(f"🛡️ [ProgressTracker] Prevented backward progress: keeping {self.current_progress}% instead of {min_progress}% for step '{step}'")

            self.current_step = step
            self.current_progress = new_progress
            self.step_history.append({
                "step": step,
                "substep": substep,
                "progress": self.current_progress,
                "timestamp": self._get_timestamp()
            })
            logger.info(f"📊 [ProgressTracker] Started step '{step}' at {self.current_progress}%")
            return self.current_progress
        
        # If same step, increment within range
        if self.current_progress < max_progress:
            # Calculate dynamic increment based on step range (10% of range or 2%, whichever is larger)
            range_size = max_progress - min_progress
            dynamic_increment = max(2, int(range_size * 0.1))
            increment = min(dynamic_increment, max_progress - self.current_progress)
            self.current_progress += increment
            # Safety check: never exceed 100%
            self.current_progress = min(100, self.current_progress)
            self.step_history.append({
                "step": step,
                "substep": substep,
                "progress": self.current_progress,
                "timestamp": self._get_timestamp()
            })
            logger.info(f"📊 [ProgressTracker] Incremented '{step}' to {self.current_progress}%")
            return self.current_progress
        
        # Already at max for this step
        return self.current_progress
    
    def get_final_progress(self, step: str) -> int:
        """Get the final progress percentage for a completed step."""
        if step not in self.PROGRESS_RANGES:
            return self.current_progress
            
        _, max_progress = self.PROGRESS_RANGES[step]
        self.current_progress = max_progress
        # Safety check: never exceed 100%
        self.current_progress = min(100, self.current_progress)
        self.step_history.append({
            "step": step,
            "substep": "completed",
            "progress": self.current_progress,
            "timestamp": self._get_timestamp()
        })
        logger.info(f"📊 [ProgressTracker] Completed step '{step}' at {self.current_progress}%")
        return self.current_progress
    
    def get_progress_message(self, step: str, substep: Optional[str] = None) -> str:
        """Get appropriate message for the current step."""
        messages = {
            # Main survey generation workflow
            "initializing_workflow": "Starting survey generation workflow...",
            "building_context": "Analyzing requirements and gathering templates",
            "preparing_generation": "Setting up survey creation pipeline...",
            "resuming_from_human_review": "Resuming survey generation after human review...",
            "generating_questions": "Creating your survey content",
            "llm_processing": "Processing with AI model...",
            "parsing_output": "Structuring generated content...",
            "human_review": "Reviewing AI-generated system prompt...",
            "validation_scoring": "Running comprehensive evaluations and quality assessments...",
            "evaluating_pillars": "Analyzing quality across all pillars...",
            "finalizing": "Processing results and finalizing survey...",
            "completed": "Survey generation completed successfully!",

            # Document parsing workflow
            "extracting_document": "Extracting text from document...",
            "processing_document": "Processing document structure...",
            "analyzing_document": "AI is analyzing document content...",
            "parsing_complete": "Document parsing completed successfully!",

            # Field extraction workflow
            "analyzing_rfq": "Analyzing RFQ content...",
            "analyzing_survey": "Analyzing survey structure...",
            "extracting_methodologies": "Identifying methodologies...",
            "classifying_industry": "Classifying industry category...",
            "determining_goals": "Determining research goals...",
            "assessing_quality": "Assessing survey quality...",
            "generating_title": "Generating suggested title...",
            "validating_fields": "Validating extracted fields...",
            "extraction_complete": "Field extraction completed!"
        }
        
        base_message = messages.get(step, f"Processing {step}...")
        
        if substep:
            return f"{base_message} ({substep})"
        return base_message
    
    def get_progress_data(self, step: str, substep: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        """Get complete progress data for a step."""
        progress = self.get_step_progress(step, substep)
        
        return {
            "type": "progress",
            "step": step,
            "percent": progress,
            "message": self.get_progress_message(step, substep),
            "workflow_id": self.workflow_id,
            "substep": substep,
            **kwargs
        }
    
    def get_completion_data(self, step: str, **kwargs: Any) -> Dict[str, Any]:
        """Get completion data for a step."""
        progress = self.get_final_progress(step)
        
        return {
            "type": "progress",
            "step": step,
            "percent": progress,
            "message": self.get_progress_message(step),
            "workflow_id": self.workflow_id,
            "completed": True,
            **kwargs
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for logging."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get the complete progress history."""
        return self.step_history.copy()
    
    def reset(self) -> None:
        """Reset the progress tracker. WARNING: This can cause backward progress!"""
        # Log warning about potential backward movement
        if self.current_progress > 0:
            logger.warning(f"⚠️ [ProgressTracker] DANGEROUS: Resetting tracker with {self.current_progress}% progress. This may cause backward movement!")

        self.current_step = None
        self.current_progress = 0
        self.step_history = []
        logger.info(f"🔄 [ProgressTracker] Reset progress tracker for workflow {self.workflow_id}")


# Global progress trackers by workflow ID
_progress_trackers: Dict[str, ProgressTracker] = {}


def get_progress_tracker(workflow_id: str) -> ProgressTracker:
    """Get or create a progress tracker for a workflow."""
    if workflow_id not in _progress_trackers:
        _progress_trackers[workflow_id] = ProgressTracker(workflow_id)
        logger.info(f"📊 [ProgressTracker] Created new tracker for workflow {workflow_id}")
    else:
        # Log when reusing existing tracker to help debug duplicates
        existing_tracker = _progress_trackers[workflow_id]
        logger.info(f"♻️ [ProgressTracker] Reusing existing tracker for workflow {workflow_id} (current: {existing_tracker.current_progress}%, step: {existing_tracker.current_step})")

    return _progress_trackers[workflow_id]


def cleanup_progress_tracker(workflow_id: str) -> None:
    """Clean up a progress tracker when workflow completes."""
    if workflow_id in _progress_trackers:
        del _progress_trackers[workflow_id]
        logger.info(f"🧹 [ProgressTracker] Cleaned up tracker for workflow {workflow_id}")


def get_all_active_workflows() -> List[str]:
    """Get list of all active workflow IDs."""
    return list(_progress_trackers.keys())
