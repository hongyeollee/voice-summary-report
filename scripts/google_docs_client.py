"""Google Docs/Drive API 클라이언트 - 회의록 문서 생성 및 공유"""

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]

SHARE_MODES = {
    "private": None,
    "anyone_reader": {"type": "anyone", "role": "reader"},
    "anyone_writer": {"type": "anyone", "role": "writer"},
    "anyone_commenter": {"type": "anyone", "role": "commenter"},
}


class GoogleDocsClient:
    def __init__(self, credentials_path: str):
        creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=SCOPES
        )
        self.docs_service = build("docs", "v1", credentials=creds)
        self.drive_service = build("drive", "v3", credentials=creds)

    def create_document(self, minutes: dict) -> str:
        """회의록 데이터로 Google Docs 문서를 생성하고 URL을 반환한다."""
        title = minutes.get("overview", {}).get("purpose", "회의록")
        date = minutes.get("overview", {}).get("date", "")
        doc_title = f"[회의록] {title}" if title else "회의록"
        if date:
            doc_title = f"{doc_title} ({date})"

        doc = self.docs_service.documents().create(body={"title": doc_title}).execute()
        document_id = doc["documentId"]

        requests = self._build_content_requests(minutes)
        if requests:
            self.docs_service.documents().batchUpdate(
                documentId=document_id, body={"requests": requests}
            ).execute()

        return f"https://docs.google.com/document/d/{document_id}/edit"

    def set_permissions(self, document_id: str, share_mode: str, email: str = None):
        """문서의 공유 권한을 설정한다."""
        if email:
            self.drive_service.permissions().create(
                fileId=document_id,
                body={"type": "user", "role": "writer", "emailAddress": email},
                sendNotificationEmail=False,
            ).execute()
            return

        perm = SHARE_MODES.get(share_mode)
        if perm:
            self.drive_service.permissions().create(
                fileId=document_id, body=perm
            ).execute()

    def _build_content_requests(self, minutes: dict) -> list:
        """회의록 데이터를 Google Docs API 요청 목록으로 변환한다."""
        requests = []
        idx = 1  # 문서 내 현재 커서 위치 (1부터 시작)

        # 배경
        background = minutes.get("background", "")
        if background:
            idx = self._add_heading(requests, idx, "배경", "HEADING_2")
            idx = self._add_paragraph(requests, idx, background)

        # 1. 회의 개요
        overview = minutes.get("overview", {})
        idx = self._add_heading(requests, idx, "1. 회의 개요", "HEADING_2")

        date = overview.get("date", "명시되지 않음")
        idx = self._add_bullet(requests, idx, f"일시: {date}")

        purpose = overview.get("purpose", "명시되지 않음")
        idx = self._add_bullet(requests, idx, f"목적: {purpose}")

        attendees = overview.get("attendees", [])
        attendees_str = ", ".join(attendees) if attendees else "명시되지 않음"
        idx = self._add_bullet(requests, idx, f"참석자: {attendees_str}")

        # 2. 주요 논의 사항
        key_discussions = minutes.get("key_discussions", [])
        idx = self._add_heading(requests, idx, "2. 주요 논의 사항", "HEADING_2")
        for item in key_discussions:
            idx = self._add_bullet(requests, idx, item)

        # 3. 결정 사항
        decisions = minutes.get("decisions", [])
        idx = self._add_heading(requests, idx, "3. 결정 사항", "HEADING_2")
        for item in decisions:
            idx = self._add_bullet(requests, idx, item)

        # 4. Action Items
        action_items = minutes.get("action_items", [])
        idx = self._add_heading(requests, idx, "4. Action Items (향후 계획)", "HEADING_2")
        for item in action_items:
            if isinstance(item, dict):
                assignee = item.get("assignee", "미정")
                task = item.get("task", "")
                deadline = item.get("deadline", "미정")
                text = f"[{assignee}] {task} (기한: {deadline})"
            else:
                text = str(item)
            idx = self._add_bullet(requests, idx, text)

        return requests

    def _add_heading(self, requests: list, idx: int, text: str, style: str) -> int:
        """제목을 추가하고 새 커서 위치를 반환한다."""
        content = text + "\n"
        requests.append({
            "insertText": {"location": {"index": idx}, "text": content}
        })
        requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": idx, "endIndex": idx + len(content)},
                "paragraphStyle": {"namedStyleType": style},
                "fields": "namedStyleType",
            }
        })
        return idx + len(content)

    def _add_paragraph(self, requests: list, idx: int, text: str) -> int:
        """일반 텍스트 단락을 추가하고 새 커서 위치를 반환한다."""
        content = text + "\n"
        requests.append({
            "insertText": {"location": {"index": idx}, "text": content}
        })
        return idx + len(content)

    def _add_bullet(self, requests: list, idx: int, text: str) -> int:
        """불릿 항목을 추가하고 새 커서 위치를 반환한다."""
        content = text + "\n"
        requests.append({
            "insertText": {"location": {"index": idx}, "text": content}
        })
        requests.append({
            "createParagraphBullets": {
                "range": {"startIndex": idx, "endIndex": idx + len(content)},
                "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
            }
        })
        return idx + len(content)
