import os
import json
from modules.database import Database, Data
import dotenv

# load env vars
dotenv.load_dotenv()

# init database instance
db = Database()

# retrieving current scores for AMZN in db
amzn_data = db.get_data("final_db", "AMZN")

# add current score to data
amzn_data.append_value("data_today", 49)

# uploading updated data back to db
db.upsert_data("AMZN", amzn_data)
