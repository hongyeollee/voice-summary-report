# Telegram Voice Meeting Minutes Agent - 개발 문서

## 1. 프로젝트 개요

텔레그램에서 음성 파일을 수신하면 AI가 자동으로 회의록을 생성하여 문서로 제공하는 에이전트.

두 가지 버전으로 개발하며, **v1(간소화)**을 먼저 구현한다.

| 버전 | 설명 | 핵심 차이 |
|------|------|----------|
| **v1 (간소화)** | Claude Code + 텔레그램 MCP 플러그인 | Claude가 STT+요약 모두 처리. 최소 코드 |
| **v2 (풀버전)** | 독립 Python 봇 서버 | Whisper STT + 플러그형 LLM. 완전 자체 운영 |

---

## 설계 배경 및 의사결정 맥락

> 이 섹션은 새 세션의 Claude가 프로젝트 배경을 이해하고 일관된 결과물을 만들 수 있도록 기록한다.

### 운영 환경
- **Claude Max 구독** 사용 중 → Claude Code 세션을 통한 처리에 추가 API 비용 없음
- **텔레그램 MCP 플러그인**이 Claude Code에 이미 연동된 상태. 별도 봇 서버 구축 불필요
- **Apple Silicon Mac** (로컬 서버)에서 Claude Code 세션을 상시 실행
- 학습 및 포트폴리오 목적의 프로젝트

### v1을 우선 개발하는 이유
- Claude Code 자체가 **멀티모달(오디오 직접 이해)** 능력을 가지므로 별도 STT(Whisper)가 불필요
- Claude Code가 LLM 역할을 하므로 별도 LLM 프로바이더 연동이 불필요
- MCP 텔레그램 플러그인이 메시지 수신/발신을 처리하므로 python-telegram-bot 서버가 불필요
- 결과적으로 **문서 생성 스크립트 + 프롬프트 템플릿**만 직접 구현하면 됨

### v2는 언제 필요한가
- Claude Code 세션 없이 **독립적으로 24/7 운영**해야 할 때
- **여러 사용자**가 동시에 사용해야 할 때
- LLM을 **Ollama 등 무료 모델로 교체**하여 구독 없이 운영하고 싶을 때

### 개발 방침
- 프롬프트 템플릿과 문서 렌더러 디자인(레이아웃, 폰트 크기 등)은 **기본형으로 먼저 구현**하고, 결과물 확인 후 피드백으로 수정
- 과도한 사전 설계보다 **빠른 구현 → 피드백 반영** 사이클을 우선

---

# v1: Claude Code 기반 간소화 버전 (우선 개발)

## 2. 아키텍처 개요

```
사용자 → 텔레그램 음성 전송
              │
              ▼
     [텔레그램 MCP 플러그인]
              │
              ▼
     [Claude Code 세션 (상시 실행)]
       ├── 음성 파일 수신 (멀티모달 오디오 이해)
       ├── 회의록 형태로 요약 생성
       ├── Google Docs API로 회의록 문서 생성
       └── 텔레그램으로 Google Docs 링크 전송
```

**핵심**: Claude Code 자체가 에이전트 역할. 별도 STT(Whisper)나 LLM 연동이 불필요.

### 왜 간소화가 가능한가

| 기존 설계에서 필요했던 것 | v1에서 | 이유 |
|------------------------|--------|------|
| Whisper (STT) | 불필요 | Claude가 오디오를 직접 이해 (멀티모달) |
| LLM 프로바이더 추상화 | 불필요 | Claude Code 자체가 LLM |
| Python 봇 서버 | 불필요 | MCP 플러그인이 텔레그램 연동 |
| python-telegram-bot | 불필요 | MCP 통해 메시지 수신/발신 |
| 비동기 아키텍처 | 불필요 | Claude Code가 순차 처리 |

### 필요한 것만 남기면

1. **Google Docs 문서 생성 스크립트** - 회의록을 Google Docs로 직접 생성 (Python)
2. **Claude Code 커맨드/훅** - 음성 파일 수신 시 자동 처리 흐름
3. **프롬프트 템플릿** - 회의록 형식 지정

---

## 3. 기술 스택

