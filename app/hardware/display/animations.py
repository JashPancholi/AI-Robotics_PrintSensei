def progress_bar(progress: float, segments: int = 10) -> str:
    bounded = min(max(progress, 0.0), 1.0)
    filled = round(bounded * segments)
    return "#" * filled + "-" * (segments - filled)
