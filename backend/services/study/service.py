import re
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Callable, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from app.enums.label_type import LabelType
from app.models.label_data import LabelData
from app.renderer import LabelRenderer, RenderResult
from backend.core.enums import TaskType
from backend.core.request import Request
from backend.engines.diagram.service import DiagramService
from backend.services.ai.base import AIProvider
from backend.services.ai.openai_provider import OpenAIProvider
from backend.services.image.thermal import ThermalImageProcessor


class StudyServiceError(RuntimeError):
    """Raised when study content or its preview cannot be generated."""


StudyPoint = Annotated[str, Field(min_length=1, max_length=180)]


class GeneratedStudyContent(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    points: list[StudyPoint] = Field(min_length=1, max_length=8)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("title must not be blank")
        return normalized

    @field_validator("points")
    @classmethod
    def normalize_points(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values if value.strip()]
        if not normalized:
            raise ValueError("at least one non-blank point is required")
        return normalized


class StudyContentGenerator:
    POINT_LIMITS = {"low": 3, "medium": 5, "high": 8}

    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider

    @property
    def provider(self) -> AIProvider:
        if self._provider is None:
            self._provider = OpenAIProvider()
        return self._provider

    def generate(self, text: str, detail_level: str) -> GeneratedStudyContent:
        point_limit = self.POINT_LIMITS[detail_level]
        prompt = f"""
You create concise study labels for a 58 mm monochrome thermal printer.

User request:
{text}

Return only a JSON object with this shape:
{{
  "title": "A short topic title",
  "points": ["A concise study point"]
}}

Requirements:
- Return between 1 and {point_limit} points.
- Each point must be independently useful and no longer than 180 characters.
- Keep the title under 80 characters.
- Do not use Markdown, numbering, or bullet characters.
- Do not add facts unrelated to the user's request.
""".strip()

        try:
            result = self.provider.generate_structured_output(
                prompt,
                GeneratedStudyContent.model_json_schema(),
            )
            content = GeneratedStudyContent.model_validate(result)
        except Exception as exc:
            raise StudyServiceError("The AI service could not generate valid study content.") from exc

        return content.model_copy(update={"points": content.points[:point_limit]})


@dataclass(frozen=True)
class StudyGenerationResult:
    request_id: UUID
    content: GeneratedStudyContent
    render: RenderResult
    content_type: Literal["notes", "diagram"] = "notes"

    @property
    def preview_url(self) -> str:
        route = "diagram-images" if self.content_type == "diagram" else "generated-labels"
        return f"/{route}/{Path(self.render.file).name}"


class StudyService:
    def __init__(
        self,
        generator: StudyContentGenerator | None = None,
        renderer: LabelRenderer | None = None,
        diagram_service: DiagramService | None = None,
        thermal_processor: ThermalImageProcessor | None = None,
    ) -> None:
        self.generator = generator or StudyContentGenerator()
        self.renderer = renderer or LabelRenderer()
        self._diagram_service = diagram_service
        self.thermal_processor = thermal_processor or ThermalImageProcessor()

    @property
    def diagram_service(self) -> DiagramService:
        if self._diagram_service is None:
            self._diagram_service = DiagramService()
        return self._diagram_service

    def generate(
        self,
        text: str,
        detail_level: str,
        progress_callback: Callable[[int, str], None] | None = None,
    ) -> StudyGenerationResult:
        report = progress_callback or (lambda progress, stage: None)
        report(5, "Classifying request")
        if self._is_diagram_request(text):
            return self._generate_diagram(text, detail_level, report)

        return self._generate_notes(text, detail_level, report)

    @staticmethod
    def _is_diagram_request(text: str) -> bool:
        return bool(
            re.search(
                r"\b(diagram|schematic|flowchart|cutaway|cross[- ]section)\b",
                text,
                flags=re.IGNORECASE,
            )
        )

    def _generate_notes(
        self,
        text: str,
        detail_level: str,
        report: Callable[[int, str], None],
    ) -> StudyGenerationResult:
        report(15, "Generating study points")
        content = self.generator.generate(text, detail_level)
        report(70, "Study content generated")
        label_data = LabelData(
            title=content.title,
            label_type=LabelType.STUDY,
            metadata={
                "points": content.points,
                "source": "text",
                "detail_level": detail_level,
            },
        )

        try:
            report(80, "Rendering label preview")
            render = self.renderer.render(label_data)
        except Exception as exc:
            raise StudyServiceError("The study label preview could not be rendered.") from exc
        report(95, "Label preview ready")

        return StudyGenerationResult(
            request_id=uuid4(),
            content=content,
            render=render,
            content_type="notes",
        )

    def _generate_diagram(
        self,
        text: str,
        detail_level: str,
        report: Callable[[int, str], None],
    ) -> StudyGenerationResult:
        request = Request(
            task=TaskType.DIAGRAM,
            instruction=text,
            input_mode="text",
            detail_level=detail_level,
        )

        try:
            response = self.diagram_service.generate(request, progress_callback=report)
            payload = response.payload or {}
            image_path = Path(payload.get("image", ""))
            specification = payload.get("specification")
            if not response.success or not image_path.is_file() or specification is None:
                raise ValueError("Diagram generation returned no image.")

            report(92, "Converting to printer bitmap")
            thermal_image = self.thermal_processor.prepare(image_path)
            report(97, "Printer bitmap ready")

            description = specification.description.strip()[:180]
            content = GeneratedStudyContent(
                title=specification.title,
                points=[description or "Generated educational diagram."],
            )
        except Exception as exc:
            raise StudyServiceError("The AI service could not generate the requested diagram.") from exc

        return StudyGenerationResult(
            request_id=uuid4(),
            content=content,
            render=RenderResult(
                status="success",
                file=thermal_image.file.as_posix(),
                width=thermal_image.width,
                height=thermal_image.height,
            ),
            content_type="diagram",
        )
