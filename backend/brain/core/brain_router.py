from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, AsyncGenerator

@dataclass
class BrainResponse:
    """Standardized response from the brain system"""
    success: bool
    response: str
    mode_used: ChatMode
    processing_time: float
    resources_used: List[str]
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    verification_status: str = "pending"
    execution_plan: Optional[Dict[str, Any]] = None
    session_id: str = "default"

    def to_dict(self) -> Dict[str, Any]:
        """Convert BrainResponse to a dictionary for JSON serialization"""
        return {
            "success": self.success,
            "response": self.response,
            "mode_used": self.mode_used.value if hasattr(self.mode_used, 'value') else str(self.mode_used),
            "processing_time": self.processing_time,
            "resources_used": self.resources_used,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "verification_status": self.verification_status,
            "execution_plan": self.execution_plan,
            "session_id": self.session_id
        }

    def __str__(self) -> str:
        """String representation for display"""
        if self.execution_plan:
            return self.execution_plan.get("response", self.response)
        return self.response 

    async def _handle_agent_mode(self, request: ChatRequest) -> AsyncGenerator[BrainResponse, None]:
        """Handle Agent mode with streaming responses."""
        try:
            from real_agent_automation_handler import handle_real_agent_automation
            
            # Use the real automation system with streaming responses
            async for response_chunk in handle_real_agent_automation(request.query, request.session_id):
                # Convert each chunk to BrainResponse
                brain_response = BrainResponse(
                    success=response_chunk.get("success", True),
                    response=response_chunk.get("response", ""),
                    mode_used=request.mode,
                    processing_time=0.0,
                    resources_used=["automation", "llm", "memory"],
                    confidence=response_chunk.get("confidence", 0.8),
                    metadata=response_chunk.get("metadata", {}),
                    execution_plan=response_chunk.get("execution_plan", None),
                    session_id=request.session_id
                )
                yield brain_response
                
        except ImportError as e:
            logger.warning(f"Improved agent handler not available: {e}, using fallback")
            # Fallback to basic agent mode
            yield BrainResponse(
                success=True,
                response=f"🤖 **Agent Mode - Basic Handler**\n\nI understand you want me to help with: \"{request.query}\"\n\nThe advanced universal automation system is currently not available. Please try again or contact support if this issue persists.",
                mode_used=request.mode,
                processing_time=0.5,
                resources_used=["memory", "basic_planning"],
                confidence=0.6,
                metadata={"fallback_mode": True, "error": str(e)},
                session_id=request.session_id
            ) 