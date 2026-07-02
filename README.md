# 💬YouTube Comment Scraper 

An automated ETL (Extract, Transform, Load) pipeline built to extract raw YouTube comments and perform sentiment analysis, simplifying the process of gathering large-scale social data for analysis in tools like Excel and Power BI. I built this project for learning purposes.

## ⚙️Technologies

 * Python (the core engine)
 * SQLite (storage for raw data)
 * Pandas (Data cleaning and transformation)
 * NLTK/VADER (AI Sentiment Analysis)
 * yt-dlp (Data extraction)
 * tkinter (GUI for QOL)

## 🤖Features

* **Automated Extraction**: Enter a URL and a comment limit to pull unstructured data directly from YouTube.
* **SQL Staging Layer**: Utilizes SQLite to temporarily store raw comment data. (handling duplicates via Primary Keys)
* **Data Cleaning**: Automatically removes junk characters, formats timestamps, and strips empty spaces using Pandas.
* **Sentiment Analysis**: Every comment is processed through the VADER NLP lexicon to assign a positive, negative, or neutral score.
* **CSV Export**: Outputs a clean, UTF-8 encoded CSV file ready for immediate use in Power BI or SQL.

 ## 🫡How it Works

  * **Extract**: The scraper uses yt-dlp to reliably fetch raw, unstructured JSON comment data instead of APIs with daily limits or system heavy tools like Selenium.
  * **Transform**: First, the raw comments are temporarily saved in a local SQLite database, using Primary Keys to automatically block any duplicates. Once the data is safe pandas takes over to clean up the messy text and fix the broken timestamps. Finally, every clean comment is passed through the VADER sentiment analyzer to figure out if it is Positive, Negative, or Neutral.
  * **Load**: The refined, structured dataset is exported as a clean, UTF-8 encoded CSV instantly ready for dashboarding in Power BI or Excel.

## 🧑‍🍳The Process
I started out just trying to pull comments without getting blocked, which is why I went with yt-dlp instead of dealing with strict API limits. Once the data actually started coming in, I realized it was completely unstructured and full of weird formatting.

To handle that, I set up a local SQLite database to act as a staging area. Instead of keeping everything in a massive Python list that could crash, saving it to a local .db file let me use Primary Keys to automatically drop duplicate comments as they came in.

Once the raw data was safely stored, I pulled it into Pandas. I spent most of my time here writing logic to strip out junk characters, fix the broken Unix timestamps, and get the text readable. After the text was clean, I ran it through VADER sentiment analyzer to figure out if people were being positive, negative, or neutral.

And in the end, I built a simple Tkinter GUI so even others who are not familiar with using the terminal or computers in general can easily use it. I also put in some basic threading so the app wouldn't freeze up while the scraper was running in the background.

## Overall Growth

This project was a huge step up from standard coding assignments. It forced me to actually think about data architecture, handle weird cases in text formatting, and build a pipeline that works. Each bug I fixed helped bridge the gap between knowing the theory of databases and actually building one that works.

## How can it be improved?

* **Batch Saving**: Update the database to save comments in small chunks as they come in, preventing data loss if the scraper crashes midway.
* **Smarter AI**: VADER works as intended but it has its limitations with other languages and complex sarcasm, switching it out with a local LLM to catch the tone better.
* **Auto-Visualization**: Have the script automatically generate a basic pie chart of the positive/negative/neutral split and save it alongside the CSV.

## 🚦Running this project

1. Clone the repository to your local machine
2. Install the required Python libraries (yt-dlp, pandas, vaderSentiment)
   ```bash
   pip install -r requirements.txt
   ```
3. Run the main Python script:
   ```bash
   python main.py
   ```