| 항목 | 선택 | 비고 |
|------|------|------|
| AI 엔진 | Claude Code (Max 구독) | STT + 요약 모두 처리, 추가 비용 없음 |
| 텔레그램 연동 | MCP 텔레그램 플러그인 | 이미 연동 완료 |
| 문서 생성 | Google Docs API | 회의록을 Google Docs로 직접 생성 |
| 문서 공유 | Google Drive API | 링크 공유 및 접근 권한 설정 |
| 실행 환경 | Apple Silicon Mac (로컬) | Claude Code 세션 상시 실행 |
| DB | 없음 | 파일 기반 저장 |

---

## 4. 프로젝트 구조

```
voice-summary-report/
├── .env.example                  # 환경변수 템플릿 (Google API 설정)
├── .gitignore
├── README.md
├── requirements.txt
├── docs/
│   └── DEVELOPMENT.md            # 이 문서
│
├── scripts/
│   ├── create_meeting_doc.py     # Google Docs 회의록 생성 CLI
│   └── google_docs_client.py     # Google Docs/Drive API 클라이언트
│
├── prompts/
│   └── meeting_minutes.md        # 회의록 프롬프트 템플릿
│
├── credentials/                  # Google API 인증 (gitignored)
│   └── service_account.json
│
└── data/
    └── .gitkeep
```

**v2 대비 제거된 것**: `app/` 전체, `fonts/`, 로컬 렌더러 (PDF/DOCX/MD/TXT)
**v1에서 추가된 것**: Google Docs/Drive API 연동, 링크 공유 기능

---

## 5. 데이터 흐름

```
1. 사용자 → 텔레그램 봇에 음성 파일 전송

2. Claude Code (MCP 텔레그램 플러그인으로 메시지 수신)
   ├── 음성 파일을 직접 듣고 텍스트로 변환
   ├── 회의록 형식으로 구조화 요약
   │   (prompts/meeting_minutes.md 템플릿 기반)
   │
   └── Google Docs에 회의록 문서 생성
       ├── scripts/create_meeting_doc.py 실행
       ├── Google Docs API로 문서 생성 (제목/불릿/테이블 스타일 적용)
       ├── Google Drive API로 공유 권한 설정
       └── 문서 URL 반환

3. Claude Code → 텔레그램으로 Google Docs 링크 전송
   └── "회의록이 생성되었습니다: https://docs.google.com/document/d/{id}/edit"
```

---

## 6. 핵심 컴포넌트 설계

### 6.1 회의록 프롬프트 템플릿

`prompts/meeting_minutes.md`:

```markdown
# 회의록 생성 프롬프트

다음 음성 내용을 회의록 형식으로 요약해주세요.

## 출력 형식 (JSON)

{
  "title": "회의 제목 (내용에서 추론)",
  "date": "회의 일시 (언급된 경우, 없으면 오늘 날짜)",
  "attendees": ["참석자1", "참석자2"],
  "agenda": ["안건1", "안건2"],
  "key_points": ["주요 논의사항1", "주요 논의사항2"],
  "decisions": ["결정사항1", "결정사항2"],
  "action_items": ["[담당자] 할일1", "[담당자] 할일2"],
  "summary": "전체 요약 (3-5문장)"
}

## 규칙
- 한국어로 작성
- 참석자가 명시되지 않으면 "명시되지 않음"
- 회의가 아닌 내용(강의, 독백 등)도 동일 형식으로 구조화
- JSON만 반환, 추가 설명 없이
```

### 6.2 Google Docs 문서 생성 스크립트

`scripts/create_meeting_doc.py` - Claude Code에서 Bash로 호출:

```bash
# 사용법
python scripts/create_meeting_doc.py --input meeting.json
python scripts/create_meeting_doc.py --input meeting.json --share anyone_reader
```

- JSON 파일 또는 stdin으로 회의록 데이터를 받음
- Google Docs API로 문서 생성 (제목, 본문, 불릿, 테이블 스타일 적용)
- Google Drive API로 공유 권한 설정
- 생성된 Google Docs URL을 stdout으로 출력

### 6.3 Google Docs 클라이언트

`scripts/google_docs_client.py`:

