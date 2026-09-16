import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()


def main() -> None:
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    database = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    if not all([database, user, password]):
        raise ValueError("Check your .env file.")

    url = (
        f"postgresql+psycopg2://"
        f"{user}:{password}@{host}:{port}/{database}"
    )

    engine = create_engine(url)

    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT COUNT(*) FROM public.transactions")
        )
        count = result.scalar_one()

    print(f"Database connection successful.")
    print(f"Transactions found: {count:,}")


if __name__ == "__main__":
    main()