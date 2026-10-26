# AI Daily

按层级和信源浏览 AI 资讯、开源项目与深度写作。保留原文语言，不翻译、不生成摘要，点击标题直达原文。

**在线阅读：<https://sigangluo.github.io/ai-daily/>**

## 内容组织

- **T1 · 官方一手**：模型发布、官方博客
- **T2 · 聚合媒体**：国内外行业新闻
- **T3 · 社区与项目**：GitHub Trending、掘金 AI、Product Hunt、Hacker News 等
- **T4 · 深度写作**：个人博客与低频技术写作

一期接入 **42 个信源**，按「层级 → 国内/国外 → 信源」展示。T5 论文信源保留在配置中，但暂未启用，筛选与展示方式另行讨论。

完整清单和接入方式见 [SOURCES.md](SOURCES.md)，程序只读取 [sources.yaml](sources.yaml) 中 `enabled: true` 的信源。

## 每日更新

GitHub Actions 每天约北京时间 **07:17** 抓取信源，更新 `site/data/latest.json`，提交数据变化并部署到 GitHub Pages，也可以在 Actions 页面手动触发。

- 首次使用 `--bootstrap` 回填最近 **30 天**；之后每日只处理最近 **1 天**的新内容
- 每日结果与历史按原文链接合并、去重、按日期排序，持续保留滚动 30 天，不再按信源截断为 5–10 条
- 每个信源独立抓取，有限并发、超时和重试；单个信源失败不影响其他信源
- 页面默认每个信源展示 6 条，可展开全部；本月无更新的信源合并为紧凑提示，不用旧文章填充
- 网站是原生 HTML/CSS/JS 静态站，无前端依赖和构建步骤

## 本地运行

需要 Python 3.9+。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/update.py --bootstrap
.venv/bin/python scripts/serve.py
```

打开 <http://localhost:8000>。之后每日增量更新：

```bash
.venv/bin/python scripts/update.py
```

只更新个别信源，或单独回填一个新信源：

```bash
.venv/bin/python scripts/update.py --only github-trending,anthropic-news,juejin-ai
.venv/bin/python scripts/update.py --only qwen-research --bootstrap
```

## 目录结构

```text
.github/workflows/daily.yml  每日抓取、提交和 Pages 部署
scripts/fetchers.py         RSS/Atom、网页与公开 API 解析器
scripts/update.py           信源校验、抓取、容错与数据生成
scripts/serve.py            本地静态预览
site/index.html             页面结构
site/assets/                样式与前端渲染
site/data/latest.json       自动生成的当前内容快照
sources.yaml                信源配置（程序读取）
SOURCES.md                  信源说明（人工阅读）
```

## 新增或调整信源

编辑 `sources.yaml`，为信源设置唯一的 `id`，并填写 `name`、`tier`、`region`、`type`、`url` 和 `enabled`。RSS、Atom 和 Wechat2RSS 使用通用解析器；网页或特殊 API 需要在 `scripts/fetchers.py` 中增加适配。调整后运行完整 `--bootstrap` 回填，并同步维护 `SOURCES.md`；只新增一个信源时可用 `--only <id> --bootstrap`。

## 已知限制

- 公众号通过 [Wechat2RSS](https://github.com/ttttmr/Wechat2RSS) 公共服务接入，可能有延迟或服务波动
- GitHub Trending、Anthropic、掘金及国内厂商官网依赖网页结构或公开接口，结构变化时需要更新解析器
- DeepSeek 官网 News 有 AWS WAF；DeepSeek、StepFun、Import AI 通过 Jina Reader 读取公开内容并禁用缓存，DeepMind RSS 失败时也用它兜底，条目仍跳转官方原文
- 低频信源可能近 30 天没有新内容，这是正常状态，不使用旧文章填充
- 本站只保存标题、链接和少量元数据，文章版权属于原信源

## License

代码采用 [MIT License](LICENSE)。
