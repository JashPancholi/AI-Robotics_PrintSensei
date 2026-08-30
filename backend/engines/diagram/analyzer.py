from backend.services.ai.openai_provider import OpenAIProvider

from .models import DiagramSpecification


class DiagramAnalyzer:
    """
    Converts user instructions into a structured diagram specification.
    Uses AI for understanding.
    """

    def __init__(self):

        self.ai = OpenAIProvider()


    def analyze(self, request):

        prompt = f"""

You are a diagram planning AI for PrintSensei.

Your task is to understand the user's diagram request
and create a structured diagram specification.

User request:

{request.instruction}


User preferred detail level:

{request.detail_level}


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


        return DiagramSpecification(
            **result
        )