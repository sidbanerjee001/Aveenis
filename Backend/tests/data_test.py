# tests/data_tests.py tests the Data class

import json
from modules.database import Data
import pytest

# Mock templates for testing
templates = {"ticker": {"score": 0}}


# Fixture to create a mock Data object
@pytest.fixture
def mock_data():
    # Create a Data object with type 'ticker' and stock ticker 'AAPL'
    return Data(_type="ticker", _stock_ticker="AAPL")


# Test to check value retrieval from the Data object
def test_data_get_value(mock_data):
    assert mock_data.get_value("stock_ticker") == "AAPL"
    # assert mock_data.get_value("mentions") == []
    # assert mock_data.get_value("post_ids") == []
    # assert mock_data.get_value("updated_at") == ""
    # assert mock_data.get_value("type") == "ticker"


# Test to check setting values in the Data object
def test_data_set_value(mock_data):
    mock_data.set_value("stock_ticker", "GOOG")
    assert mock_data.get_value("stock_ticker") == "GOOG"
    # mock_data.set_value("mentions", [1, 2, 3])
    # assert mock_data.get_value("mentions") == [1, 2, 3]
    # mock_data.set_value("updated_at", "2023-10-01T12:00:00Z")
    # assert mock_data.get_value("updated_at") == "2023-10-01T12:00:00Z"
    mock_data.set_value("score", 10)
    assert mock_data.get_value("score") == 10

# # Test to check appending values to a list in the Data object
# def test_data_append_value(mock_data):
#     mock_data.append_value("post_ids", "post_1")
#     assert mock_data.get_value("post_ids") == ["post_1"]
#     mock_data.append_value("post_ids", "post_2")
#     assert mock_data.get_value("post_ids") == ["post_1", "post_2"]


# # Test to check removing values from a list in the Data object
# def test_data_remove_value(mock_data):
#     mock_data.append_value("post_ids", "post_1")
#     mock_data.append_value("post_ids", "post_2")
#     mock_data.remove_value("post_ids", "post_1")
#     assert mock_data.get_value("post_ids") == ["post_2"]


# # Test to check popping values from a list in the Data object
# def test_data_pop_value(mock_data):
#     mock_data.append_value("post_ids", "post_1")
#     mock_data.append_value("post_ids", "post_2")
#     popped_value = mock_data.pop_value("post_ids", 0)
#     assert popped_value == "post_1"
#     assert mock_data.get_value("post_ids") == ["post_2"]


# # Test to check clearing values from a list in the Data object
# def test_data_clear_value(mock_data):
#     mock_data.append_value("post_ids", "post_1")
#     mock_data.append_value("post_ids", "post_2")
#     mock_data.clear_value("post_ids")
#     assert mock_data.get_value("post_ids") == []


# Test to check the string representation of the Data object
def test_data_str(mock_data):
    expected = json.dumps({"score": 0})
    assert str(mock_data) == expected
