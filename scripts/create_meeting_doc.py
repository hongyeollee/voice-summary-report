#!/usr/bin/env python3
"""회의록 JSON 데이터를 Google Docs 문서로 생성하는 CLI 도구.

사용법:
    python scripts/create_meeting_doc.py --input meeting.json
    python scripts/create_meeting_doc.py --input meeting.json --share anyone_reader
    python scripts/create_meeting_doc.py --input meeting.json --share-email user@example.com
    cat meeting.json | python scripts/create_meeting_doc.py
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from google_docs_client import GoogleDocsClient

load_dotenv()


def parse_args():
    parser = argparse.ArgumentParser(description="회의록 Google Docs 생성")
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=None,
        help="회의록 JSON 파일 경로. 미지정 시 stdin에서 읽음",
    )
    parser.add_argument(
        "--share",
        type=str,
        default=None,
        help="공유 모드: private, anyone_reader, anyone_writer, anyone_commenter",
    )
    parser.add_argument(
        "--share-email",
        type=str,
        default=None,
        help="특정 이메일에 편집 권한 부여",
    )
    parser.add_argument(
        "--credentials",
        type=str,
        default=None,
        help="Google 서비스 계정 JSON 키 경로",
    )
    return parser.parse_args()


def load_minutes(input_path: Optional[str]) -> dict:
    """JSON 파일 또는 stdin에서 회의록 데이터를 로드한다."""
    if input_path and input_path != "-":
        with open(input_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return json.load(sys.stdin)


def main():
    args = parse_args()

    client_secret_path = (
        args.credentials
        or os.getenv("GOOGLE_CREDENTIALS_PATH", "./credentials/oauth_client.json")
    )
    token_path = os.getenv("GOOGLE_TOKEN_PATH", "./credentials/token.json")

    if not Path(client_secret_path).exists():
        print(
            f"오류: OAuth 클라이언트 파일을 찾을 수 없습니다: {client_secret_path}",
            file=sys.stderr,
        )
        print(
            "credentials/oauth_client.json을 배치하거나 --credentials 옵션을 사용하세요.",
            file=sys.stderr,
        )
        sys.exit(1)

    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    minutes = load_minutes(args.input)
    client = GoogleDocsClient(client_secret_path, token_path, folder_id=folder_id)
    url = client.create_document(minutes)

    # 공유 권한 설정
    document_id = url.split("/d/")[1].split("/")[0]

    share_mode = args.share or os.getenv("GOOGLE_DOCS_SHARE_MODE", "private")
    if share_mode != "private" or args.share_email:
        client.set_permissions(document_id, share_mode, args.share_email)

    print(url)


if __name__ == "__main__":
    main()
