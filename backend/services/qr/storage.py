import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StoredShareAssets:
    image_path: str
    page_path: str


class LocalShareStorage:
    """Stores QR share assets beneath one path-confined local directory."""

    def __init__(self, root: Path | str = "shared_content/shares") -> None:
        self.root = Path(root).resolve()

    def store_assets(
        self,
        token: str,
        image_path: Path,
        page_html: str,
    ) -> StoredShareAssets:
        share_directory = self._resolve(token)
        image_target = share_directory / "image.png"
        page_target = share_directory / "index.html"
        try:
            share_directory.mkdir(parents=True, exist_ok=False)
            shutil.copyfile(image_path, image_target)
            page_target.write_text(page_html, encoding="utf-8")
        except Exception:
            if share_directory.is_dir():
                shutil.rmtree(share_directory)
            raise

        return StoredShareAssets(
            image_path=image_target.as_posix(),
            page_path=page_target.as_posix(),
        )

    def resolve_asset(self, asset_path: str | Path) -> Path:
        candidate = Path(asset_path)
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        resolved = candidate.resolve()
        if not resolved.is_relative_to(self.root):
            raise ValueError("Share asset path is outside local share storage.")
        return resolved

    def assets_exist(self, image_path: str, page_path: str) -> bool:
        try:
            return (
                self.resolve_asset(image_path).is_file()
                and self.resolve_asset(page_path).is_file()
            )
        except ValueError:
            return False

    def delete_assets(self, image_path: str, page_path: str) -> None:
        image = self.resolve_asset(image_path)
        page = self.resolve_asset(page_path)
        directories = {image.parent, page.parent}
        for asset in (image, page):
            asset.unlink(missing_ok=True)
        for directory in directories:
            if directory != self.root:
                try:
                    directory.rmdir()
                except (FileNotFoundError, OSError):
                    pass

    def _resolve(self, relative_path: str | Path) -> Path:
        resolved = (self.root / relative_path).resolve()
        if not resolved.is_relative_to(self.root):
            raise ValueError("Share path is outside local share storage.")
        return resolved
