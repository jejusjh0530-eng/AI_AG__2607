"""Typecast text-to-speech CLI - direct REST API integration (stdlib only, no SDK).

Reads the API key from the TYPECAST_API_KEY environment variable.
Get a key at: https://studio.typecast.ai/developers/api/

Usage:
    python typecast_tts.py list-voices
    python typecast_tts.py speak --voice-id tc_xxxx --text "안녕하세요" --output output/typecast/greeting.wav
    python typecast_tts.py speak --voice-id tc_xxxx --text "정말 신나요!" --emotion happy --format mp3
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API_BASE = "https://api.typecast.ai"
DEFAULT_MODEL = "ssfm-v30"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "typecast"


def get_api_key() -> str:
    api_key = os.environ.get("TYPECAST_API_KEY")
    if not api_key:
        sys.exit(
            "TYPECAST_API_KEY 환경변수가 설정되어 있지 않습니다.\n"
            "https://studio.typecast.ai/developers/api/ 에서 키를 발급받은 뒤 설정하세요.\n"
            '  PowerShell: $env:TYPECAST_API_KEY = "발급받은키"\n'
            '  Bash:       export TYPECAST_API_KEY="발급받은키"'
        )
    return api_key


def call_api(
    method: str, path: str, api_key: str, payload: dict | None = None, api_version: str = "v1"
) -> bytes:
    url = f"{API_BASE}/{api_version}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("X-API-KEY", api_key)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        sys.exit(f"Typecast API 오류 (HTTP {e.code}): {body}")


def list_voices(args):
    api_key = get_api_key()
    query = []
    if args.gender:
        query.append(f"gender={args.gender}")
    if args.age:
        query.append(f"age={args.age}")
    path = "/voices" + (f"?{'&'.join(query)}" if query else "")
    body = call_api("GET", path, api_key, api_version="v2")
    voices = json.loads(body)
    if args.use_case:
        voices = [v for v in voices if args.use_case in v.get("use_cases", [])]
    print(f"총 {len(voices)}개 캐릭터\n")
    for v in voices:
        use_cases = ", ".join(v.get("use_cases", []))
        print(
            f"{v.get('voice_id')}\t{v.get('voice_name')}\t"
            f"{v.get('gender')}/{v.get('age')}\t용도: {use_cases}"
        )


def speak(args):
    api_key = get_api_key()
    payload = {
        "voice_id": args.voice_id,
        "text": args.text,
        "model": args.model,
        "output": {"audio_format": args.format},
    }
    if args.language:
        payload["language"] = args.language
    if args.emotion:
        payload["prompt"] = {"emotion_type": "preset", "emotion_preset": args.emotion}

    audio = call_api("POST", "/text-to-speech", api_key, payload)

    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT_DIR / f"tts.{args.format}"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(audio)
    print(f"저장 완료: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Typecast TTS API 연동 CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list-voices", help="사용 가능한 캐릭터(보이스) 목록 조회")
    p_list.add_argument("--gender", choices=["male", "female"], help="성별 필터")
    p_list.add_argument(
        "--age",
        choices=["child", "young_adult", "middle_age", "senior"],
        help="연령대 필터",
    )
    p_list.add_argument(
        "--use-case", help="용도 필터 (예: Conversational, Announcer, TikTok/Reels/Shorts)"
    )
    p_list.set_defaults(func=list_voices)

    p_speak = sub.add_parser("speak", help="텍스트를 음성 파일로 변환")
    p_speak.add_argument("--voice-id", required=True, help="캐릭터 voice_id (예: tc_xxxx)")
    p_speak.add_argument("--text", required=True, help="변환할 텍스트 (최대 2000자)")
    p_speak.add_argument("--model", default=DEFAULT_MODEL, help="TTS 모델 (기본값: ssfm-v30)")
    p_speak.add_argument("--language", help="ISO 639-3 언어 코드 (예: kor, eng)")
    p_speak.add_argument("--emotion", help="감정 프리셋 (예: happy, sad, angry, normal)")
    p_speak.add_argument("--format", default="wav", choices=["wav", "mp3"], help="출력 오디오 포맷")
    p_speak.add_argument("--output", help="저장 경로 (기본값: output/typecast/tts.<format>)")
    p_speak.set_defaults(func=speak)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
