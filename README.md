# 🎥 YouTube Data ETL Pipeline & Sentiment Analyzer

A high-performance automated pipeline designed to extract YouTube comments, process them through a SQL-based staging layer, and perform AI-driven sentiment analysis. This tool is built to bridge the gap between raw social media data and actionable insights for platforms like Power BI and Excel.

## 🛠️ Tech Stack
- **Engine:** Python 3.11+
- **Extraction:** `yt-dlp` (High-reliability scraping)
- **Staging:** `SQLite` (Relational storage for duplicate management)
- **Processing:** `Pandas` (Vectorized data transformation)
- **NLP Engine:** `VADER` (Valence Aware Dictionary and sEntiment Reasoner)
- **Interface:** `Tkinter` (Multi-threaded GUI)

## 🚀 Key Features
- **Smart Extraction:** Efficiently fetches comments using video URLs without requiring Google API keys.
- **SQL Integrity:** Implements a staging database with primary key constraints to automatically handle data deduplication.
- **Data Refining:** Cleans raw JSON responses into structured data, handling timestamps and non-standard characters.
- **Sentiment Scoring:** Generates Positive, Negative, and Neutral polarity scores for every comment.
- **Analytics Ready:** Instant export to UTF-8 encoded CSV files.

## ⚙️ Architecture (ETL Process)
1. **Extract:** `yt-dlp` extracts raw JSON payloads from the target URL.
2. **Transform:** 
   - Raw data is cached in a local `.db` file via SQL.
   - `Pandas` handles cleaning and formatting.
   - `vaderSentiment` performs text analysis.
3. **Load:** The final structured dataset is saved as a CSV for external analysis.

## 📦 Installation & Setup
1. **Clone the Project:**
   ```bash
   git clone https://github.com/skm-edu4/yt-comment-analyzer.git
   cd yt-comment-analyzer
   pip install -r requirements.txt
   python main.py
