from typing import Optional
from backend.services.ai.openai_provider import OpenAIProvider
from backend.services.vision.models import VisualAnalysis
from .models import DiagramSpecification


class DiagramAnalyzer:
    """
    Converts user instructions and optional visual context into a structured diagram specification.
    Uses AI for understanding.
    """

    def __init__(self, provider: Optional[OpenAIProvider] = None):
        self.ai = provider or OpenAIProvider()

    def analyze(self, request, vision_context: Optional[VisualAnalysis] = None) -> DiagramSpecification:
        
        vision_section = ""
        if vision_context:
            elements_summary = ", ".join(
                [f"{e.name} (Position: {e.position})" for e in vision_context.elements]
            ) or "None"
            
            relations_summary = "; ".join(
                [f"{r.source} -> {r.target} ({r.description})" for r in vision_context.relationships]
            ) or "None"
            
            ocr_text = ", ".join(vision_context.extracted_text) or "None"

            vision_section = f"""
Supporting Image Context (from user-supplied reference image):
- Image Classification: {vision_context.image_type}
- Visual Overview: {vision_context.description}
- Visible OCR Labels: {ocr_text}
- Detected Structural Components: {elements_summary}
- Identified Relationships: {relations_summary}

Use this visual context to ground your component extraction, layout, and connections.
"""

        prompt = f"""
You are a diagram planning AI for PrintSensei.

Your task is to understand the user's diagram request and any accompanying visual reference
to create a structured diagram specification.

User request:
{request.instruction}

User preferred detail level:
{request.detail_level}
{vision_section}
Detail rules:

LOW:
- Keep only essential components.
- Maximum readability.
- Suitable for small thermal printers.

MEDIUM:
- Include important supporting components.
- Balanced educational diagram.

HIGH:
- Include detailed components.
- More labels are acceptable.


Every diagram element MUST contain an importance score.

Importance scoring:

10:
Critical component. Must always appear.

7-9:
Important supporting component.

4-6:
Normal component.

1-3:
Minor detail.


Return ONLY JSON.

Required format:

{{
"title": "",
"description": "",
"style": "",
"orientation": "",
"labels": true,
"elements": [
    {{
        "name": "",
        "description": "",
        "position": "",
        "label": true,
        "importance": 5
    }}
],
"relationships": [
    {{
        "source": "",
        "target": "",
        "description": ""
    }}
],
"rendering_notes": ""
}}

Remember:
- Think about thermal printer limitations.
- Avoid unnecessary details.
- Assign realistic importance scores.
- Higher importance means the component is more essential.
"""

        result = self.ai.generate_structured_output(
            prompt,
            DiagramSpecification.model_json_schema()
        )

        return DiagramSpecification(**result)