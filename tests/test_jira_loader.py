from datetime import date
from src.loaders.jira_loader import load_developer_map, load_deliverables_csv, load_bugs_csv

DEV_MAP_FIXTURE = "tests/fixtures/developers.csv"
DELIVERABLES_FIXTURE = "tests/fixtures/jira_deliverables.csv"
BUGS_FIXTURE = "tests/fixtures/jira_bugs.csv"


def test_developer_map_keys_are_lowercase():
    dm = load_developer_map(DEV_MAP_FIXTURE)
    for key in dm:
        assert key == key.lower()


def test_developer_map_values_are_emails():
    dm = load_developer_map(DEV_MAP_FIXTURE)
    assert dm["navneet shukla"] == "navneet.shukla@cashflo.io"
    assert dm["shiva kumar swami"] == "shivakumar.swami@cashflo.io"


def test_loads_five_deliverables():
    dm = load_developer_map(DEV_MAP_FIXTURE)
    records = load_deliverables_csv(DELIVERABLES_FIXTURE, dm)
    assert len(records) == 5


def test_deliverable_email_resolved_from_display_name():
    dm = load_developer_map(DEV_MAP_FIXTURE)
    records = load_deliverables_csv(DELIVERABLES_FIXTURE, dm)
    navneet_records = [r for r in records if r.email == "navneet.shukla@cashflo.io"]
    assert len(navneet_records) == 2


def test_deliverable_missing_story_points_is_none():
    dm = load_developer_map(DEV_MAP_FIXTURE)
    records = load_deliverables_csv(DELIVERABLES_FIXTURE, dm)
    cash_102 = next(r for r in records if r.issue_key == "CASH-102")
    assert cash_102.story_points is None


def test_deliverable_resolved_date_parsed():
    dm = load_developer_map(DEV_MAP_FIXTURE)
    records = load_deliverables_csv(DELIVERABLES_FIXTURE, dm)
    cash_101 = next(r for r in records if r.issue_key == "CASH-101")
    assert cash_101.resolved_date == date(2026, 5, 15)


def test_loads_three_bugs():
    dm = load_developer_map(DEV_MAP_FIXTURE)
    bugs = load_bugs_csv(BUGS_FIXTURE, dm)
    assert len(bugs) == 3


def test_bug_email_resolved_from_display_name():
    dm = load_developer_map(DEV_MAP_FIXTURE)
    bugs = load_bugs_csv(BUGS_FIXTURE, dm)
    navneet_bugs = [b for b in bugs if b.email == "navneet.shukla@cashflo.io"]
    assert len(navneet_bugs) == 1


def test_bug_created_date_parsed():
    dm = load_developer_map(DEV_MAP_FIXTURE)
    bugs = load_bugs_csv(BUGS_FIXTURE, dm)
    bug_201 = next(b for b in bugs if b.issue_key == "BUG-201")
    assert bug_201.created_date == date(2026, 5, 20)
