import pytest
from pydantic import ValidationError

from ghost_shield.connectors import DeletionReport, Document, QueryResult


def test_document_serialization_and_defaults() -> None:
    document = Document(id="doc-1", text="private text")

    assert document.model_dump() == {
        "id": "doc-1",
        "text": "private text",
        "metadata": {},
        "vector": None,
    }
    assert document.model_dump_json()


def test_document_metadata_defaults_are_isolated() -> None:
    first = Document(id="doc-1", text="one")
    second = Document(id="doc-2", text="two")

    first.metadata["source"] = "upload"

    assert second.metadata == {}


def test_query_result_and_deletion_report_defaults() -> None:
    document = Document(id="doc-1", text="private text", vector=[0.1, 0.2])
    result = QueryResult(document=document, score=0.92)
    report = DeletionReport(
        id="doc-1",
        soft_deleted=True,
        hard_purged=False,
        residual_artifacts_found=False,
        details="Marked deleted in the connector index.",
    )

    assert result.is_soft_deleted is False
    assert result.document.vector == [0.1, 0.2]
    assert report.model_dump()["hard_purged"] is False


def test_required_fields_and_types_are_validated() -> None:
    with pytest.raises(ValidationError):
        Document(text="missing id")

    with pytest.raises(ValidationError):
        QueryResult(document={"id": "doc-1", "text": "text"}, score="not-a-score")

    with pytest.raises(ValidationError):
        DeletionReport(
            id="doc-1",
            soft_deleted=True,
            hard_purged=False,
            residual_artifacts_found=False,
        )
