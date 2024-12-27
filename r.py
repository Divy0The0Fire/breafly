from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from fastapi.middleware.cors import CORSMiddleware
import logging

app = FastAPI()

# Add CORS middleware to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all HTTP headers
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the data model for the response
class NewsItem(BaseModel):
    date: str
    title: str
    url: str
    image: str
    source: str
    favicon: Optional[str]  # Allow None values
    body: str

def get_random_news(limit: int):
    try:
        conn = sqlite3.connect('news.db')
        cursor = conn.cursor()
        
        # Fetch up to `limit` random news items sorted by date in descending order
        cursor.execute('''
            SELECT date, title, url, image, source, favicon, body 
            FROM news 
            ORDER BY RANDOM() 
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        # Convert rows to list of dictionaries
        news_list = [
            {
                "date": row[0],
                "title": row[1],
                "url": row[2],
                "image": row[3],
                "source": row[4],
                "favicon": row[5] if row[5] is not None else '',  # Ensure `favicon` is not None
                "body": row[6]
            }
            for row in rows
        ]
        
        # Sort news items by date in descending order
        news_list.sort(key=lambda x: x['date'], reverse=True)
        
        return news_list
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logging.info(f"Response: {response.status_code}")
    return response

@app.get("/news", response_model=List[NewsItem])
async def get_news(limit: int = 200):
    if limit <= 0 or limit > 200:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 200")
    news_list = get_random_news(limit)
    return news_list

# If you need to run the FastAPI app, use the following command:
# uvicorn main:app --reload
