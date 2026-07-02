import yt_dlp
import sqlite3
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
from pathlib import Path

# Ensure the AI dictionary is downloaded
nltk.download('vader_lexicon', quiet=True)

# --- 1. THE PIPELINE LOGIC ---
def setup_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS raw_comments (
            comment_id TEXT PRIMARY KEY, parent_id TEXT, text TEXT, timestamp INTEGER,
            like_count INTEGER, author_id TEXT, author_name TEXT, is_favorited BOOLEAN, is_uploader BOOLEAN
        )
    ''')
    conn.commit()
    return conn

def run_full_pipeline(video_url, amount, final_csv_path, log_callback):
    """The main engine that runs in the background"""
    temp_db_path = Path(final_csv_path).parent / "temp_raw_data.db"
    
    # --- SCRAPING PHASE ---
    log_callback("\n[STEP 1/3] Initializing YouTube Scraper...")
    conn = setup_database(temp_db_path)
    cursor = conn.cursor()

    class ProgressLogger:
        def __init__(self): self.page = 0
        def debug(self, msg):
            if "comment API" in msg:
                self.page += 1
                log_callback(f"⏳ Scraping... (Fetched {self.page} pages)")
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): log_callback(f"[ERROR]: {msg}")

    ydl_opts = {
        'quiet': True, 'no_warnings': True, 'extract_flat': False, 'getcomments': True,        
        'extractor_args': {'youtube': {'max_comments': [str(amount)]}},
        'logger': ProgressLogger(),
        'sleep_requests': 1.5, 'retries': 10, 'fragment_retries': 10, 'retry_sleep': 'exp'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            raw_comments = info.get('comments', [])
            
            if not raw_comments:
                log_callback("❌ No comments found.")
                return

            sql_data = [(
                c.get('id'), c.get('parent', 'root'), c.get('text'), c.get('timestamp'),
                c.get('like_count', 0), c.get('author_id'), c.get('author'),
                bool(c.get('is_favorited', False)), bool(c.get('author_is_uploader', False))
            ) for c in raw_comments]
            
            cursor.executemany('INSERT OR IGNORE INTO raw_comments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', sql_data)
            conn.commit()
            log_callback(f"✅ Scraped and saved {cursor.rowcount} comments.")
            
    except Exception as e:
        log_callback(f"❌ Scraper failed: {e}")
        return
    finally:
        conn.close()

    # --- PANDAS & VADER PHASE ---
    log_callback("\n[STEP 2/3] Cleaning Data with Pandas...")
    try:
        conn = sqlite3.connect(temp_db_path)
        df = pd.read_sql_query("SELECT * FROM raw_comments", conn)
        conn.close()

        df['date_published'] = pd.to_datetime(df['timestamp'], unit='s')
        df = df[['comment_id', 'date_published', 'author_name', 'author_id', 'text', 'like_count']]
        df['text'] = df['text'].astype(str).str.replace(r'\r+|\n+', ' ', regex=True).str.strip()

        log_callback("\n[STEP 3/3] Running AI Sentiment Analysis (VADER)...")
        analyzer = SentimentIntensityAnalyzer()
        
        def get_sentiment(score):
            if score >= 0.05: return "Positive 😊"
            elif score <= -0.05: return "Negative 😡"
            else: return "Neutral 😐"

        df['sentiment_score'] = df['text'].apply(lambda x: analyzer.polarity_scores(str(x))['compound'])
        df['sentiment_label'] = df['sentiment_score'].apply(get_sentiment)
        
        df.to_csv(final_csv_path, index=False, encoding='utf-8-sig')
        log_callback(f"\n🎉 PIPELINE COMPLETE! Data saved to:\n{final_csv_path}")

    except Exception as e:
        log_callback(f"❌ Analysis failed: {e}")
    finally:
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

# --- 2. THE GRAPHICAL USER INTERFACE (GUI) ---
class YouTubeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Comment Scraper :)")
        self.root.geometry("600x500")
        self.root.configure(padx=20, pady=20)
        
        # URL Input
        ttk.Label(root, text="YouTube Video URL:", font=('Arial', 10, 'bold')).pack(anchor="w")
        self.url_entry = ttk.Entry(root, width=70)
        self.url_entry.pack(pady=5, fill="x")
        
        # Amount Input
        ttk.Label(root, text="Max Comments to Scrape:", font=('Arial', 10, 'bold')).pack(anchor="w", pady=(10,0))
        self.amount_entry = ttk.Entry(root, width=20)
        self.amount_entry.insert(0, "500") # Default value
        self.amount_entry.pack(anchor="w", pady=5)
        
        # Save Location Button
        self.save_path = tk.StringVar()
        self.save_path.set("No location selected...")
        
        btn_frame = ttk.Frame(root)
        btn_frame.pack(fill="x", pady=15)
        
        ttk.Button(btn_frame, text="1. Choose Save Location", command=self.choose_location).pack(side="left")
        ttk.Label(btn_frame, textvariable=self.save_path, foreground="gray").pack(side="left", padx=10)
        
        # Start Button
        self.start_btn = ttk.Button(root, text="2. RUN PIPELINE ▶", command=self.start_pipeline)
        self.start_btn.pack(fill="x", pady=10)
        
        # Log Output Box
        ttk.Label(root, text="System Logs:").pack(anchor="w")
        self.log_box = scrolledtext.ScrolledText(root, height=12, state='disabled', bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9))
        self.log_box.pack(fill="both", expand=True)

    def log(self, message):
        """Prints messages to the GUI text box instead of the terminal"""
        self.log_box.config(state='normal')
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END) # Auto-scroll to bottom
        self.log_box.config(state='disabled')

    def choose_location(self):
        path = filedialog.asksaveasfilename(
            title="Save Final CSV As...", defaultextension=".csv",
            filetypes=[("CSV File", "*.csv")], initialfile="Analyzed_YouTube_Data.csv"
        )
        if path:
            self.save_path.set(path)

    def start_pipeline(self):
        url = self.url_entry.get().strip()
        amount = self.amount_entry.get().strip()
        save_file = self.save_path.get()
        
        if not url or "youtube.com" not in url:
            self.log("❌ Error: Please enter a valid YouTube URL.")
            return
        if not amount.isdigit():
            self.log("❌ Error: Amount must be a number.")
            return
        if save_file == "No location selected...":
            self.log("❌ Error: Please choose a save location first.")
            return

        self.start_btn.config(state="disabled") # Prevent double clicking
        self.log("="*40)
        self.log(f"🚀 Starting Engine for: {url}")
        
        # Run the heavy code in a background thread so the GUI doesn't freeze!
        threading.Thread(target=self.run_background_task, args=(url, int(amount), save_file), daemon=True).start()

    def run_background_task(self, url, amount, save_file):
        run_full_pipeline(url, amount, save_file, self.log)
        self.start_btn.config(state="normal") # Re-enable button when done

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeApp(root)
    root.mainloop()