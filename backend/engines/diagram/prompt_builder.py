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

        relationships = "\n".join(
            [
                f"- {item.source} -> {item.target}: {item.description}"
                for item in specification.relationships
            ]
        ) or "- Show clear functional connections between related components."


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
- Compose specifically for a final width of 384 pixels
- Use very large, bold, short labels that remain readable after reducing the image to 384 pixels
- Use thick outlines and arrows; avoid thin lines, fine textures, and small type
- Label components with names only; do not include descriptive paragraphs around the diagram
- No unnecessary background
- Show an internal cutaway view when the request asks how an object works
- Use arrows to show mechanical movement, electrical signals, or information flow
- Keep generous spacing between labels and components


Components:

{elements}


Connections and signal flow:

{relationships}


The final image must be suitable for a small thermal printer.
"""


        return prompt.strip()
