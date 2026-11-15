import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import psycopg2

try:
    df = pd.read_csv("fieldgym_dataset_730days.csv")
    print(f"✅Úspěšně načteno {len(df)} řádků z CSV souboru!")
except FileNotFoundError:
    print("❌CHYBA: Soubor 'fieldgym_dataset_730days.csv' nebyl nalezen!")
    exit()

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌CHYBA: Chybí DATABASE_URL v .env souboru!")
    exit()

engine_url = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1).replace("postgres://", "postgresql+psycopg2://", 1)
engine = create_engine(engine_url)

try:
    with engine.connect() as conn:
        print("✅Úspěšně připojeno k Neon.tech databázi přes SQLAlchemy!")
except Exception as e:
    print(f"❌Chyba při připojení k DB: {e}")
    exit()

df.to_sql('fct_fieldgym_data_RAW', con=engine, if_exists='replace', index=True)
print("✅Data byla úspěšně nahrána do tabulky 'fieldgym_data' v databázi!")