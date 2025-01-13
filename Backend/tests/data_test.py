# tests/data_tests.py tests the Data class

import json
from modules.database import Data
import pytest

# Mock templates for testing
templates = {"ticker": {"data_today": [10, 11, 13], "data_history": [3, 45, 34]}}


# Fixture to create a mock Data object
@pytest.fixture
def mock_data():
    # Create a Data object with type 'ticker' and stock ticker 'AAPL'
    return Data(_type="ticker", _stock_ticker="AAPL")


# Test to check value retrieval from the Data object
def test_data_get_value(mock_data):
    assert mock_data.get_value("stock_ticker") == "AAPL"


# Test to check setting values in the Data object
def test_data_set_value(mock_data):
    mock_data.set_value("stock_ticker", "GOOG")
    assert mock_data.get_value("stock_ticker") == "GOOG"
    mock_data.set_value("data_today", [10, 34, 5])
    assert mock_data.get_value("data_today") == [10, 34, 5]
    mock_data.set_value("data_history", [20, 45, 8])
    assert mock_data.get_value("data_history") == [20, 45, 8]


# # Test to check appending values to a list in the Data object
def test_data_append_value(mock_data):
    mock_data.append_value("data_today", 100)
    assert mock_data.get_value("data_today") == [100]
    mock_data.append_value("data_today", 50)
    assert mock_data.get_value("data_today") == [100, 50]

    mock_data.append_value("data_history", 200)
    assert mock_data.get_value("data_history") == [200]
    mock_data.append_value("data_history", 150)
    assert mock_data.get_value("data_history") == [200, 150]


# Test to check removing values from a list in the Data object
def test_data_remove_value(mock_data):
    mock_data.set_value("data_today", [10, 34, 5])
    mock_data.append_value("data_today", 100)
    mock_data.remove_value("data_today", 34)
    assert mock_data.get_value("data_today") == [10, 5, 100]

    mock_data.set_value("data_history", [20, 45, 8])
    mock_data.append_value("data_history", 200)
    mock_data.remove_value("data_history", 45)
    assert mock_data.get_value("data_history") == [20, 8, 200]


# Test to check popping values from a list in the Data object
def test_data_pop_value(mock_data):
    mock_data.set_value("data_today", [10, 34, 5])
    mock_data.append_value("data_today", 100)
    popped_value = mock_data.pop_value("data_today", 0)
    assert popped_value == 10
    assert mock_data.get_value("data_today") == [34, 5, 100]

    mock_data.set_value("data_history", [20, 45, 8])
    mock_data.append_value("data_history", 200)
    popped_value = mock_data.pop_value("data_history", 0)
    assert popped_value == 20
    assert mock_data.get_value("data_history") == [45, 8, 200]


# Test to check clearing values from a list in the Data object
def test_data_clear_value(mock_data):
    mock_data.set_value("data_today", [10, 34, 5])
    mock_data.append_value("data_today", 100)
    mock_data.clear_value("data_today")
    assert mock_data.get_value("data_today") == []

    mock_data.set_value("data_history", [20, 45, 8])
    mock_data.append_value("data_history", 200)
    mock_data.clear_value("data_history")
    assert mock_data.get_value("data_history") == []


# Test to check the string representation of the Data object
def test_data_str(mock_data):
    expected = json.dumps({"data_today": [], "data_history": []})
    assert str(mock_data) == expected
