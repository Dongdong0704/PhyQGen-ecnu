"""Stable entry points for the question-generation subsystem."""

from knowledge import knowledge_status

from agents.common import QUESTION_TIMEOUT_SECONDS
from agents.connections import test_connection
from agents.model_gateway import GenerationError
from agents.workflow import generate_question, question_graph


__all__ = [
    "GenerationError",
    "QUESTION_TIMEOUT_SECONDS",
    "generate_question",
    "knowledge_status",
    "question_graph",
    "test_connection",
]
