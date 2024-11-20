# tests/database_tests.py handles tests for database class

import pytest
from unittest.mock import MagicMock
import os
import json
from datetime import datetime
from modules.database import Database, Data
import dotenv

dotenv.load_dotenv()


@pytest.fixture
def database():
    db = Database()
    return db


def test_create_data(database):
    """
    Test creating a Data object and verifying it can be saved to the database.
    """
    data = database.create_data("ticker", "AAPL")
    assert isinstance(data, Data)


def test_upsert_data(database):
    """
    Test upserting data into the database and validate its persistence.
    """
    data = Data(_type="ticker", _stock_ticker="AAPL")
    data.set_value("mentions", [5, 10, 15])
    database.upsert_data("AAPL", data)

    response = (
        database._Database__client.table("ticker")
        .select("*")
        .eq("stock_ticker", "AAPL")
        .execute()
    )

    assert response.data is not None, "Upserted data not found in the database"
    assert len(response.data) == 1
    assert response.data[0]["data"] == str(data)


def test_get_data(database):
    """
    Test retrieving data from the database and verify the returned Data object.
    """

    # Retrieve the data using the get_data method
    retrieved_data = database.get_data("ticker", "AAPL")

    # Validate the retrieved Data object
    assert isinstance(retrieved_data, Data)
