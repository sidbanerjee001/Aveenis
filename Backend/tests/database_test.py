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


# Test creating a Data object and verifying it can be saved to the database.
def test_create_data(database):
    data = database.create_data("ticker", "AAPL")
    assert isinstance(data, Data)


# Test upserting data into the database and validate its persistence.
def test_upsert_data(database):

    data = Data(_type="ticker", _stock_ticker="AAPL")
    data.set_value("score", 10)
    database.upsert_data("AAPL", data)

    # Retrieve data without get_data
    response = (
        database._Database__client.table("ticker")
        .select("*")
        .eq("stock_ticker", "AAPL")
        .execute()
    )

    # Verify response from db is valid
    assert response.data is not None, "Upserted data not found in the database"
    assert len(response.data) == 1
    assert response.data[0]["data"] == str(data)


# Test retrieving data from the database and verify the returned Data object.
def test_get_data(database):

    # Retrieve the data using the get_data method
    retrieved_data = database.get_data("ticker", "AAPL")

    # Validate the retrieved Data object
    assert isinstance(retrieved_data, Data)
