import argparse
import getpass
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings  # noqa: E402
from app.db import AuthRepository, DuplicateUserError, SQLiteDatabase  # noqa: E402
from app.services.auth_service import AuthService  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Stock Manager administrator account.",
    )
    parser.add_argument("--email", required=True)
    parser.add_argument("--display-name", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    password = getpass.getpass("관리자 비밀번호(12자 이상): ")
    confirmation = getpass.getpass("관리자 비밀번호 확인: ")
    if password != confirmation:
        print("비밀번호가 일치하지 않습니다.", file=sys.stderr)
        return 2

    service = AuthService(AuthRepository(SQLiteDatabase(settings.database_path)))
    try:
        user = service.create_admin(
            email=args.email.strip(),
            display_name=args.display_name.strip(),
            password=password,
        )
    except DuplicateUserError:
        print("이미 등록된 이메일입니다.", file=sys.stderr)
        return 3
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"관리자 계정을 생성했습니다: {user.email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
