# CE49X Final Project — Conflict Situation Monitoring

Primary notebook: `CE49X_Final_Project_Clean.ipynb`

## Deliverables in this folder

- `CE49X_Final_Project_Clean.ipynb` (single final notebook)
- `dashboard.png` (final static dashboard figure, 300 DPI)
- `build_html_dashboard.py` (builds interactive `dashboard.html`)
- `Final_Project.pdf` and `final_project_extracted.txt` (assignment brief/reference)

## Environment setup

```powershell
cd "C:\Users\BORA\CE49X\Final Project"
python -m venv "C:\Users\BORA\CE49X\.venv"
"C:\Users\BORA\CE49X\.venv\Scripts\activate"
pip install -r requirements.txt
```

## PostgreSQL with Docker

Recreate container (if needed):

```powershell
docker run --name ce49x-postgres `
  -e POSTGRES_USER=ce49x `
  -e POSTGRES_HOST_AUTH_METHOD=trust `
  -e POSTGRES_DB=conflict_monitoring `
  -p 5432:5432 `
  -d postgres:16
```

Start/verify existing container:

```powershell
docker start ce49x-postgres
docker ps
```

Python connection string:

`postgresql://ce49x@localhost:5432/conflict_monitoring`

## Required PostgreSQL tables

| Table | Content |
|---|---|
| `firms_detections` | Cleaned FIRMS thermal detection records |
| `news_articles` | Collected conflict news metadata |
| `thermal_events` | Clustered thermal events with computed features |
| `event_matches` | Thermal event-news matching rows |

## Reproducibility

- Notebook run: open `CE49X_Final_Project_Clean.ipynb`, then **Kernel -> Restart & Run All**.
- HTML dashboard build:

```powershell
"C:\Users\BORA\CE49X\.venv\Scripts\python.exe" "C:\Users\BORA\CE49X\Final Project\build_html_dashboard.py"
```

Generated HTML outputs:

- `D:\CE49X_FinalProject\results\outputs\figures\dashboard.html`
- `D:\CE49X_FinalProject\figures\dashboard.html`
