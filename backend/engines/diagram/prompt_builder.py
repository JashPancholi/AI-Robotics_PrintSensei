from .models import DiagramSpecification


class DiagramPromptBuilder:


    def build(
        self,
        specification: DiagramSpecification
    ) -> str:


        elements = "\n".join(
            [
                f"- {item.name}: {item.description}"
                for item in specification.elements
            ]
        )


        prompt = f"""
Create a thermal printer compatible educational diagram.

Title:
{specification.title}


Style:
{specification.style}


Orientation:
{specification.orientation}


Requirements:
- Black and white line art
- High contrast
- Simple shapes
- Clear readable labels
- No unnecessary background


Components:

{elements}


The final image must be suitable for a small thermal printer.
"""


        return prompt.strip()