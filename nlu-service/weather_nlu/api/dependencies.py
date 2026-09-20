from datetime import date, datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends

from weather_nlu.extractor import QuestionExtractor


VIETNAM_TIMEZONE = timezone(timedelta(hours=7))
_extractor: QuestionExtractor | None = None


def set_extractor(extractor: QuestionExtractor | None) -> None:
    global _extractor
    _extractor = extractor


def get_extractor() -> QuestionExtractor:
    if _extractor is None:
        raise RuntimeError("Bộ đọc câu hỏi chưa được nạp")
    return _extractor


def get_reference_date() -> date:
    return datetime.now(VIETNAM_TIMEZONE).date()


Extractor = Annotated[QuestionExtractor, Depends(get_extractor)]
ReferenceDate = Annotated[date, Depends(get_reference_date)]
