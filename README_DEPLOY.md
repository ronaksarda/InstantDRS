# Deployment Guide: InstantDRS

Follow these steps to upload your project to GitHub, deploy it to Google Cloud, and submit it for the Solution Challenge.

## 1. GitHub Upload
1. Create a new repository on [GitHub](https://github.com/new).
2. Open your terminal in the project folder and run:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: InstantDRS Production"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin main
   ```

## 2. Google Cloud Deployment (Cloud Run)
We use Cloud Run because it handles the C++ Priority Engine perfectly via Docker.

### Prerequisites
- Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install).
- Run `gcloud auth login` and `gcloud config set project YOUR_PROJECT_ID`.

### Deployment Steps
1. Enable the necessary APIs:
   ```bash
   gcloud services enable run.googleapis.com containerregistry.googleapis.com
   ```
2. Deploy the application:
   ```bash
   gcloud run deploy instant-drs --source . --region us-central1 --allow-unauthenticated
   ```
3. Once finished, GCP will provide a URL (e.g., `https://instant-drs-xyz.a.run.app`).

## 3. Hack2Skills Submission
1. **Pitch Deck**: Fill out the provided PPTX template in your project folder.
2. **Video Demo**: Record a 2-minute walkthrough of the SOS report and Authority dashboard.
3. **Submission**: Go to the Hack2Skills portal and provide:
   - Your GitHub Repository URL.
   - Your Live Google Cloud URL.
   - The Pitch Deck (exported as PDF).
   - The Demo Video Link (YouTube/Drive).

## 4. Local Debugging
To run locally for testing:
1. Ensure your `.env` has the `GEMINI_API_KEY`.
2. Run `.\compile.bat` (Windows) or `./compile.sh` (Mac/Linux).
3. Run `python app.py`.
4. Visit `http://localhost:5000`.

> [!TIP]
> Always verify the **Authority Dashboard** (`/authority`) after deployment to ensure Firebase connectivity is active.
