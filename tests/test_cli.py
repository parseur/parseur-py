from unittest.mock import patch

from click.testing import CliRunner

from parseur.cli import cli


def test_list_parser_fields():
    runner = CliRunner()
    with patch("parseur.ParserField.list", return_value=[{"id": "PF1"}]) as mock_list:
        result = runner.invoke(cli, ["list-parser-fields", "123"])

    assert result.exit_code == 0
    mock_list.assert_called_once_with(123)
    assert '"id": "PF1"' in result.output


def test_list_export_configs():
    runner = CliRunner()
    with patch("parseur.ExportConfig.list", return_value=[{"id": 10}]) as mock_list:
        result = runner.invoke(cli, ["list-export-configs", "123"])

    assert result.exit_code == 0
    mock_list.assert_called_once_with(123)
    assert '"id": 10' in result.output


def test_download_mailbox_to_stdout():
    runner = CliRunner()
    with patch("parseur.Mailbox.download", return_value=b"a,b\n1,2\n") as mock_dl:
        result = runner.invoke(cli, ["download-mailbox", "123"])

    assert result.exit_code == 0
    mock_dl.assert_called_once_with(123, "csv")
    assert result.stdout_bytes == b"a,b\n1,2\n"


def test_download_mailbox_to_file():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with patch("parseur.Mailbox.download", return_value=b"x") as mock_dl:
            result = runner.invoke(
                cli, ["download-mailbox", "123", "--format", "xlsx", "-o", "out.xlsx"]
            )
        assert result.exit_code == 0
        mock_dl.assert_called_once_with(123, "xlsx")
        with open("out.xlsx", "rb") as fh:
            assert fh.read() == b"x"


def test_download_field():
    runner = CliRunner()
    with patch("parseur.ParserField.download", return_value=b"ItemCode\n") as mock_dl:
        result = runner.invoke(cli, ["download-field", "123", "PF951"])

    assert result.exit_code == 0
    mock_dl.assert_called_once_with(123, "PF951", "csv")
    assert result.stdout_bytes == b"ItemCode\n"


def test_download_export():
    runner = CliRunner()
    with patch("parseur.ExportConfig.download", return_value=b"col\n") as mock_dl:
        result = runner.invoke(cli, ["download-export", "123", "10", "--format", "csv"])

    assert result.exit_code == 0
    mock_dl.assert_called_once_with(123, 10, "csv")


def test_download_rejects_bad_format():
    runner = CliRunner()
    result = runner.invoke(cli, ["download-mailbox", "123", "--format", "pdf"])
    assert result.exit_code != 0
