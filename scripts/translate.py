import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_PATH = ROOT / "data" / "translations.json"
API_URL = "https://api.deepseek.com/chat/completions"
BATCH_SIZE = 20
SKIP_SOURCES = {"github-trending", "producthunt"}


def log(message):
    print(message, file=sys.stderr, flush=True)


def load_cache():
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_cache(cache):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def translation_key(item):
    return hashlib.sha256((item["url"] + "\n" + item["title"]).encode("utf-8")).hexdigest()


def call_deepseek(batch, api_key):
    payload = [{"id": translation_key(item), "title": item["title"]} for item in batch]
    messages = [
        {"role": "system", "content": "你是技术资讯标题翻译器。把标题翻译成自然、准确、简洁的简体中文。保留模型、产品、公司、协议、框架和仓库的专有名称，不增删事实，不输出解释。只返回 JSON 对象 translations，键为输入 id，值为中文标题。"},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]
    body = json.dumps({"model": "deepseek-chat", "messages": messages, "temperature": 0.2,
                       "max_tokens": 4000, "stream": False}).encode("utf-8")
    last_error = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(API_URL, data=body, headers={
                "Authorization": "Bearer " + api_key,
                "Content-Type": "application/json",
                "User-Agent": "ai-daily/1.0",
            })
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.load(response)
            content = result["choices"][0]["message"]["content"].strip()
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.S).strip()
            translated = json.loads(content)["translations"]
            expected = {entry["id"] for entry in payload}
            if set(translated) != expected or any(not str(value).strip() for value in translated.values()):
                raise RuntimeError("翻译结果缺少条目或包含空标题")
            return {key: str(value).strip() for key, value in translated.items()}
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError, RuntimeError) as error:
            last_error = error
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"DeepSeek 翻译失败: {last_error}")


def localize_items(sources):
    cache = load_cache()
    pending = []
    official_count = 0
    for source in sources:
        for item in source["items"]:
            key = translation_key(item)
            if item.get("title_zh"):
                item["title_zh_source"] = "official"
                cache[key] = item["title_zh"]
                official_count += 1
            elif re.search(r"[\u3400-\u9fff]", item["title"]):
                item["title_zh"] = item["title"]
                item["title_zh_source"] = "official"
                cache[key] = item["title_zh"]
                official_count += 1
            elif key in cache:
                item["title_zh"] = cache[key]
                item["title_zh_source"] = "deepseek"
            elif source["id"] not in SKIP_SOURCES:
                pending.append(item)
    save_cache(cache)
    if not pending:
        log(f"中文标题：官方 {official_count} 条，缓存/已有翻译覆盖其余条目，无需调用 DeepSeek")
        return
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        log(f"警告：{len(pending)} 条标题需要 DeepSeek 翻译，但未配置 DEEPSEEK_API_KEY，暂时保留原文")
        return
    log(f"中文标题：官方 {official_count} 条，待 DeepSeek 翻译 {len(pending)} 条")
    completed = 0
    for start in range(0, len(pending), BATCH_SIZE):
        batch = pending[start:start + BATCH_SIZE]
        translated = call_deepseek(batch, api_key)
        for item in batch:
            key = translation_key(item)
            cache[key] = translated[key]
            item["title_zh"] = cache[key]
            item["title_zh_source"] = "deepseek"
        save_cache(cache)
        completed += len(batch)
        log(f"  DeepSeek 已翻译 {completed}/{len(pending)}")
