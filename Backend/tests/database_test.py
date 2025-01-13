# tests/database_tests.py handles tests for database class

import pytest
import os
import json
from modules.database import Database, Data
import dotenv

dotenv.load_dotenv()


@pytest.fixture
def database():
    db = Database()
    return db


# Test creating a Data object and verifying it can be saved to the database.
def test_create_data(database):
    data = database.create_data("ticker", "AMZN")
    assert isinstance(data, Data)


# Test upserting data into the database and validate its persistence.
def test_upsert_data(database):

    data = Data(_type="ticker", _stock_ticker="AMZN")
    data.set_value("data_today", [10, 45, 34])
    data.set_value("data_history", [20, 30, 40])
    database.upsert_data("AMZN", data)

    # Retrieve data without get_data
    response = (
        database._Database__client.table("final_db")
        .select("*")
        .eq("stock_ticker", "AMZN")
        .execute()
    )

    # Verify response from db is valid
    assert response.data is not None, "Upserted data not found in the database"
    assert len(response.data) == 1
    assert response.data[0]["data"] == str(data)


# Test retrieving data from the database and verify the returned Data object.
def test_get_data(database):

    # Retrieve the data using the get_data method
    retrieved_data = database.get_data("final_db", "AMZN")

    # Validate the retrieved Data object
    assert isinstance(retrieved_data, Data)
