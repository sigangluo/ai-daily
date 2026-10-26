#!/usr/bin/env python3
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from fetchers import fetch_source

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "sources.yaml"
DATA_PATH = ROOT / "site" / "data" / "latest.json"
SHANGHAI = ZoneInfo("Asia/Shanghai")
TIERS = {
    "T1": ("官方一手", "模型发布与官方博客"),
    "T2": ("聚合媒体", "行业新闻与全景动态"),
    "T3": ("社区与项目", "开源项目、新产品与技术社区"),
    "T4": ("深度写作", "低频、高质量的长期阅读"),
}
REGIONS = (("cn", "国内"), ("intl", "国外"))
RETENTION_DAYS = 30
DAILY_FETCH_DAYS = 1


def log(message):
    print(message, file=sys.stderr, flush=True)


def load_sources():
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    sources = [source for source in config["sources"] if source.get("enabled")]
    ids = set()
    for source in sources:
        missing = [key for key in ("id", "name", "tier", "region", "type", "url") if not source.get(key)]
        if missing:
            raise ValueError(f"信源缺少字段 {missing}: {source}")
        if source["id"] in ids:
            raise ValueError(f"重复的信源 ID: {source['id']}")
        if source["tier"] not in TIERS:
            raise ValueError(f"一期不支持层级 {source['tier']}: {source['id']}")
        if dict(REGIONS).get(source["region"]) is None:
            raise ValueError(f"未知地区 {source['region']}: {source['id']}")
        if not source["url"].startswith("https://"):
            raise ValueError(f"信源必须使用 HTTPS: {source['id']}")
        ids.add(source["id"])
    if not sources:
        raise ValueError("没有已启用的信源")
    return sources


def previous_sources():
    if not DATA_PATH.exists():
        return {}
    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {source["id"]: source for source in data.get("sources", [])}


def normalize_items(items, now, days):
    earliest = now.date() - timedelta(days=days)
    unique = {}
    for item in items:
        url = item.get("url", "")
        title = " ".join(item.get("title", "").split())
        date = item.get("date", "")
        if not title or not url or not date:
            continue
        try:
            published = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            continue
        if published > now.date() + timedelta(days=1) or published < earliest:
            continue
        normalized = {"title": title[:500], "url": url, "date": date}
        if item.get("description"):
            normalized["description"] = " ".join(item["description"].split())[:300]
        if item.get("meta"):
            normalized["meta"] = item["meta"][:4]
        unique[url] = normalized
    return sorted(unique.values(), key=lambda item: (item["date"], item["title"]), reverse=True)


def build_source(source, now, previous, fetch_days):
    result = {key: source[key] for key in ("id", "name", "tier", "region")}
    old = previous.get(source["id"], {})
    old_items = normalize_items(old.get("items", []), now, RETENTION_DAYS)
    try:
        fetched = fetch_source(source)
        fresh_items = normalize_items(fetched, now, fetch_days)
        items = fresh_items if fetch_days == RETENTION_DAYS else normalize_items(fresh_items + old_items, now, RETENTION_DAYS)
        result.update({"url": source["url"], "status": "ok", "items": items, "fresh_items": len(fresh_items)})
        log(f"OK  {source['id']}: 抓取 {len(fetched)} 条，本次新增/更新 {len(fresh_items)} 条，本月保留 {len(items)} 条")
    except Exception as error:
        result.update({
            "url": source["url"],
            "status": "error",
            "error": str(error)[:300],
            "items": old_items,
        })
        if old_items:
            result["stale"] = True
        log(f"ERR {source['id']}: {error}")
    return result


def main():
    parser = argparse.ArgumentParser(description="抓取启用的信源并生成 site/data/latest.json")
    parser.add_argument("--only", help="只更新指定信源 ID，多个用逗号分隔")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--bootstrap", action="store_true", help="回填最近 30 天；默认每日增量拉取最近 1 天")
    args = parser.parse_args()
    fetch_days = RETENTION_DAYS if args.bootstrap else DAILY_FETCH_DAYS
    sources = load_sources()
    previous = previous_sources()
    if args.only:
        wanted = set(args.only.split(","))
        unknown = wanted - {source["id"] for source in sources}
        if unknown:
            raise SystemExit(f"未知或未启用的信源: {', '.join(sorted(unknown))}")
        sources = [source for source in sources if source["id"] in wanted]
        merged = dict(previous)
    else:
        merged = {}
    now = datetime.now(SHANGHAI)
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 12))) as pool:
        futures = {pool.submit(build_source, source, now, previous, fetch_days): source for source in sources}
        for future in as_completed(futures):
            result = future.result()
            merged[result["id"]] = result
    enabled = load_sources()
    ordered = [merged[source["id"]] for source in enabled if source["id"] in merged]
    missing = [source["id"] for source in enabled if source["id"] not in merged]
    if missing:
        raise SystemExit(f"以下信源没有数据，请先完整更新: {', '.join(missing)}")
    output = {
        "generated_at": now.isoformat(timespec="seconds"),
        "retention_days": RETENTION_DAYS,
        "fetch_days": fetch_days,
        "tiers": [{"id": key, "name": value[0], "description": value[1]} for key, value in TIERS.items()],
        "regions": [{"id": key, "name": value} for key, value in REGIONS],
        "sources": ordered,
    }
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    item_count = sum(len(source["items"]) for source in ordered)
    error_count = sum(source["status"] == "error" for source in ordered)
    log(f"完成：{len(ordered)} 个信源，{item_count} 条内容，{error_count} 个异常 → {DATA_PATH}")


if __name__ == "__main__":
    main()
