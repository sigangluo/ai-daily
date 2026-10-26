import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from zoneinfo import ZoneInfo

USER_AGENT = "ai-daily/1.0 (+https://github.com/sigangluo/ai-daily)"
SHANGHAI = ZoneInfo("Asia/Shanghai")


def request(url, body=None, extra_headers=None):
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    headers.update(extra_headers or {})
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    last_error = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"请求失败: {last_error}")


def local_name(tag):
    return tag.rsplit("}", 1)[-1].lower()


def clean_text(value):
    return re.sub(r"\s+", " ", unescape(value or "")).strip()


def clean_url(value, base):
    url = urllib.parse.urljoin(base, unescape(value or "").strip())
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ""
    query = [(key, val) for key, val in urllib.parse.parse_qsl(parsed.query)
             if not key.lower().startswith("utm_")]
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path,
                                    urllib.parse.urlencode(query), ""))


def date_text(value):
    if not value:
        return ""
    raw = value.strip()
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            for fmt in ("%b %d, %Y", "%B %d, %Y"):
                try:
                    return datetime.strptime(raw, fmt).date().isoformat()
                except ValueError:
                    pass
            match = re.search(r"\d{4}-\d{2}-\d{2}", raw)
            return match.group(0) if match else ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(SHANGHAI).date().isoformat()


def timestamp_text(value):
    try:
        return datetime.fromtimestamp(int(value), timezone.utc).astimezone(SHANGHAI).date().isoformat()
    except (TypeError, ValueError, OSError):
        return ""


def child_values(node, names):
    return [clean_text(child.text) for child in node if local_name(child.tag) in names]


def parse_feed(raw, source):
    root = ET.fromstring(raw)
    entries = [node for node in root.iter() if local_name(node.tag) in ("item", "entry")]
    items = []
    for entry in entries:
        titles = child_values(entry, ("title",))
        title = titles[0] if titles else ""
        dates = child_values(entry, ("pubdate", "published", "updated", "date"))
        url = ""
        for link in [child for child in entry if local_name(child.tag) == "link"]:
            href = link.attrib.get("href", "")
            rel = link.attrib.get("rel", "alternate")
            if href and rel == "alternate":
                url = href
                break
            if not url:
                url = href or clean_text(link.text)
        if not url:
            urls = child_values(entry, ("guid", "id"))
            url = next((value for value in urls if value.startswith(("http://", "https://"))), "")
        url = clean_url(url, source["url"])
        if title and url:
            items.append({"title": title, "url": url, "date": date_text(dates[0] if dates else "")})
    return items


class HeadingArticleParser(HTMLParser):
    def __init__(self, base_url):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.articles = []
        self.article = None
        self.anchor = None
        self.heading_depth = 0
        self.in_time = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "article":
            self.article = {"links": [], "date": "", "title": []}
        elif self.article is not None and tag == "a":
            self.anchor = {"url": clean_url(attrs.get("href", ""), self.base_url), "heading": [], "plain": []}
        elif self.article is not None and tag in ("h1", "h2", "h3"):
            self.heading_depth += 1
        elif self.article is not None and tag == "time":
            self.in_time = True
            if attrs.get("datetime"):
                self.article["date"] = date_text(attrs["datetime"])

    def handle_endtag(self, tag):
        if tag == "article" and self.article is not None:
            article_title = clean_text(" ".join(self.article["title"]))
            candidates = [link for link in self.article["links"] if clean_text(" ".join(link["heading"]))]
            if not candidates and article_title:
                candidates = [link for link in self.article["links"]
                              if clean_text(" ".join(link["plain"])) == article_title]
            if candidates and candidates[0]["url"]:
                self.articles.append({"title": article_title, "url": candidates[0]["url"], "date": self.article["date"]})
            self.article = None
            self.anchor = None
        elif tag == "a" and self.anchor is not None:
            if self.article is not None:
                self.article["links"].append(self.anchor)
            self.anchor = None
            self.heading_depth = 0
        elif tag in ("h1", "h2", "h3") and self.heading_depth:
            self.heading_depth -= 1
        elif tag == "time":
            self.in_time = False

    def handle_data(self, data):
        if self.article is not None and self.heading_depth:
            self.article["title"].append(data)
        if self.anchor is not None:
            self.anchor["plain"].append(data)
            if self.heading_depth:
                self.anchor["heading"].append(data)
        if self.in_time and self.article is not None and not self.article["date"]:
            self.article["date"] = date_text(data)


class DeepSeekParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items = []
        self.current = None
        self.heading_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set(attrs.get("class", "").split())
        if tag == "a" and classes.intersection(("ds-news-hero-card", "ds-news-list-item")):
            self.current = {"url": clean_url(attrs.get("href", ""), "https://www.deepseek.com"),
                            "title": [], "text": []}
        elif self.current is not None and tag in ("h2", "h3"):
            self.heading_depth += 1

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            title = clean_text(" ".join(self.current["title"]))
            text = clean_text(" ".join(self.current["text"]))
            match = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", text)
            if title and self.current["url"] and match:
                date = f"{int(match.group(1)):04d}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
                self.items.append({"title": title, "url": self.current["url"], "date": date})
            self.current = None
            self.heading_depth = 0
        elif tag in ("h2", "h3") and self.heading_depth:
            self.heading_depth -= 1

    def handle_data(self, data):
        if self.current is not None:
            self.current["text"].append(data)
            if self.heading_depth:
                self.current["title"].append(data)


def parse_deepseek(raw):
    parser = DeepSeekParser()
    parser.feed(raw.decode("utf-8", "replace"))
    return parser.items


def date_from_text(value):
    text = clean_text(value)
    chinese = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", text)
    if chinese:
        return f"{int(chinese.group(1)):04d}-{int(chinese.group(2)):02d}-{int(chinese.group(3)):02d}"
    iso = re.search(r"\d{4}-\d{2}-\d{2}", text)
    if iso:
        return iso.group(0)
    english = re.search(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4}", text)
    return date_text(english.group(0)) if english else ""


class AnchorCardParser(HTMLParser):
    def __init__(self, base_url, prefixes):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.prefixes = prefixes
        self.items = []
        self.current = None
        self.heading_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and self.current is None:
            url = clean_url(attrs.get("href", ""), self.base_url)
            if url and any(urllib.parse.urlsplit(url).path.startswith(prefix) for prefix in self.prefixes):
                self.current = {"url": url, "title": [], "text": []}
        elif self.current is not None and tag in ("h2", "h3"):
            self.heading_depth += 1

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            title = clean_text(" ".join(self.current["title"]))
            date = date_from_text(" ".join(self.current["text"]))
            if title and date:
                self.items.append({"title": title, "url": self.current["url"], "date": date})
            self.current = None
            self.heading_depth = 0
        elif tag in ("h2", "h3") and self.heading_depth:
            self.heading_depth -= 1

    def handle_data(self, data):
        if self.current is not None:
            self.current["text"].append(data)
            if self.heading_depth:
                self.current["title"].append(data)


class KimiParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items = []
        self.current = None
        self.depth = 0
        self.in_date = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        if tag == "div" and "menu-card" in classes and self.current is None:
            self.current = {"url": "", "title": "", "date": []}
            self.depth = 1
        elif self.current is not None and tag == "div":
            self.depth += 1
        if self.current is None:
            return
        if tag == "a" and attrs.get("href", "").startswith("/blog/"):
            self.current["url"] = clean_url(attrs["href"], "https://www.kimi.ai")
            self.current["title"] = clean_text(attrs.get("aria-label", "")) or self.current["title"]
        elif tag == "h4" and "card-title" in classes:
            self.current["heading"] = []
        elif tag == "p" and "card-date" in classes:
            self.in_date = True

    def handle_endtag(self, tag):
        if self.current is None:
            return
        if tag == "h4" and "heading" in self.current:
            self.current["title"] = self.current["title"] or clean_text(" ".join(self.current.pop("heading")))
        elif tag == "p":
            self.in_date = False
        elif tag == "div":
            self.depth -= 1
            if self.depth == 0:
                date = date_from_text(" ".join(self.current["date"]))
                if self.current["title"] and self.current["url"] and date:
                    self.items.append({"title": self.current["title"], "url": self.current["url"], "date": date})
                self.current = None

    def handle_data(self, data):
        if self.current is None:
            return
        if self.in_date:
            self.current["date"].append(data)
        if "heading" in self.current:
            self.current["heading"].append(data)


class ZaiParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items = []
        self.current = None
        self.depth = 0
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "div" and "update-container" in attrs.get("class", "").split() and self.current is None:
            date = attrs.get("id", "")
            self.current = {"date": date, "title": [],
                            "url": f"https://docs.z.ai/release-notes/new-released#{date}"}
            self.depth = 1
        elif self.current is not None and tag == "div":
            self.depth += 1
            if attrs.get("data-component-part") == "update-description":
                self.in_title = True

    def handle_endtag(self, tag):
        if self.current is None or tag != "div":
            return
        if self.in_title:
            self.in_title = False
        self.depth -= 1
        if self.depth == 0:
            title = clean_text(" ".join(self.current["title"]))
            if title and re.fullmatch(r"\d{4}-\d{2}-\d{2}", self.current["date"]):
                self.items.append({"title": title, "url": self.current["url"], "date": self.current["date"]})
            self.current = None

    def handle_data(self, data):
        if self.current is not None and self.in_title:
            self.current["title"].append(data)


def parse_cards(raw, base_url, prefixes):
    parser = AnchorCardParser(base_url, prefixes)
    parser.feed(raw.decode("utf-8", "replace"))
    return parser.items


def parse_kimi(raw):
    parser = KimiParser()
    parser.feed(raw.decode("utf-8", "replace"))
    return parser.items


def parse_zai(raw):
    parser = ZaiParser()
    parser.feed(raw.decode("utf-8", "replace"))
    return parser.items


def parse_stepfun(raw):
    text = raw.decode("utf-8", "replace")
    items = parse_cards(raw, "https://www.stepfun.com", ("/news/",))
    if items:
        return items
    pattern = re.compile(r"\[(.*?)\]\((https://www\.stepfun\.com/news/[^)]+)\)", re.S)
    for match in pattern.finditer(text):
        body, url = match.groups()
        images = re.findall(r"!\[Image \d+:\s*(.*?)\]\([^)]+\)", body, re.S)
        title = clean_text(images[-1]) if images else ""
        date = date_from_text(body)
        if title and date:
            items.append({"title": title, "url": url, "date": date})
    return items


def parse_minimax_news(raw):
    payload = json.loads(raw)
    items = []
    for entry in payload.get("data") or []:
        title = clean_text(entry.get("title"))
        slug = entry.get("slug", "")
        try:
            date = timestamp_text(entry.get("publishDate") / 1000)
        except (TypeError, KeyError):
            date = ""
        if title and slug and date:
            items.append({"title": title, "url": f"https://www.minimax.io/news/{slug}", "date": date})
    return items


def parse_qwen(raw):
    payload = json.loads(raw)
    items = []
    for entry in payload.get("data", {}).get("articles", []):
        extra = entry.get("extra") or {}
        title = clean_text(entry.get("title"))
        path = entry.get("path", "")
        date = date_text(extra.get("date", ""))
        if title and path and date:
            items.append({"title": title, "url": f"https://qwen.ai/research/{path}", "date": date})
    return items


def parse_jina_feed(raw):
    text = raw.decode("utf-8", "replace")
    items = []
    pattern = re.compile(r"### \[(.*?)\]\((https?://[^)]+)\)(.*?)(?=^### \[|\Z)", re.M | re.S)
    for match in pattern.finditer(text):
        title = clean_text(match.group(1))
        url = clean_url(match.group(2), "https://deepmind.google")
        date_match = re.search(r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),[^\n]+", match.group(3))
        date = date_text(date_match.group(0)) if date_match else ""
        if title and url and date:
            items.append({"title": title, "url": url, "date": date})
    return items


def parse_substack(raw):
    text = raw.decode("utf-8", "replace")
    marker = "Markdown Content:\n"
    payload = text.split(marker, 1)[1].lstrip() if marker in text else text
    items = []
    for entry in json.loads(payload):
        title = clean_text(entry.get("title"))
        url = clean_url(entry.get("canonical_url", ""), "https://importai.substack.com")
        date = date_text(entry.get("post_date", ""))
        if title and url and date:
            items.append({"title": title, "url": url, "date": date})
    return items


class TrendingParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items = []
        self.item = None
        self.anchor = None
        self.in_heading = False
        self.in_description = False
        self.in_language = False
        self.in_time = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        if tag == "article":
            self.item = {"title": "", "url": "", "date": datetime.now(SHANGHAI).date().isoformat(),
                         "description": "", "meta": []}
        elif self.item is None:
            return
        if tag == "a" and self.in_heading:
            self.anchor = attrs.get("href", "")
        elif tag == "p" and "col-9" in classes:
            self.in_description = True
        elif attrs.get("itemprop") == "programmingLanguage":
            self.in_language = True
        elif tag == "h2":
            self.in_heading = True

    def handle_endtag(self, tag):
        if tag == "article" and self.item is not None:
            self.item["title"] = clean_text(self.item["title"]).replace(" / ", "/")
            self.item["description"] = clean_text(self.item["description"])
            if self.item["title"] and self.item["url"]:
                self.items.append(self.item)
            self.item = None
            self.anchor = None
        elif self.item is None:
            return
        if tag == "h2":
            self.in_heading = False
            if self.anchor:
                self.item["url"] = clean_url(self.anchor, "https://github.com")
        elif tag == "p":
            self.in_description = False
        elif tag == "span":
            self.in_language = False

    def handle_data(self, data):
        if self.item is None:
            return
        if self.in_heading:
            self.item["title"] += data
        elif self.in_description:
            self.item["description"] += data
        elif self.in_language:
            language = clean_text(data)
            if language and language not in self.item["meta"]:
                self.item["meta"].append(language)
        today = re.search(r"([\d,]+)\s+stars\s+today", data, re.I)
        if today:
            self.item["meta"].append(f"{today.group(1)} stars today")


def parse_anthropic(raw):
    parser = HeadingArticleParser("https://www.anthropic.com")
    parser.feed(raw.decode("utf-8", "replace"))
    return parser.articles


def parse_trending(raw):
    parser = TrendingParser()
    parser.feed(raw.decode("utf-8", "replace"))
    return parser.items


def parse_juejin(raw):
    payload = json.loads(raw)
    if payload.get("err_no") != 0:
        raise RuntimeError(f"掘金 API: {payload.get('err_msg', '未知错误')}")
    items = []
    for entry in payload.get("data") or []:
        info = entry.get("article_info") or {}
        article_id = info.get("article_id") or entry.get("article_id")
        title = clean_text(info.get("title"))
        url = clean_url(info.get("link_url") or f"https://juejin.cn/post/{article_id}", "https://juejin.cn")
        if title and article_id and url:
            items.append({"title": title, "url": url, "date": timestamp_text(info.get("ctime"))})
    return items


def fetch_source(source):
    source_id = source["id"]
    if source_id == "juejin-ai":
        raw = request(source["url"], {"id_type": 2, "sort_type": 300, "cate_id": "6809637773935378440", "limit": 30, "cursor": "0"})
        items = parse_juejin(raw)
    elif source_id == "deepmind-blog":
        try:
            items = parse_feed(request(source["url"]), source)
        except Exception:
            raw = request("https://r.jina.ai/" + source["url"], extra_headers={"X-No-Cache": "true"})
            items = parse_jina_feed(raw)
    else:
        formats = {"deepseek-news": "html", "stepfun-news": "markdown"}
        extra_headers = {"X-No-Cache": "true"} if source["url"].startswith("https://r.jina.ai/") else {}
        if source_id in formats:
            extra_headers["X-Return-Format"] = formats[source_id]
        raw = request(source["url"], extra_headers=extra_headers)
        if source_id == "deepseek-news":
            items = parse_deepseek(raw)
        elif source_id == "qwen-research":
            items = parse_qwen(raw)
        elif source_id == "glm-release-notes":
            items = parse_zai(raw)
        elif source_id == "kimi-blog":
            items = parse_kimi(raw)
        elif source_id == "minimax-blog":
            items = parse_cards(raw, "https://www.minimax.io", ("/blog/",))
        elif source_id == "minimax-news":
            items = parse_minimax_news(raw)
        elif source_id == "stepfun-news":
            items = parse_stepfun(raw)
        elif source_id.startswith("anthropic-"):
            items = parse_anthropic(raw)
        elif source_id == "github-trending":
            items = parse_trending(raw)
        elif source_id == "import-ai":
            items = parse_substack(raw)
        elif source["type"] in ("rss", "atom", "wechat"):
            items = parse_feed(raw, source)
        else:
            raise RuntimeError(f"暂不支持的信源类型: {source['type']}")
    if source["type"] in ("web_list", "json_list") and not items:
        raise RuntimeError("页面或接口解析结果为 0 条，可能是结构已变化")
    return items
