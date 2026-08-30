import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.enums.label_type import LabelType
from app.renderer import RenderResult
from backend.core.response import Response
from backend.engines.diagram.models import DiagramElement, DiagramSpecification
from backend.services.image.thermal import ThermalImageResult
from backend.services.study.service import StudyContentGenerator, StudyService


class FakeAIProvider:
    def generate_structured_output(self, prompt, schema):
        assert "between 1 and 3 points" in prompt
        assert schema["title"] == "GeneratedStudyContent"
        return {
            "title": "  Binary Search  ",
            "points": [
                "  Requires sorted input.  ",
                "Compares against the middle value.",
                "Discards half after each comparison.",
                "This extra point is removed for low detail.",
            ],
        }


class FakeRenderer:
    def __init__(self):
        self.label_data = None

    def render(self, label_data):
        self.label_data = label_data
        return RenderResult(
            status="success",
            file="generated_labels/label_00007.png",
            width=384,
            height=280,
        )


def test_study_service_generates_and_renders_study_label():
    renderer = FakeRenderer()
    service = StudyService(
        generator=StudyContentGenerator(provider=FakeAIProvider()),
        renderer=renderer,
    )

    result = service.generate("Explain binary search", "low")

    assert result.content.title == "Binary Search"
    assert len(result.content.points) == 3
    assert result.preview_url == "/generated-labels/label_00007.png"
    assert result.content_type == "notes"
    assert renderer.label_data.label_type is LabelType.STUDY
    assert renderer.label_data.metadata == {
        "points": result.content.points,
        "source": "text",
        "detail_level": "low",
    }


class FailingNotesGenerator:
    def generate(self, text, detail_level):
        raise AssertionError("Diagram requests must not use the notes generator.")


class FakeDiagramService:
    def __init__(self):
        self.request = None

    def generate(self, request, progress_callback=None):
        self.request = request
        if progress_callback:
            progress_callback(60, "Generating diagram image")
            progress_callback(90, "Diagram image generated")
        return Response(
            success=True,
            message="Diagram generated successfully",
            payload={
                "specification": DiagramSpecification(
                    title="Mouse Internal Working",
                    description="A labeled cutaway showing the mouse components and signal flow.",
                    elements=[
                        DiagramElement(
                            name="Optical sensor",
                            description="Detects movement across a surface.",
                        )
                    ],
                ),
                "image": "diagram_images/human_heart.png",
            },
        )


class FakeThermalProcessor:
    def prepare(self, source):
        return ThermalImageResult(
            file=Path("diagram_images/mouse_thermal.png"),
            width=384,
            height=384,
        )


def test_study_service_routes_explicit_diagram_request_to_diagram_engine():
    diagram_service = FakeDiagramService()
    service = StudyService(
        generator=FailingNotesGenerator(),
        renderer=FakeRenderer(),
        diagram_service=diagram_service,
        thermal_processor=FakeThermalProcessor(),
    )

    result = service.generate("a cheap mouse internal working diagram", "medium")

    assert diagram_service.request.task.value == "diagram"
    assert diagram_service.request.instruction == "a cheap mouse internal working diagram"
    assert result.content_type == "diagram"
    assert result.content.title == "Mouse Internal Working"
    assert result.preview_url == "/diagram-images/mouse_thermal.png"
    assert result.render.width == 384
    assert result.render.height == 384
