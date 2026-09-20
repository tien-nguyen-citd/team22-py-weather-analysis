import os
from dataclasses import dataclass
from pathlib import Path

from weather_nlu.paths import MODELS_DIR


# Đặt trước khi import huggingface_hub để model luôn nằm trong nlu-service/.models.
os.environ.setdefault("HF_HOME", str(MODELS_DIR / "huggingface"))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


@dataclass(frozen=True)
class ModelFiles:
    """Một repo trên Hugging Face và các file cần tải."""

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
