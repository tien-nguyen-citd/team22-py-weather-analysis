from collections.abc import Callable
from dataclasses import dataclass

from weather_chatbot.activities import (
    ActivityKeywordMatcher,
    load_activities,
    load_activity_examples,
)
from weather_chatbot.extractors.base import QuestionExtractor
from weather_chatbot.extractors.embedding import (
    MINILM_MODEL,
    POTION_MODEL,
    EmbeddingExtractor,
    MiniLmEncoder,
    Model2VecEncoder,
)
from weather_chatbot.extractors.gliner_ner import (
    GLINER_MULTI_MODEL,
    GLINER_X_SMALL_MODEL,
    MDEBERTA_TOKENIZER,
    GlinerExtractor,
    load_gliner_multi,
    load_gliner_x_small,
)
from weather_chatbot.extractors.rule_based import RuleBasedExtractor
from weather_chatbot.extractors.small_llm import QWEN_MODEL, SmallLlmExtractor
from weather_chatbot.locations import LocationMatcher, load_locations
from weather_chatbot.models import ModelFiles


@dataclass(frozen=True)
class ExtractorSpec:
    name: str
    description: str
    models: tuple[ModelFiles, ...]
    create: Callable[[], QuestionExtractor]


def create_rule_based() -> QuestionExtractor:
    return RuleBasedExtractor(
        LocationMatcher(load_locations()), ActivityKeywordMatcher(load_activities())
    )


def create_model2vec() -> QuestionExtractor:
    return EmbeddingExtractor(
        "model2vec",
        Model2VecEncoder(),
        load_activity_examples(),
        LocationMatcher(load_locations()),
    )


def create_rule_and_model2vec() -> QuestionExtractor:
    return EmbeddingExtractor(
        "rule+model2vec",
        Model2VecEncoder(),
        load_activity_examples(),
        LocationMatcher(load_locations()),
        keywords=ActivityKeywordMatcher(load_activities()),
    )


def create_minilm() -> QuestionExtractor:
    return EmbeddingExtractor(
        "minilm",
        MiniLmEncoder(),
        load_activity_examples(),
        LocationMatcher(load_locations()),
    )


def create_rule_and_minilm() -> QuestionExtractor:
    return EmbeddingExtractor(
        "rule+minilm",
        MiniLmEncoder(),
        load_activity_examples(),
        LocationMatcher(load_locations()),
        keywords=ActivityKeywordMatcher(load_activities()),
    )


def create_gliner_x_small() -> QuestionExtractor:
    return GlinerExtractor(
        "gliner-x-small",
        load_gliner_x_small(),
        LocationMatcher(load_locations()),
        ActivityKeywordMatcher(load_activities()),
    )


def create_gliner_multi() -> QuestionExtractor:
    return GlinerExtractor(
        "gliner-multi",
        load_gliner_multi(),
        LocationMatcher(load_locations()),
        ActivityKeywordMatcher(load_activities()),
    )


def create_small_llm() -> QuestionExtractor:
    return SmallLlmExtractor(LocationMatcher(load_locations()), load_activities())


EXTRACTORS = {
    spec.name: spec
    for spec in [
        ExtractorSpec("rule", "Không dùng ML: từ điển và luật", (), create_rule_based),
        ExtractorSpec(
            "model2vec", "Embedding tĩnh phân loại hoạt động", (POTION_MODEL,), create_model2vec
        ),
        ExtractorSpec(
            "minilm", "Embedding MiniLM (ONNX) phân loại hoạt động", (MINILM_MODEL,), create_minilm
        ),
        ExtractorSpec(
            "rule+model2vec",
            "Từ khóa trước, không khớp thì dùng model2vec",
            (POTION_MODEL,),
            create_rule_and_model2vec,
        ),
        ExtractorSpec(
            "rule+minilm",
            "Từ khóa trước, không khớp thì dùng MiniLM",
            (MINILM_MODEL,),
            create_rule_and_minilm,
        ),
        ExtractorSpec(
            "gliner-x-small",
            "Zero-shot NER, ONNX quantized",
            (GLINER_X_SMALL_MODEL,),
            create_gliner_x_small,
        ),
        ExtractorSpec(
            "gliner-multi",
            "Zero-shot NER, PyTorch",
            (GLINER_MULTI_MODEL, MDEBERTA_TOKENIZER),
            create_gliner_multi,
        ),
        ExtractorSpec(
            "qwen-0.5b", "LLM nhỏ trả về JSON", (QWEN_MODEL,), create_small_llm
        ),
    ]
}
