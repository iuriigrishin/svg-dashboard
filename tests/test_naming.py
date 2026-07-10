import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sheets.naming import generate_sheet_names


def test_basic_pairs():
    assert generate_sheet_names(2, 2, 2) == ["J1 vs J2", "M1 vs M2", "P1 vs P2"]


def test_multiple_teams_per_league():
    names = generate_sheet_names(4, 2, 0)
    assert names == ["J1 vs J2", "J3 vs J4", "M1 vs M2"]


def test_zero_teams_in_a_league_produces_no_sheets_for_it():
    names = generate_sheet_names(0, 4, 0)
    assert names == ["M1 vs M2", "M3 vs M4"]


@pytest.mark.parametrize("jun,mid,pro", [(3, 2, 2), (2, 5, 2), (2, 2, 7)])
def test_odd_team_count_rejected(jun, mid, pro):
    with pytest.raises(ValueError):
        generate_sheet_names(jun, mid, pro)