```python
class GoogleDocsClient:
    def __init__(self, credentials_path: str): ...
    def create_document(self, minutes: dict) -> str:
        """회의록 데이터로 Google Docs 문서 생성. 문서 URL 반환."""
    def set_permissions(self, document_id: str, share_mode: str):
        """문서 공유 권한 설정."""
```

### 6.4 Google Docs 공유 권한 설정

환경변수로 기본 공유 모드 설정 가능:

```env
GOOGLE_DOCS_SHARE_MODE=anyone_reader
```

| 설정값 | 동작 |
|--------|------|
| `private` | 생성자만 접근 가능 (기본값) |
| `anyone_reader` | 링크가 있는 모든 사람 읽기 가능 |
| `anyone_writer` | 링크가 있는 모든 사람 편집 가능 |
| `anyone_commenter` | 링크가 있는 모든 사람 댓글 가능 |

특정 이메일에 권한을 부여하려면 스크립트 호출 시 `--share-email user@example.com` 옵션 사용.

---

## 7. Claude Code 동작 흐름 (상세)

Claude Code 세션에서 텔레그램 MCP를 통해 메시지를 수신하면:

### Step 1: 음성 수신 및 분석
- 텔레그램 MCP로 음성 파일 수신
- Claude의 멀티모달 능력으로 오디오 직접 분석
- 별도 STT 과정 불필요

### Step 2: 회의록 생성
- `prompts/meeting_minutes.md` 템플릿에 따라 구조화
- JSON 형식의 회의록 데이터 생성

### Step 3: Google Docs 문서 생성
- JSON 데이터를 임시 파일로 저장
- `scripts/create_meeting_doc.py` 호출
- Google Docs API로 문서 생성 (회의록 형식 스타일 적용)
- Google Drive API로 공유 권한 설정 (기본: `.env`의 `GOOGLE_DOCS_SHARE_MODE`)
- 생성된 문서 URL 반환

### Step 4: 텔레그램 응답
- Google Docs 링크를 텔레그램 MCP를 통해 전송
- 요약 미리보기 텍스트도 함께 전송
- 예: "회의록이 생성되었습니다: https://docs.google.com/document/d/{id}/edit"

---

## 8. 사전 준비 사항

### 8.1 Claude Code + 텔레그램 MCP 플러그인
- Claude Code 세션 상시 실행
- 텔레그램 MCP 플러그인 연동 완료 (이미 설정됨)

