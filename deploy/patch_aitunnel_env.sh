#!/bin/bash
set -e
ENV=/home/mentor/english-mentor-bot/.env
upsert() {
  local k="$1" v="$2"
  if grep -q "^${k}=" "$ENV"; then
    sed -i "s|^${k}=.*|${k}=${v}|" "$ENV"
  else
    echo "${k}=${v}" >> "$ENV"
  fi
}
upsert TTS_PROVIDER openai
upsert OPENAI_TTS_MODEL gpt-4o-mini-tts
upsert STT_PROVIDER whisper
upsert STT_YANDEX_FALLBACK false
echo "AITUNNEL env patched"
