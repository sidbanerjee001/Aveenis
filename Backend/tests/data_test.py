# tests/data_tests.py handles tests data class

import json
from modules.database import Data
import pytest

# Mock templates for testing
templates = {"ticker": {"mentions": [], "post_ids": [], "updated_at": ""}}


@pytest.fixture
def mock_data():
    return Data(_type="ticker", _stock_ticker="AAPL")


def test_data_get_value(mock_data):
    assert mock_data.get_value("stock_ticker") == "AAPL"
    assert mock_data.get_value("mentions") == []
    assert mock_data.get_value("post_ids") == []
    assert mock_data.get_value("updated_at") == ""
    assert mock_data.get_value("type") == "ticker"


def test_data_set_value(mock_data):
    mock_data.set_value("stock_ticker", "GOOG")
    assert mock_data.get_value("stock_ticker") == "GOOG"
    mock_data.set_value("mentions", [1, 2, 3])
    assert mock_data.get_value("mentions") == [1, 2, 3]
    mock_data.set_value("updated_at", "2023-10-01T12:00:00Z")
    assert mock_data.get_value("updated_at") == "2023-10-01T12:00:00Z"


def test_data_append_value(mock_data):
    mock_data.append_value("post_ids", "post_1")
    assert mock_data.get_value("post_ids") == ["post_1"]
    mock_data.append_value("post_ids", "post_2")
    assert mock_data.get_value("post_ids") == ["post_1", "post_2"]


def test_data_remove_value(mock_data):
    mock_data.append_value("post_ids", "post_1")
    mock_data.append_value("post_ids", "post_2")
    mock_data.remove_value("post_ids", "post_1")
    assert mock_data.get_value("post_ids") == ["post_2"]


def test_data_pop_value(mock_data):
    mock_data.append_value("post_ids", "post_1")
    mock_data.append_value("post_ids", "post_2")
    popped_value = mock_data.pop_value("post_ids", 0)
    assert popped_value == "post_1"
    assert mock_data.get_value("post_ids") == ["post_2"]


def test_data_clear_value(mock_data):
    mock_data.append_value("post_ids", "post_1")
    mock_data.append_value("post_ids", "post_2")
    mock_data.clear_value("post_ids")
    assert mock_data.get_value("post_ids") == []


def test_data_str(mock_data):
    expected = json.dumps({"mentions": [], "post_ids": [], "updated_at": ""})
    assert str(mock_data) == expected
