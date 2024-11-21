from supabase import create_client, Client
import os
from dotenv import load_dotenv
import uuid
import logging

load_dotenv()

# Set up logger
server_logger = logging.getLogger(__name__)
server_logger.setLevel(logging.INFO)
server_handler = logging.FileHandler('serverLogging.log')
server_handler.setLevel(logging.INFO)
server_formatter = logging.Formatter(
    "{asctime} - {levelname} - {message}", style="{", datefmt="%Y-%m-%d %H:%M"
)
server_handler.setFormatter(server_formatter)
server_logger.addHandler(server_handler)

# Supabase setup
supabase_url = os.getenv("API_URL")
supabase_key = os.getenv("API_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

def update_supabase(processed_blogs, title):
    server_logger.info(f"Fetching Batch for Posts:")
    try:   
        for blog in processed_blogs:
            post_data = {
                'id' : abs(hash(str(uuid.uuid4()))),
                'Ticker' : blog['Ticker'],
                'Popularity' : blog['Popularity'],
                'Popularity_In_Text' : blog['In Text Popularity'],
                'Date' : blog['Date'],
                'Message' : blog['Message'],
                'Likes' : blog['Likes']
            }
            
            response = supabase.table(title).upsert(post_data).execute()
            server_logger.info(f"Supabase response for post: {response}")
    except Exception as e:
        server_logger.error(f"Error fetching or storing data (Raw Mentions): {e}")
        
def clear_table(name):
    try:
        response = supabase.from_(name).delete().neq('id', 0).execute()
        server_logger.info(f"All rows deleted from {name}, {response}")
    except Exception as e:
        server_logger.error(f"Error clearing table: {e}")
        
def top_ticker(name, descending = True):
    try:
        return supabase.table(name).select("Ticker").order("Ticker", desc=descending).limit(1).execute()
    except Exception as e:
        server_logger.error(f"Error fetching last ticker: {e}")