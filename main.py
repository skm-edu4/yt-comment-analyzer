import sqlite3
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import yt_dlp
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class ScraperEngine:
    """Handles the core ETL logic: Extraction, Transformation, and SQL Staging."""
    def __init__(self, db_name="staging_comments.db"):
        self.db_name = db_name
        self.analyzer = SentimentIntensityAnalyzer()
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS comments 
                           (id TEXT PRIMARY KEY, author TEXT, text TEXT, 
                            timestamp TEXT, sentiment_score REAL, sentiment_label TEXT)''')

    def fetch_raw_data(self, url, limit):
        ydl_opts = {
            'getcomments': True,
            'skip_download': True,
            'extract_flat': True,
            'max_comments': limit,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('comments', [])

    def process_and_analyze(self, raw_comments):
        processed_data = []
        for c in raw_comments:
            text = c.get('text', '')
            # VADER Analysis
            scores = self.analyzer.polarity_scores(text)
            compound = scores['compound']
            
            label = 'Neutral'
            if compound >= 0.05: label = 'Positive'
            elif compound <= -0.05: label = 'Negative'

            processed_data.append({
                'id': c.get('id'),
                'author': c.get('author'),
                'text': text,
                'timestamp': c.get('timestamp'),
                'sentiment_score': compound,
                'sentiment_label': label
            })
        return pd.DataFrame(processed_data)

    def save_to_staging(self, df):
        with sqlite3.connect(self.db_name) as conn:
            # Use SQL logic to ignore duplicates based on Primary Key (id)
            for _, row in df.iterrows():
                try:
                    row.to_frame().T.to_sql('comments', conn, if_exists='append', index=False)
                except sqlite3.IntegrityError:
                    continue # Skip duplicates

class YouTubeAppGUI:
    """Handles the Tkinter interface and threading."""
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Comment ETL Tool")
        self.engine = ScraperEngine()
        self._setup_ui()

    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(main_frame, text="Video URL:").grid(row=0, column=0, sticky=tk.W)
        self.url_entry = ttk.Entry(main_frame, width=50)
        self.url_entry.grid(row=0, column=1, pady=5)

        ttk.Label(main_frame, text="Max Comments:").grid(row=1, column=0, sticky=tk.W)
        self.limit_entry = ttk.Entry(main_frame, width=10)
        self.limit_entry.insert(0, "100")
        self.limit_entry.grid(row=1, column=1, sticky=tk.W, pady=5)

        self.start_btn = ttk.Button(main_frame, text="Start ETL Pipeline", command=self.run_task)
        self.start_btn.grid(row=2, column=0, columnspan=2, pady=20)

        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))

    def run_task(self):
        url = self.url_entry.get()
        limit = int(self.limit_entry.get())
        
        self.start_btn.state(['disabled'])
        self.progress.start()
        
        # Run in thread to prevent GUI freezing
        threading.Thread(target=self.execute_pipeline, args=(url, limit), daemon=True).start()

    def execute_pipeline(self, url, limit):
        try:
            raw = self.engine.fetch_raw_data(url, limit)
            df = self.engine.process_and_analyze(raw)
            self.engine.save_to_staging(df)
            
            # Export to CSV
            output_file = "youtube_sentiment_export.csv"
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
            messagebox.showinfo("Success", f"Task Complete!\nExported {len(df)} comments to {output_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process: {str(e)}")
        finally:
            self.progress.stop()
            self.start_btn.state(['!disabled'])

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeAppGUI(root)
    root.mainloop()
