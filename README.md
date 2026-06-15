# Peter's Review Manager

This project consists of two main components: a Python-based Scraper and a React-based Viewer.

## Components

### 1. Scraper
The Scraper is a Python application that fetches media reviews from Peter Rogers' LiveJournal and generates a `peter_reviews_data.csv` file.

**Location:** `/scraper`

**Usage:**
1. Navigate to the `scraper` directory.
2. Activate the virtual environment: `source venv/bin/activate`.
3. Run the scraper: `python3 scraper.py`.
4. The output will be saved to `peter_reviews_data.csv`.

### 2. Viewer
The Viewer is a React SPA (Single Page Application) that provides a filtered, paginated view of the reviews data.

**Location:** `/viewer`

**Usage:**
1. Navigate to the `viewer` directory.
2. Install dependencies (if not already done): `npm install`.
3. Start the development server: `npm run dev`.
4. Open your browser to the provided URL (usually `http://localhost:5173`).
5. To build for production: `npm run build`.

## Deployment (GitHub Pages)

The Viewer is configured for easy deployment to GitHub Pages.

### One-time Setup
1. Ensure your repository name on GitHub is `peters-reviews`. If it's different, update the `base` field in `viewer/vite.config.ts` and the `homepage` field in `viewer/package.json`.
2. Push your code to the `main` branch.

### Deploying
1. Navigate to the `viewer` directory.
2. Run:
   ```bash
   npm run deploy
   ```
This will build the app and push the contents of the `dist` folder to a `gh-pages` branch on your repository.

3. On GitHub, go to **Settings > Pages** and ensure the **Branch** is set to `gh-pages` (root).

## Data Integration
The Viewer is configured to fetch data from `/peter_reviews_data.csv`. During development, a symlink exists in `viewer/public/` pointing to the scraper's output. When deploying, ensure the CSV file is placed in the root of the web server or the `public` folder before building.

## Requirements
- Python 3.x
- Node.js & npm
