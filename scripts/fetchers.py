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


def request(url, body=None):
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
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
            self.article = {"links": [], "date": ""}
        elif self.article is not None and tag == "a":
            self.anchor = {"url": clean_url(attrs.get("href", ""), self.base_url), "heading": [], "plain": []}
        elif self.anchor is not None and tag in ("h1", "h2", "h3"):
            self.heading_depth += 1
        elif self.article is not None and tag == "time":
            self.in_time = True
            if attrs.get("datetime"):
                self.article["date"] = date_text(attrs["datetime"])

    def handle_endtag(self, tag):
        if tag == "article" and self.article is not None:
            for link in self.article["links"]:
                title = clean_text(" ".join(link["heading"]))
                if title and link["url"]:
                    self.articles.append({"title": title, "url": link["url"], "date": self.article["date"]})
                    break
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
        if self.anchor is not None:
            self.anchor["plain"].append(data)
            if self.heading_depth:
                self.anchor["heading"].append(data)
        if self.in_time and self.article is not None and not self.article["date"]:
            self.article["date"] = date_text(data)


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
    if source["id"] == "juejin-ai":
        raw = request(source["url"], {"id_type": 2, "sort_type": 300, "cate_id": "6809637773935378440", "limit": 30, "cursor": "0"})
        return parse_juejin(raw)
    raw = request(source["url"])
    if source["id"] == "anthropic-news":
        return parse_anthropic(raw)
    if source["id"] == "github-trending":
        return parse_trending(raw)
    if source["type"] in ("rss", "atom", "wechat"):
        return parse_feed(raw, source)
    raise RuntimeError(f"暂不支持的信源类型: {source['type']}")
