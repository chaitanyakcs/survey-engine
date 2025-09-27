"""
Centralized progress tracking system for survey generation workflow.
This ensures consistent, incremental progress percentages based on actual workflow completion.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Centralized progress tracking that ensures consistent, incremental progress percentages.
    Each workflow step has a defined progress range, and the tracker ensures no conflicts.
    """
    
    # Define progress ranges for each workflow step
    PROGRESS_RANGES = {
        "initializing_workflow": (0, 10),
        "building_context": (10, 25),
        "preparing_generation": (25, 35),
        "generating_questions": (35, 60),  # Updated: 35-60% for Generating Questions LLM processing
        "llm_processing": (35, 60),        # Updated: 35-60% for LLM processing (same as generating_questions)
        "parsing_output": (60, 65),        # Updated: 60-65% for parsing output
        "human_review": (65, 75),          # Updated: 65-75% for human review
        "validation_scoring": (75, 85),    # Updated: 75-85% for validation scoring
        "evaluating_pillars": (85, 95),    # Updated: 85-95% for evaluating pillars
        "finalizing": (90, 95),            # Keep finalizing at 90-95%
        "completed": (95, 100)
    }
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.current_step = None
        self.current_progress = 0
        self.step_history = []
        
    def get_step_progress(self, step: str, substep: Optional[str] = None) -> int:
        """
        Get the appropriate progress percentage for a given step.
        Ensures progress only moves forward and stays within step ranges.
        """
        if step not in self.PROGRESS_RANGES:
            logger.warning(f"⚠️ [ProgressTracker] Unknown step: {step}")
            return self.current_progress
            
        min_progress, max_progress = self.PROGRESS_RANGES[step]
        
        # If this is a new step, start at the minimum
        if self.current_step != step:
            self.current_step = step
            self.current_progress = min_progress
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
            # Increment by 5% or to max, whichever is smaller
            increment = min(5, max_progress - self.current_progress)
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
            "initializing_workflow": "Starting survey generation workflow...",
            "building_context": "Analyzing requirements and gathering templates",
            "preparing_generation": "Setting up survey creation pipeline...",
            "generating_questions": "Creating your survey content",
            "llm_processing": "Processing with AI model...",
            "parsing_output": "Structuring generated content...",
            "human_review": "Reviewing AI-generated system prompt...",
            "validation_scoring": "Running comprehensive evaluations and quality assessments...",
            "evaluating_pillars": "Analyzing quality across all pillars...",
            "finalizing": "Processing results and finalizing survey...",
            "completed": "Survey generation completed successfully!"
        }
        
        base_message = messages.get(step, f"Processing {step}...")
        
        if substep:
            return f"{base_message} ({substep})"
        return base_message
    
    def get_progress_data(self, step: str, substep: Optional[str] = None, **kwargs) -> Dict[str, Any]:
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
    
    def get_completion_data(self, step: str, **kwargs) -> Dict[str, Any]:
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
    
    def get_history(self) -> list:
        """Get the complete progress history."""
        return self.step_history.copy()
    
    def reset(self):
        """Reset the progress tracker."""
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
    
    return _progress_trackers[workflow_id]


def cleanup_progress_tracker(workflow_id: str):
    """Clean up a progress tracker when workflow completes."""
    if workflow_id in _progress_trackers:
        del _progress_trackers[workflow_id]
        logger.info(f"🧹 [ProgressTracker] Cleaned up tracker for workflow {workflow_id}")


def get_all_active_workflows() -> list:
    """Get list of all active workflow IDs."""
    return list(_progress_trackers.keys())
