# modules/database.py will handle all interaction with database (supabase)

import os
import json
import copy
from supabase import create_client
import datetime

# Import all templates into a dict
templates = {}
for filename in os.listdir("data_template/"):
    if filename.endswith(".json"):
        with open(f"data_template/{filename}", "r") as f:
            templates[filename[:-5]] = json.load(f)


class Data:
    def __init__(self, _type: str, _data: dict = None, _stock_ticker: str = None):
        """
        Initialize a new Data object with the given type, id, and data.

        Args:
            _type (str): The type of data to load (e.g. ticker).
            _stock_ticker (str): The ticker for the stock entry. (e.g AAPL, GOOG)
            _data (str): The data to load as a JSON string. If None, the default
                template for the given type will be used.

        Raises:
            FileNotFoundError: If the default template for the given type does
                not exist.
        """
        file_path = f"data_template/{_type}.json"
        assert os.path.exists(file_path)

        self.__type = _type

        # Return copied template data if no input data is provided
        if not _data:
            assert _stock_ticker is not None
            self.__data = copy.deepcopy(templates[_type])
            self.__stock_ticker = _stock_ticker
            return

        # Load fields from input data
        self.__data = json.loads(_data["data"])
        self.__stock_ticker = _data["stock_ticker"]

        # Check for any updates from template
        for key, value in templates[_type].items():
            if key not in self.__data:
                self.__data[key] = value

    def get_value(self, _key: str):
        """
        Return the value associated with the given key.

        Args:
            _key (str): The key to retrieve the value for.

        Returns:
            object: The value associated with the given key.
        """
        if _key == "stock_ticker":
            return self.__stock_ticker
        elif _key == "type":
            return self.__type
        else:
            return self.__data[_key]

    def set_value(self, _key: str, _value):
        """
        Set the value associated with the given key.

        Args:
            _key (str): The key to set the value for.
            _value: The value to set.

        """
        if _key == "stock_ticker":
            self.__stock_ticker = _value
            return

        assert _key in self.__data
        self.__data[_key] = _value

    def append_value(self, _key: str, _value):
        """
        Append a value to the end of the list associated with the given key.

        Args:
            _key (str): The key to append the value to.
            _value (object): The value to append.
        """

        assert _key in self.__data
        assert isinstance(self.__data[_key], list)
        self.__data[_key].append(_value)

    def remove_value(self, _key: str, _value):
        """
        Remove a value from the list associated with the given key.

        Args:
            _key (str): The key to remove the value from.
            _value (object): The value to remove.
        """

        assert _key in self.__data
        assert isinstance(self.__data[_key], list)
        self.__data[_key].remove(_value)

    def pop_value(self, _key: str, _index: int):
        """
        Pop a value from the list associated with the given key.

        Args:
            _key (str): The key to remove the element from.
            _index (int): The index of the element to pop.
        """

        assert _key in self.__data
        assert isinstance(self.__data[_key], list)
        assert _index < len(self.__data[_key])
        return self.__data[_key].pop(_index)

    def clear_value(self, _key: str):
        """
        Remove all values from the list associated with the given key.

        Args:
            _key (str): The key to remove all values from.
        """

        assert _key in self.__data
        assert isinstance(self.__data[_key], list)
        self.__data[_key] = []

    def __str__(self):
        """
        Return a string representation of this Data object as a JSON string.

        Returns:
            str: A JSON string representing this Data object.
        """
        return json.dumps(self.__data)

    def __ret__(self):
        """
        Use str(Data) instead to get the string representation of the Data object

        Raises:
            NotImplementedError: Always, as this method should not be used.
        """

        raise NotImplementedError(
            "Use str(Data) instead to get the string representation of the Data object"
        )


class Database:
    def __init__(self):
        """
        Initialize a new Database object with the given URL and key.

        Raises:
            AssertionError: If the SUPABASE_URL or SUPABASE_KEY environment variables are not set.
        """
        self.__client = create_client(
            os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")
        )

    #! Database data creation
    def create_data(self, _table_name: str, _stock_ticker: str):
        """
        Create a new Data object with the given type and id.

        Args:
            _table_name (str): The type of data to create (e.g. ticker).
            _stock_ticker (str): The ticker of the stock entry. (e.g. AAPL, GOOG)

        Returns:
            Data: A new Data object with the given type and id.
        """

        return Data(_table_name, _stock_ticker=_stock_ticker)

    #! Database data retrieval
    def get_data(self, _table_name: str, _stock_ticker: str):
        """
        Retrieve a row from the specified table by the given ID.

        Args:
            _table_name (str): The name of the table to retrieve the row from.
            _id (int): The ID of the row to retrieve.

        Returns:
            Data: The retrieved row from the database represented as a Data object.
        """
        response = (
            self.__client.table(_table_name)
            .select("*")
            .eq("stock_ticker", _stock_ticker)
            .execute()
            .data
        )

        return (
            Data(
                _table_name,
                response[0],
            )
            if response
            else None
        )

    def upsert_data(self, _stock_ticker: str, _data: Data):
        """
        Update a row in the database with the given Data object.

        If the row does not exist, it will be inserted into the database.

        Args:
            _data (Data): The Data object to upsert in the database.
        """

        # Update the updated_at field
        # _data.set_value("updated_at", str(datetime.datetime.now(datetime.UTC)))

        # Update the data in the database
        self.__client.table(_data.get_value("type")).upsert(
            {"stock_ticker": _stock_ticker, "data": str(_data)}
        ).execute()
