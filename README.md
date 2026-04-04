# Voice Summary Report

텔레그램 음성 메시지 → AI 회의록 자동 생성 에이전트

## 개요

텔레그램으로 음성 파일을 보내면 AI가 자동으로 회의록을 생성하여 원하는 문서 형식으로 제공합니다.

## 아키텍처 (v1 - Claude Code 기반)

```
텔레그램 음성 → Claude Code (MCP 플러그인) → 회의록 요약 → 문서 생성 → 텔레그램 응답
                     │
                     ├── 음성 직접 이해 (멀티모달, STT 불필요)
                     ├── 회의록 형태 구조화 요약
                     └── PDF / DOCX / MD / TXT 문서 생성
```

### 왜 이 구조인가

- **Whisper(STT) 불필요** - Claude가 오디오를 직접 이해
- **별도 봇 서버 불필요** - MCP 텔레그램 플러그인이 연동 처리
- **추가 비용 없음** - Claude Max 구독 내에서 운영
- **코드 최소화** - 문서 생성 스크립트만 직접 구현

## 주요 기능

- 텔레그램 봇으로 음성/오디오 파일 수신
- Claude의 멀티모달 능력으로 음성 직접 분석 및 요약
- 회의록 형태로 구조화 (제목, 참석자, 안건, 결정사항, 할일 등)
- PDF / DOCX / Markdown / TXT 문서 생성

## 기술 스택

| 항목 | 기술 |
|------|------|
| AI 엔진 | Claude Code (Max 구독) |
| 텔레그램 | MCP 텔레그램 플러그인 |
| 문서 생성 | Python (fpdf2, python-docx) |
| 실행 환경 | Apple Silicon Mac |

## 빠른 시작

### 사전 준비

1. Claude Code + 텔레그램 MCP 플러그인 연동
2. Python 의존성 설치:
   ```bash
   pip install -r requirements.txt
   ```
3. 한글 폰트 (`NanumGothic.ttf`)를 `fonts/` 디렉토리에 배치

### 사용 방법

1. 텔레그램에서 봇에게 음성 메시지 전송
2. Claude Code가 자동으로 음성 분석 → 회의록 생성
3. 원하는 문서 형식 선택 (PDF/DOCX/MD/TXT)
4. 생성된 문서 수신

### 문서 생성 스크립트 (수동 실행)

```bash
python scripts/generate_doc.py --format pdf --input meeting.json --output data/output/
python scripts/generate_doc.py --format all --input meeting.json --output data/output/
```

## 프로젝트 구조

```
voice-summary-report/
├── scripts/
│   ├── generate_doc.py           # 문서 생성 CLI
│   └── renderers/                # PDF/DOCX/MD/TXT 렌더러
├── prompts/
│   └── meeting_minutes.md        # 회의록 프롬프트 템플릿
├── data/output/                  # 생성된 문서
├── fonts/                        # 한글 폰트
└── docs/
    └── DEVELOPMENT.md            # 개발 문서 (v1 + v2)
```

## 개발 문서

자세한 설계, v1/v2 비교, 구현 계획은 [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)를 참고하세요.

## 버전 계획

- **v1 (현재)**: Claude Code + MCP 기반 간소화 버전
- **v2 (추후)**: 독립 Python 봇 서버 + Whisper + 플러그형 LLM
- **Phase 2**: Notion / Google Docs 연동

## 라이선스

MIT License
