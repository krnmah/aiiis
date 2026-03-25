import sys

from app.db.database import check_db_connection


def main() -> int:
    try:
        check_db_connection()
        print("Database connection: OK")
        return 0
    except Exception as exc:
        print(f"Database connection: FAILED ({exc})")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
