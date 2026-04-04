# Voice Summary Report

텔레그램 음성 메시지 → AI 회의록 자동 생성 → Google Docs 문서 에이전트

## 개요

텔레그램으로 음성 파일을 보내면 AI가 자동으로 회의록을 생성하여 Google Docs 문서로 제공하고, 링크를 텔레그램으로 전달합니다.

## 아키텍처 (v1 - Claude Code 기반)

```
텔레그램 음성 → Claude Code (MCP 플러그인) → 회의록 요약 → Google Docs 생성 → 링크 전송
                     │                                          │
                     ├── 음성 직접 이해 (멀티모달)                ├── 회의록 포맷 자동 적용
                     └── 회의록 형태 구조화 요약                  └── 공유 권한 자동 설정
```

### 왜 이 구조인가

- **Whisper(STT) 불필요** - Claude가 오디오를 직접 이해
- **별도 봇 서버 불필요** - MCP 텔레그램 플러그인이 연동 처리
- **추가 비용 없음** - Claude Max 구독 내에서 운영
- **Google Docs 직접 생성** - 웹에서 바로 확인/편집/공유 가능

## 주요 기능

- 텔레그램 봇으로 음성/오디오 파일 수신
- Claude의 멀티모달 능력으로 음성 직접 분석 및 요약
- 회의록 형태로 구조화 (제목, 참석자, 안건, 결정사항, 할일 등)
- Google Docs로 회의록 문서 자동 생성
- 공유 링크 + 접근 권한 자동 설정
- 텔레그램으로 Google Docs 링크 전송

## 기술 스택

| 항목 | 기술 |
|------|------|
| AI 엔진 | Claude Code (Max 구독) |
| 텔레그램 | MCP 텔레그램 플러그인 |
| 문서 생성 | Google Docs API |
| 문서 공유 | Google Drive API |
| 실행 환경 | Apple Silicon Mac |

## 빠른 시작

### 사전 준비

1. Claude Code + 텔레그램 MCP 플러그인 연동
2. Google Cloud 설정:
   - Google Cloud Console에서 프로젝트 생성
   - Google Docs API + Google Drive API 활성화
   - 서비스 계정 생성 → JSON 키 다운로드
   - `credentials/service_account.json`에 배치
3. 환경변수 설정:
   ```bash
   cp .env.example .env
   # .env에서 GOOGLE_DOCS_SHARE_MODE 설정
   ```
4. 의존성 설치:
   ```bash
   pip install -r requirements.txt
   ```

### 사용 방법

1. 텔레그램에서 봇에게 음성 메시지 전송
2. Claude Code가 자동으로 음성 분석 → 회의록 생성
3. Google Docs 문서가 생성되고 텔레그램으로 링크 수신
4. 링크 클릭 → 웹에서 바로 확인/편집/공유

### 문서 생성 스크립트 (수동 실행)

```bash
python scripts/create_meeting_doc.py --input meeting.json
python scripts/create_meeting_doc.py --input meeting.json --share anyone_reader
```

## 프로젝트 구조

```
voice-summary-report/
├── scripts/
│   ├── create_meeting_doc.py     # Google Docs 회의록 생성 CLI
│   └── google_docs_client.py     # Google Docs/Drive API 클라이언트
├── prompts/
│   └── meeting_minutes.md        # 회의록 프롬프트 템플릿
├── credentials/                  # Google API 인증 (gitignored)
└── docs/
    └── DEVELOPMENT.md            # 개발 문서 (v1 + v2)
```

## 개발 문서

자세한 설계, v1/v2 비교, 구현 계획은 [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)를 참고하세요.

## 버전 계획

- **v1 (현재)**: Claude Code + MCP + Google Docs 기반 간소화 버전
- **v2 (추후)**: 독립 Python 봇 서버 + Whisper + 플러그형 LLM
- **Phase 2**: Notion 연동, 다국어 지원

## 라이선스

MIT License
