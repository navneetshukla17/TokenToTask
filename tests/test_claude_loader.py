import pytest
from src.loaders.claude_loader import load_claude_csv

FIXTURE = "tests/fixtures/claude_export.csv"


def test_loads_three_developers():
    result = load_claude_csv(FIXTURE)
    assert len(result) == 3


def test_excludes_api_keys():
    result = load_claude_csv(FIXTURE)
    assert "claude_key [api key]" not in result
    assert "aditya-sales-key [api key]" not in result


def test_parses_spend_correctly():
    result = load_claude_csv(FIXTURE)
    assert result["navneet.shukla@cashflo.io"]["spend_usd"] == pytest.approx(335.06)
    assert result["chetan.nikam@cashflo.io"]["spend_usd"] == pytest.approx(608.37)


def test_parses_lines_with_comma_separator():
    result = load_claude_csv(FIXTURE)
    assert result["navneet.shukla@cashflo.io"]["lines_of_code"] == 42068
    assert result["shivakumar.swami@cashflo.io"]["lines_of_code"] == 86203


def test_emails_are_lowercased():
    result = load_claude_csv(FIXTURE)
    for email in result:
        assert email == email.lower()