### 8.2 Google Cloud 설정
1. [Google Cloud Console](https://console.cloud.google.com)에서 프로젝트 생성
2. **Google Docs API** 및 **Google Drive API** 활성화
3. **서비스 계정** 생성 후 JSON 키 다운로드
4. 키 파일을 `credentials/service_account.json`에 배치 (gitignored)

### 8.3 Python 의존성
```bash
pip install -r requirements.txt
```

---

## 9. 의존성 (v1)

```
google-api-python-client>=2.100.0   # Google Docs/Drive API
google-auth>=2.23.0                 # Google 인증
python-dotenv>=1.0.0                # 환경변수 관리
```

**v2 대비 제거된 의존성**: python-telegram-bot, openai-whisper, httpx, anthropic, openai, google-genai, fpdf2, python-docx
**v1에서 추가된 의존성**: google-api-python-client, google-auth

---

## 10. 구현 순서 (v1, 4단계)

### Step 1: 프로젝트 스캐폴딩
- 디렉토리 구조 생성 (`scripts/`, `prompts/`, `credentials/`)
- `requirements.txt` 작성
- `.env.example` 작성 (Google API 설정 포함)
- 의존성 설치

### Step 2: Google Docs 문서 생성 스크립트
- `scripts/google_docs_client.py` - Google Docs/Drive API 클라이언트
  - 서비스 계정 인증
  - 문서 생성 (제목, 본문, 불릿, 테이블 스타일)
  - 공유 권한 설정
- `scripts/create_meeting_doc.py` - CLI 진입점
  - JSON 입력 → Google Docs 생성 → URL 출력

### Step 3: 프롬프트 템플릿
- `prompts/meeting_minutes.md` 작성
- Claude Code가 참조할 회의록 생성 가이드

### Step 4: 통합 테스트 및 문서화
- 샘플 회의록 JSON으로 Google Docs 생성 테스트
- 공유 링크 접근 확인
- 실제 음성 파일로 end-to-end 테스트
- README.md 완성

---

## 11. 검증 방법

1. 샘플 회의록 JSON으로 `scripts/create_meeting_doc.py` 실행 → Google Docs 문서 생성 확인
2. 생성된 링크 접근 → 회의록 포맷(제목/불릿/테이블) 정상 확인
3. 공유 권한 설정 동작 확인 (private, anyone_reader 등)
4. 텔레그램에서 한국어 음성 메모 전송 → Claude Code가 MCP로 수신 → 회의록 JSON 생성 확인
5. 전체 흐름: 음성 전송 → Google Docs 생성 → 텔레그램으로 링크 수신 확인

---

## 12. 에러 처리

| 실패 지점 | 처리 방식 |
|-----------|----------|
| 음성 인식 불가 | Claude가 "음성을 인식할 수 없습니다" 텔레그램 응답 |
| 회의 내용 아님 | 동일 형식으로 구조화 (강의/독백도 처리) |
| Google API 인증 실패 | "Google API 인증에 실패했습니다" 에러 + 로그 |
| Google Docs 생성 실패 | Claude가 텍스트 형태로 회의록 직접 텔레그램 전송 (폴백) |
| 공유 권한 설정 실패 | 문서는 생성되었으나 공유 실패 안내 + 수동 공유 가이드 |

---

---

# v2: 독립 Python 봇 서버 (풀버전, 추후 개발)

> v1으로 충분한 경우 v2 개발은 선택 사항.
> v2는 Claude Code 없이 독립 실행 가능한 24/7 봇 서버를 목표로 한다.

## 13. v2 아키텍처

```
사용자 → 텔레그램 음성/오디오 전송
         │
         ▼
  [Python 봇 서버 (python-telegram-bot)]
         │
         ├── [Whisper 로컬] 음성→텍스트 변환
         │
         ├── [LLM 프로바이더] 텍스트→회의록 요약
         │   ├── Ollama (기본, 무료)
         │   ├── Claude API
         │   ├── OpenAI API
         │   └── Gemini API
         │
         ├── [문서 생성] PDF/DOCX/MD/TXT
         │
         └── 텔레그램으로 문서 전송
```

## 14. v2 기술 스택

| 항목 | 선택 | 비고 |
|------|------|------|
| 언어 | Python 3.11+ | 단일 런타임 |
| 텔레그램 봇 | python-telegram-bot ≥21.0 | async 지원 |
| STT | OpenAI Whisper (로컬) | base 모델, MPS 가속 |
| AI 요약 | 플러그형 LLM | Ollama(무료) / Claude / OpenAI / Gemini |
| PDF | fpdf2 | 한글 지원 |
| DOCX | python-docx | Word 문서 생성 |
| 실행 환경 | Apple Silicon Mac | MPS 가속 |

## 15. v2 프로젝트 구조

```
voice-summary-report/
├── .env.example
├── .env                          # gitignored
├── .gitignore
├── README.md
├── requirements.txt
├── pyproject.toml
├── Makefile
│
├── app/
│   ├── __init__.py
│   ├── main.py                   # 진입점
│   ├── config.py                 # Settings 데이터클래스
│   ├── models.py                 # MeetingMinutes 데이터클래스
│   │
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── handlers.py           # 텔레그램 핸들러
│   │   └── keyboards.py          # 인라인 키보드
│   │
│   ├── transcription/
│   │   ├── __init__.py
│   │   └── whisper_client.py     # Whisper STT (MPS 가속)
│   │
│   ├── summarization/
│   │   ├── __init__.py
│   │   ├── base.py               # LLMProvider 추상 클래스
│   │   ├── factory.py            # 프로바이더 팩토리
│   │   ├── prompts.py            # 프롬프트 템플릿
│   │   ├── ollama_provider.py    # Ollama (무료)
│   │   ├── claude_provider.py    # Claude API
│   │   ├── openai_provider.py    # OpenAI API
│   │   └── gemini_provider.py    # Gemini API
│   │
│   ├── document/
│   │   ├── __init__.py
│   │   ├── generator.py          # 형식별 디스패처
│   │   ├── pdf_renderer.py
│   │   ├── docx_renderer.py
│   │   ├── markdown_renderer.py
│   │   └── txt_renderer.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── audio.py              # 오디오 다운로드/변환
│       └── storage.py            # 파일 경로 관리
│
├── data/
│   ├── audio/
│   └── output/
│
├── tests/
│   ├── test_config.py
│   ├── test_whisper_client.py
│   ├── test_llm_providers.py
│   ├── test_document_generator.py
│   └── test_handlers.py
│
└── fonts/
    └── NanumGothic.ttf
```

## 16. v2 LLM 프로바이더 설계

### 추상 인터페이스

```python
class LLMProvider(ABC):
    @abstractmethod
    async def summarize(self, transcript: str, language: str = "ko") -> MeetingMinutes: ...
```

### 프로바이더 팩토리

```python
def create_llm_provider(settings: Settings) -> LLMProvider:
    match settings.llm_provider:
        case "ollama":  return OllamaProvider(settings)
        case "claude":  return ClaudeProvider(settings)
        case "openai":  return OpenAIProvider(settings)
        case "gemini":  return GeminiProvider(settings)
```

### 환경 설정으로 전환

```env
LLM_PROVIDER=ollama          # ollama | claude | openai | gemini
LLM_MODEL=llama3.1:8b        # 프로바이더별 모델명
```

## 17. v2 환경 설정 (.env.example)

```env
# === 필수 ===
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# === LLM 프로바이더 ===
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b
OLLAMA_BASE_URL=http://localhost:11434

# Claude (유료): LLM_PROVIDER=claude, ANTHROPIC_API_KEY=your-key
# OpenAI (유료): LLM_PROVIDER=openai, OPENAI_API_KEY=your-key
# Gemini (무료 티어): LLM_PROVIDER=gemini, GOOGLE_API_KEY=your-key

# === Whisper ===
WHISPER_MODEL_SIZE=base
WHISPER_DEVICE=mps

# === 일반 ===
MAX_AUDIO_FILE_MB=20
DATA_DIR=./data
LANGUAGE=ko
LOG_LEVEL=INFO
```

## 18. v2 의존성

```
python-telegram-bot>=21.0
openai-whisper
httpx>=0.27.0
anthropic>=0.39.0
openai>=1.40.0
google-genai>=1.0.0
fpdf2>=2.8.0
python-docx>=1.1.0
python-dotenv>=1.0.0
pytest>=8.0
pytest-asyncio>=0.24.0
```

## 19. v2 구현 순서 (9단계)

1. 프로젝트 스캐폴딩
2. 설정 모듈 + 데이터 모델
3. Whisper STT 모듈 (MPS 가속)
4. LLM 프로바이더 모듈 (Ollama/Claude/OpenAI/Gemini)
5. 문서 생성 모듈 (PDF/DOCX/MD/TXT)
6. 유틸리티 모듈 (audio, storage)
7. 텔레그램 봇 핸들러
8. 에러 처리 및 마무리
9. 문서화

---

## 20. v1 vs v2 비교

| 항목 | v1 (간소화) | v2 (풀버전) |
|------|-----------|-----------|
| 코드량 | ~200줄 | ~1500줄 |
| 의존성 | 2개 (fpdf2, python-docx) | 11개 |
| STT | Claude 내장 (멀티모달) | Whisper 로컬 |
| LLM | Claude Code 세션 | 플러그형 (Ollama 등) |
| 텔레그램 | MCP 플러그인 | python-telegram-bot 서버 |
| 비용 | Claude Max 구독만 | Ollama 무료 / API 유료 |
| 독립 실행 | Claude Code 세션 필요 | 독립 실행 가능 |
| 확장성 | Claude Code에 의존 | 자유로운 확장 |
| 포트폴리오 가치 | 낮음 (구성 위주) | 높음 (풀스택 구현) |

---

## 21. 2차 개발 범위 (Phase 2, 공통)

- Notion API 연동: 회의록을 Notion 페이지로 직접 생성
- Google Docs 연동: Google Docs API로 문서 업로드
- 다국어 지원 확장
- 회의록 템플릿 커스터마이징
