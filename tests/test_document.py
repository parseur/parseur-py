from datetime import datetime
import tempfile
from unittest.mock import MagicMock, patch

import parseur


@patch("parseur.client.requests.get")
def test_list_documents(mock_request, document_list_data):
    # Mock response for the paginated endpoint
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = document_list_data
    mock_request.return_value = mock_response

    # Test parameters
    mailbox_id = 123
    search = "invoice"
    order_by = parseur.DocumentOrderKey.PROCESSED
    ascending = False
    with_result = True
    received_after = datetime(2025, 7, 1, 15, 30)
    received_before = datetime(2025, 7, 2, 8, 0)

    result = list(
        parseur.Document.list(
            mailbox_id=mailbox_id,
            search=search,
            order_by=order_by,
            ascending=ascending,
            received_after=received_after,
            received_before=received_before,
            with_result=with_result,
        )
    )

    # Check that request was made
    assert mock_request.called

    # Extract the URL and query
    args, kwargs = mock_request.call_args
    url = args[0]
    assert url.startswith(f"https://api.parseur.com/parser/{mailbox_id}/document_set")

    # Query parameters
    params = kwargs.get("params")
    assert params is not None

    # Assert all expected parameters are present and correctly encoded
    assert params["search"] == search
    assert params["ordering"] == "-processed"  # because ascending=False
    assert params["with_result"] == "true"
    assert params["received_after"] == "2025-07-01"
    assert params["received_before"] == "2025-07-02"

    assert len(result) == len(document_list_data["results"])
    doc1 = result[0]
    assert doc1.id == doc1["id"] == 2885

    assert doc1.id == doc1["id"] == 2885
    assert doc1.name == doc1["name"] == "scan_philippe.lipack_2025-07-23-11-46-09.pdf"

    assert doc1.status == doc1["status"] == "PARSEDOK"
    assert doc1.status_source == doc1["status_source"] == "AI"

    assert (
        doc1.received
        == doc1["received"]
        == datetime.fromisoformat("2025-07-31T03:09:13.398385+00:00")
    )
    assert (
        doc1.processed
        == doc1["processed"]
        == datetime.fromisoformat("2025-07-31T03:11:15.107217+00:00")
    )

    assert doc1.ai_credits_used == doc1["ai_credits_used"] == 4
    assert doc1.credits_used == doc1["credits_used"] == 4

    assert doc1.is_ai_ready == doc1["is_ai_ready"] is True
    assert doc1.is_ocr_ready == doc1["is_ocr_ready"] is True
    assert doc1.is_processable == doc1["is_processable"] is True
    assert doc1.is_split == doc1["is_split"] is False
    assert doc1.is_splittable == doc1["is_splittable"] is True

    assert doc1.parser == doc1["parser"] == 120
    assert doc1.template == doc1["template"] is None

    assert doc1.attached_to == doc1["attached_to"] is None

    assert (
        doc1.csv_download_url
        == doc1["csv_download_url"]
        == (
            "https://api.parseur.com/document/NUXbecvwY3Xc3J_IMatZsCP1x4x2lwstowfPfhpUayD94ebAcye3qMCqXG0kkq2U/"
            "result/scan_philippe.lipack_2025-07-23-11-46-09.pdf.csv"
        )
    )
    assert (
        doc1.json_download_url
        == doc1["json_download_url"]
        == (
            "https://api.parseur.com/document/NUXbecvwY3Xc3J_IMatZsCP1x4x2lwstowfPfhpUayD94ebAcye3qMCqXG0kkq2U/"
            "result/scan_philippe.lipack_2025-07-23-11-46-09.pdf.json"
        )
    )
    assert (
        doc1.xls_download_url
        == doc1["xls_download_url"]
        == (
            "https://api.parseur.com/document/NUXbecvwY3Xc3J_IMatZsCP1x4x2lwstowfPfhpUayD94ebAcye3qMCqXG0kkq2U/"
            "result/scan_philippe.lipack_2025-07-23-11-46-09.pdf.xlsx"
        )
    )
    assert (
        doc1.original_document_url
        == doc1["original_document_url"]
        == (
            "https://api.parseur.com/document/NUXbecvwY3Xc3J_IMatZsCP1x4x2lwstowfPfhpUayD94ebAcye3qMCqXG0kkq2U/"
            "scan_philippe.lipack_2025-07-23-11-46-09.pdf"
        )
    )
    assert (
        doc1.ocr_ready_url
        == doc1["ocr_ready_url"]
        == (
            "https://api.parseur.com/document/NUXbecvwY3Xc3J_IMatZsCP1x4x2lwstowfPfhpUayD94ebAcye3qMCqXG0kkq2U/"
            "ocr_ready/scan_philippe.lipack_2025-07-23-11-46-09.pdf"
        )
    )


