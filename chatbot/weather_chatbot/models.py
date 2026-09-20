import os
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

from weather_chatbot.paths import MODELS_DIR


# Phải đặt trước khi import huggingface_hub (kể cả gián tiếp qua transformers, gliner)
# để mọi model đều nằm trong chatbot/.models, dễ đo dung lượng và dễ xóa.
os.environ.setdefault("HF_HOME", str(MODELS_DIR / "huggingface"))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


@dataclass(frozen=True)
class ModelFiles:
    """Một repo trên Hugging Face và các file cần tải (để trống là tải cả repo)."""

    repo_id: str
    allow_patterns: tuple[str, ...] = ()


def download_model(model: ModelFiles) -> Path:
    """Tải model nếu chưa có, trả về thư mục chứa file của model."""
    from huggingface_hub import snapshot_download

    return Path(
        snapshot_download(model.repo_id, allow_patterns=list(model.allow_patterns) or None)
    )


def find_downloaded_model(model: ModelFiles) -> Path | None:
    """Trả về thư mục model đã tải, hoặc None nếu chưa tải."""
    from huggingface_hub import snapshot_download
    from huggingface_hub.errors import LocalEntryNotFoundError

    try:
        return Path(
            snapshot_download(
                model.repo_id,
                allow_patterns=list(model.allow_patterns) or None,
                local_files_only=True,
            )
        )
    except LocalEntryNotFoundError:
        return None


def model_size_mb(model: ModelFiles, folder: Path) -> float:
    """Dung lượng các file cần dùng của model (không tính file khác lỡ tải về)."""
    total_bytes = 0
    for path in folder.rglob("*"):
        relative_path = path.relative_to(folder).as_posix()
        needed = not model.allow_patterns or any(
            fnmatch(relative_path, pattern) for pattern in model.allow_patterns
        )
        if path.is_file() and needed:
            total_bytes += path.stat().st_size
    return total_bytes / 1024**2


def downloaded_size_mb(models: list[ModelFiles]) -> float:
    """Tổng dung lượng các model đã tải, model chưa tải được tính là 0."""
    total = 0.0
    for model in models:
        folder = find_downloaded_model(model)
        if folder is not None:
            total += model_size_mb(model, folder)
    return total
