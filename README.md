# InstantDRS (Instant Disaster Response System) 🚨

InstantDRS is a web application built for the **2026 Google Solution Challenge**. It allows a person in an emergency to submit a quick SOS report with optional media (photos/video/audio), and it gives a dispatcher a dashboard to view and manage these incidents.

![Dashboard Screenshot](docs/screenshot.png)

## 🛠️ Technical Stack
- **Frontend**: HTML/JS/CSS (TailwindCSS) with a simple web interface.
- **Backend**: Python (Flask).
- **AI Integration**: Google Gemini 1.5 Flash is used to summarize incoming emergency reports.
- **Sorting**: A C++ merge sort (`incident_sorter.cpp`) that orders active incidents based on severity.
- **Database**: Firebase Firestore is used to store data for the Command Center.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- G++ Compiler (to compile the C++ sorting file)
- Google Gemini API Key

### Installation & Setup
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Compile the incident sorter:
   ```bash
   # Windows
   .\compile.bat
   
   # Linux/Mac
   ./compile.sh
   ```
4. Configure your `.env` file (copy `.env.example` to `.env` if available). 
   - Set your `GEMINI_API_KEY`.
   - Set your `ADMIN_PASSWORD` (this is used to log into the dispatch dashboard).
5. Run the server:
   ```bash
   python app.py
   ```

## 🔐 Authority Dashboard
You can access the dispatch dashboard at `/authority`.
- Log in with the username `admin` and the password you set in your `.env` file under `ADMIN_PASSWORD`.
- From the dashboard, you can create additional dispatcher accounts under the Settings tab.
