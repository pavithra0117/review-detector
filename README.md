# E-commerce Fake Review Detection System

This project is a Streamlit-based web application that detects fake reviews from e-commerce platforms like Amazon. It uses sentiment analysis, linguistic heuristics, and keyword density to classify reviews.

## Features
- **URL Analysis**: Automatically extracts reviews from Amazon product URLs.
- **Manual Input**: Allows users to paste reviews for analysis.
- **Rule-based Detection**: Uses custom logic to identify suspicious patterns:
  - High sentiment in very short reviews.
  - Excessive keyword density (e.g., "best", "perfect", "must buy").
  - Word repetition.
- **Interactive UI**: Progress spinners, metrics, and highlighted result tables.
- **Fallback Mechanism**: Uses demo data if scraping is blocked by the platform.

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   streamlit run app.py
   ```

## Project Structure
- `app.py`: The main application code containing UI, scraping, and detection logic.
- `requirements.txt`: List of Python dependencies.

## Detection Logic Details
The system uses the following criteria for flagging a review as **Fake**:
- **Sentiment vs Length**: If a review is extremely positive (sentiment > 0.8) and shorter than 10 words.
- **Repetition**: If the same word appears more than 5 times in a relatively short review.
- **Marketing Bias**: High frequency of promotional keywords in short reviews.
- **Vague Spam**: Extremely short, neutral reviews.

## Disclaimer
This tool is for educational purposes. Detection is based on heuristics and may not be 100% accurate as sophisticated fake reviews can mimic genuine ones.
