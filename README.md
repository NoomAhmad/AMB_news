# AMB NEWS – Somalia news (GitHub Action + news.json)

A GitHub Action runs once a day, reads the RSS feeds, keeps Somalia-related
articles only and saves them to `news.json`. `index.html` just reads that file.

## Setup
1. Create a GitHub repository and upload everything in this folder
   (keep the `.github` and `scripts` folders).
2. Repo → Settings → Actions → General → Workflow permissions →
   choose "Read and write permissions" → Save.
3. Repo → Actions tab → "Update Somalia news" → Run workflow
   (this creates the first news.json; after that it runs daily at 04:00 UTC).
4. Show the page:
   - Easiest: Settings → Pages → Deploy from branch → main → / (root).
   - Or host index.html on your own site and set `newsUrl` in index.html to
     https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/news.json

## Customize
- Feeds, keywords, number of items: top of `scripts/fetch_news.py`
- Run time: the `cron` line in `.github/workflows/update-news.yml`
