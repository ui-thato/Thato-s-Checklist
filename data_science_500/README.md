# Book Market Analytics: Books to Scrape (Data Science 500)

## What's in this folder
- `books_to_scrape_analysis.ipynb`: the full project, covering scraping → cleaning → charts → linear regression.
- `report/Book_Market_Analytics_Report.docx`: the written report. Gaps that need numbers from **your** run are highlighted in yellow.
- `requirements.txt`: the Python libraries needed.

`books_raw.csv` and `books_clean.csv` are created when you run the notebook.

## How to run it
1. Install Python 3.9 or newer, then open a terminal in this folder and run:
   ```
   pip install -r requirements.txt
   jupyter notebook
   ```
2. Open `books_to_scrape_analysis.ipynb` and choose **Kernel → Restart & Run All**. You need an internet connection. Scraping all 1,000 books takes about 5–10 minutes. For a quick test, set `SCRAPE_BOOK_PAGES = False` in the Settings cell. That skips stock quantity and descriptions, so set it back to `True` for the final run.
3. When it finishes, save the notebook so the outputs and charts are stored in it.

## After running
1. **Notebook:** fill in each *"What this shows"* box and the Step 5 summary using your outputs.
2. **Report:** replace every yellow `[...]` gap with your numbers and findings, then remove the yellow highlighting. Adjust the Recommendations so they match what you found.
3. Add the official cover page and sign the declaration, then export the report to PDF for Moodle.
4. Submit the notebook and `books_clean.csv` as separate deliverables.

## Note on the results
Books to Scrape is a practice site, so its prices and ratings may not follow real market patterns. If the model's R² comes out close to 0, the code isn't wrong. It's a finding that should be explained, and the report already discusses this under limitations.
