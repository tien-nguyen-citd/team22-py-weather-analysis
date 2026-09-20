from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
MODELS_DIR = PROJECT_DIR / ".models"

# Danh sách địa điểm dùng chung với backend, chỉ đọc file và không import code backend.
SEED_DIR = PROJECT_DIR.parent / "backend" / "data" / "seed"
LOCATIONS_PATH = SEED_DIR / "locations.csv"
LOCATION_ALIASES_PATH = SEED_DIR / "location-aliases.csv"

ACTIVITIES_PATH = DATA_DIR / "activities.csv"
ACTIVITY_EXAMPLES_PATH = DATA_DIR / "activity-examples.csv"
QUESTIONS_PATH = DATA_DIR / "questions.csv"
