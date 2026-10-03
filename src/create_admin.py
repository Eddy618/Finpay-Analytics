import getpass

from pwdlib import PasswordHash
from sqlalchemy import text

from api.database import engine


password_hash = PasswordHash.recommended()


def main():
    print("FinPay Analytics - Create Admin User")
    print("------------------------------------")

    username = input("Admin username: ").strip()

    if not username:
        raise ValueError("Username cannot be empty.")

    password = getpass.getpass("Admin password: ")
    confirm_password = getpass.getpass("Confirm password: ")

    if not password:
        raise ValueError("Password cannot be empty.")

    if password != confirm_password:
        raise ValueError("Passwords do not match.")

    hashed_password = password_hash.hash(password)

    query = text(
        """
        INSERT INTO public.app_users (
            username,
            password_hash,
            role,
            is_active
        )
        VALUES (
            :username,
            :password_hash,
            'admin',
            TRUE
        )
        ON CONFLICT (username)
        DO UPDATE SET
            password_hash = EXCLUDED.password_hash,
            role = 'admin',
            is_active = TRUE,
            updated_at = CURRENT_TIMESTAMP
        """
    )

    with engine.begin() as conn:
        conn.execute(
            query,
            {
                "username": username,
                "password_hash": hashed_password,
            },
        )

    print("")
    print(f"Admin user '{username}' created successfully.")


if __name__ == "__main__":
    main()