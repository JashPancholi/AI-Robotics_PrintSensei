from app.enums.input_type import InputType
from app.enums.intent import Intent
from app.enums.label_type import LabelType
from app.enums.status import Status
from app.models.label_data import LabelData
from app.models.print_request import PrintRequest


def create_fake_print_request(text: str) -> tuple[PrintRequest, LabelData]:
    intent = _detect_intent(text)
    label_type = _label_type_for_intent(intent)

    print_request = PrintRequest(
        raw_input=text,
        input_type=InputType.TEXT,
        intent=intent,
        status=Status.PROCESSING,
    )
    label_data = LabelData(
        title=_title_for_text(text, intent),
        body=text,
        qr_data=_extract_qr_data(text) if intent is Intent.QR else None,
        label_type=label_type,
        metadata={"source": "fake_request_generator"},
    )

    return print_request, label_data


def _detect_intent(text: str) -> Intent:
    normalized = text.lower()

    if "qr" in normalized or "qrcode" in normalized:
        return Intent.QR
    if "inventory" in normalized or "stock" in normalized:
        return Intent.INVENTORY
    if "study" in normalized or "flashcard" in normalized:
        return Intent.STUDY
    if "product" in normalized or "price" in normalized:
        return Intent.PRODUCT
    if "ocr" in normalized or "scan" in normalized:
        return Intent.OCR

    return Intent.UNKNOWN


def _label_type_for_intent(intent: Intent) -> LabelType:
    mapping = {
        Intent.STUDY: LabelType.STUDY,
        Intent.INVENTORY: LabelType.INVENTORY,
        Intent.PRODUCT: LabelType.PRODUCT,
        Intent.QR: LabelType.QR,
        Intent.OCR: LabelType.CUSTOM,
        Intent.UNKNOWN: LabelType.CUSTOM,
    }
    return mapping[intent]


def _title_for_text(text: str, intent: Intent) -> str:
    normalized = text.strip()
    if intent is Intent.INVENTORY and " for " in normalized.lower():
        return normalized.lower().split(" for ", maxsplit=1)[1].title()
    if intent is Intent.QR:
        return "QR Code"
    if intent is Intent.UNKNOWN:
        return "Custom Label"
    return intent.value.title()


def _extract_qr_data(text: str) -> str:
    words = text.split()
    return words[-1] if words else text