@patch("parseur.client.Client.request")
def test_retrieve_document(mock_request, document_data):
    mock_request.return_value = document_data

    doc = parseur.Document.retrieve(2885)

    mock_request.assert_called_once_with("GET", "/document/2885")

    assert doc.id == doc["id"] == 2885
    assert doc.name == doc["name"] == "scan_philippe.lipack_2025-07-23-11-46-09.pdf"
    assert doc.status == doc["status"] == "PARSEDOK"
    assert doc.status_source == doc["status_source"] == "AI"
    assert doc.parser == doc["parser"] == 120
    assert doc.template == doc["template"] is None

    assert doc.processed.isoformat().startswith("2025-07-31")
    assert doc.received.isoformat().startswith("2025-07-31")

    assert doc.credits_used == doc["credits_used"] == 4
    assert doc.ai_credits_used == doc["ai_credits_used"] == 4

    assert doc.is_ai_ready == doc["is_ai_ready"] is True
    assert doc.is_ocr_ready == doc["is_ocr_ready"] is True
    assert doc.is_processable == doc["is_processable"] is True
    assert doc.is_split == doc["is_split"] is False
    assert doc.is_splittable == doc["is_splittable"] is True

    assert doc.attached_to == doc["attached_to"] is None

    assert doc.original_document_url.endswith(".pdf")
    assert doc.csv_download_url.endswith(".csv")
    assert doc.json_download_url.endswith(".json")
    assert doc.xls_download_url.endswith(".xlsx")


@patch("parseur.client.Client.request")
def test_skip_document(mock_request, document_data):
    mock_request.return_value = document_data

    doc = parseur.Document.skip(2885)

    mock_request.assert_called_once_with("POST", "/document/2885/skip")
    assert doc.id == doc["id"] == 2885
    assert doc.name == doc["name"] == "scan_philippe.lipack_2025-07-23-11-46-09.pdf"


@patch("parseur.client.Client.request")
def test_reprocess_document(mock_request, document_data):
    mock_request.return_value = document_data

    doc = parseur.Document.reprocess(2885)

    mock_request.assert_called_once_with("POST", "/document/2885/process")
    assert doc.id == doc["id"] == 2885
    assert doc.status == doc["status"] == "PARSEDOK"


@patch("parseur.client.Client.request")
def test_copy_document(mock_request, document_data):
    mock_request.return_value = document_data

    doc = parseur.Document.copy(2885, 120)

    mock_request.assert_called_once_with("POST", "/document/2885/copy/120")
    assert doc.id == doc["id"] == 2885
    assert doc.parser == doc["parser"] == 120


@patch("parseur.client.Client.request")
def test_delete_document(mock_request):
    parseur.Document.delete(2885)

    mock_request.assert_called_once_with("DELETE", "/document/2885")


@patch("parseur.client.Client.request")
def test_upload_text_returns_document(mock_request, document_upload_text_data):
    mock_request.return_value = document_upload_text_data
    result = parseur.Document.upload_text(
        recipient="inbox@robot.parseur.com",
        subject="Test Subject",
        sender="me@ex.com",
        body_html="<b>Hello</b>",
        body_plain="Hello",
    )

    mock_request.assert_called_once()
    method, url = mock_request.call_args[0]
    payload = mock_request.call_args[1]["json"]

    assert method == "POST"
    assert url == "/email"

    assert payload["recipient"] == "inbox@robot.parseur.com"
    assert payload["subject"] == "Test Subject"
    assert payload["from"] == "me@ex.com"
    assert payload["body_html"] == "<b>Hello</b>"
    assert payload["body_plain"] == "Hello"

    assert result["message"] == result.message == "OK"
    assert (
        result["DocumentID"] == result.DocumentID == "753ec679789a4b1ebea629f630db6f29"
    )


@patch("parseur.client.Client.request")
def test_upload_file_returns_document(mock_request, document_upload_file_data):
    mock_request.return_value = document_upload_file_data

    with tempfile.NamedTemporaryFile() as fd:
        result = parseur.Document.upload_file(mailbox_id=120, file_path=fd.name)

        mock_request.assert_called_once()
        method, url = mock_request.call_args[0]
        files = mock_request.call_args[1]["files"]

        assert method == "POST"
        assert url == "/parser/120/upload"
        assert files["file"].name == fd.name

        assert result["message"] == result.message == "OK"
        assert (
            result["attachments"]
            == result.attachments
            == [
                {
                    "DocumentID": "daf8799eedc342ff93f824eaeb327171",
                    "name": "April-3765.pdf",
                }
            ]
        )


@patch("parseur.client.requests.get")
def test_document_logs_returns_logs(mock_request, document_log_data):

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = document_log_data
    mock_request.return_value = mock_response

    logs = list(parseur.Document.logs(2898))

    mock_request.assert_called_once()
    args, kwargs = mock_request.call_args
    url = args[0]
    assert url == "https://api.parseur.com/document/2898/log_set"

    assert len(logs) == 2

    log1, log2 = logs

    # Log 1 : PARSEDOK
    assert log1.id == log1["id"] == 6319
    assert log1.code == log1["code"] == "PARSEDOK"
    assert log1.status == log1["status"] == "SUCCESS"
    assert log1.message == log1["message"]
    assert log1.message.startswith("Processed with AI")
    assert log1.document == log1["document"] == 2898

    # Log 2 : INCOMING
    assert log2.id == log2["id"] == 6316
    assert log2.code == log2["code"] == "INCOMING"
    assert log2.status == log2["status"] == "INFO"
    assert log2.message == log2["message"] == "Received"
