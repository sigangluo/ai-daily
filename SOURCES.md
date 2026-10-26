# AI 日报信源清单

> 最后更新：2026-10-26 · 一期接入 **39 个信源**；T5 论文暂缓接入
> 机器可读配置见 [sources.yaml](sources.yaml)

## 分层设计

| 层级 | 定位 | 作用 |
|---|---|---|
| **T1 官方一手** | 模型发布、官方博客 | 准确性最高，零噪音，全收 |
| **T2 聚合媒体** | 行业新闻 | 官方源之外的全景覆盖 |
| **T3 社区/项目** | 开源项目、新产品、技术圈热度 | "项目推荐"主要来自这一层 |
| **T4 深度写作** | 低频高质的个人写作 | 对冲快讯噪音 |
| **T5 论文** | 每日前沿论文 | 社区精选 + 原始流过滤 + 中文解读 |

---

## T1 · 官方一手（14）

### 国内（6）—— 厂商官网无 RSS，经 GitHub Releases 订阅模型发布

| 信源 | 订阅地址 | 说明 |
|---|---|---|
| DeepSeek | [releases.atom](https://github.com/deepseek-ai/DeepSeek-V3/releases.atom) | DeepSeek-V3 系列 |
| 通义 Qwen | [releases.atom](https://github.com/QwenLM/Qwen3/releases.atom) | 阿里 Qwen3 系列 |
| 智谱 GLM | [releases.atom](https://github.com/zai-org/GLM-4.5/releases.atom) | GLM 系列 |
| 月之暗面 Kimi | [releases.atom](https://github.com/MoonshotAI/Kimi-K2/releases.atom) | Kimi K2 系列 |
| MiniMax | [releases.atom](https://github.com/MiniMax-AI/MiniMax-M2/releases.atom) | M2 系列 |
| 阶跃星辰 | [releases.atom](https://github.com/stepfun-ai/Step3/releases.atom) | Step 系列 |

> 字节豆包、百度文心无开源发布渠道，其动态由 T2 国内媒体覆盖。

### 国外（8）

| 信源 | 订阅地址 | 接入方式 |
|---|---|---|
| OpenAI News | [RSS](https://openai.com/news/rss.xml) | RSS |
| Anthropic News | [anthropic.com/news](https://www.anthropic.com/news) | 无 RSS，抓新闻列表页 |
| Google DeepMind | [RSS](https://deepmind.google/blog/rss.xml) | RSS |
| Google Research | [RSS](https://research.google/blog/rss/) | RSS |
| Mistral AI | [RSS](https://mistral.ai/news/rss) | RSS |
| Hugging Face Blog | [RSS](https://huggingface.co/blog/feed.xml) | RSS |
| GitHub Blog · AI & ML | [RSS](https://github.blog/ai-and-ml/feed/) | RSS |
| NVIDIA Blog | [RSS](https://blogs.nvidia.com/feed/) | RSS |

## T2 · 聚合媒体（11）

### 国内（6）

| 信源 | 订阅地址 | 说明 |
|---|---|---|
| 量子位 | [RSS](https://www.qbitai.com/feed) | 国内 AI 新闻最快最全 |
| 机器之心 | [RSS](https://wechat2rss.xlab.app/feed/51e92aad2728acdd1fda7314be32b16639353001.xml) | 偏技术与论文解读 |
| 36氪 | [RSS](https://www.36kr.com/feed) | 商业、融资视角 |
| InfoQ 中文 | [RSS](https://www.infoq.cn/feed) | 工程实践视角 |
| 新智元 | [RSS](https://wechat2rss.xlab.app/feed/ede30346413ea70dbef5d485ea5cbb95cca446e7.xml) | 行业新闻+观点 |
| 夕小瑶科技说 | [RSS](https://wechat2rss.xlab.app/feed/a1cd365aa14ed7d64cabfc8aa086da40ecaba34d.xml) | AI 热点科普解读 |

### 国外（5）

| 信源 | 订阅地址 |
|---|---|
| TechCrunch AI | [RSS](https://techcrunch.com/category/artificial-intelligence/feed/) |
| The Verge AI | [RSS](https://www.theverge.com/rss/ai-artificial-intelligence/index.xml) |
| Ars Technica AI | [RSS](https://arstechnica.com/ai/feed/) |
| MIT Technology Review AI | [RSS](https://www.technologyreview.com/topic/artificial-intelligence/feed) |
| The Decoder | [RSS](https://the-decoder.com/feed/) |

## T3 · 社区/项目（7）

### 国内（4）

| 信源 | 订阅地址 | 说明 |
|---|---|---|
| HelloGitHub | [RSS](https://hellogithub.com/rss) | 开源项目推荐 |
| 开源中国 | [RSS](https://www.oschina.net/news/rss) | 开源资讯 |
| 小众软件 | [RSS](https://wechat2rss.xlab.app/feed/3261d5a75cfef238650a2cabd4bbf99669c2f334.xml) | 工具/软件推荐 |
| 掘金 AI 频道 | [API](https://api.juejin.cn/recommend_api/v1/article/recommend_cate_feed) | 掘金公开 API，免登录 |

### 国外（3）

| 信源 | 订阅地址 | 说明 |
|---|---|---|
| GitHub Trending | [github.com/trending](https://github.com/trending) | 直接抓网页 |
| Product Hunt | [RSS](https://www.producthunt.com/feed) | 新产品每日榜单，AI 工具浓度高 |
| Hacker News 首页 | [RSS](https://hnrss.org/frontpage) | 国际技术圈热点风向标 |

## T4 · 深度写作（7）

### 国内（2）

| 信源 | 订阅地址 | 说明 |
|---|---|---|
| 阮一峰·科技爱好者周刊 | [Atom](https://www.ruanyifeng.com/blog/atom.xml) | 每周五一期 |
| 傅盛 | [RSS](https://wechat2rss.xlab.app/feed/71257003d43d39b91ff9d38b6f3330c883dc8e0c.xml) | 企业家视角 AI 观点 |

### 国外（5）

| 信源 | 订阅地址 | 说明 |
|---|---|---|
| Simon Willison | [Atom](https://simonwillison.net/atom/everything/) | LLM 工程实践第一博客 |
| Lilian Weng | [RSS](https://lilianweng.github.io/index.xml) | 前 OpenAI，长篇技术综述 |
| Import AI | [RSS](https://importai.substack.com/feed) | Jack Clark 的 AI 周刊 |
| Latent Space | [RSS](https://www.latent.space/feed) | AI 工程社区 |
| Berkeley AI Research | [RSS](https://bair.berkeley.edu/blog/feed.xml) | 学术界视角 |

## T5 · 论文（5，暂缓接入）

以下信源保留在候选配置中，`enabled: false`。等 T1–T4 完成后，再单独讨论论文的筛选和展示方式。

| 信源 | 订阅地址 | 说明 |
|---|---|---|
| Hugging Face Daily Papers | [API](https://huggingface.co/api/daily_papers) | 社区投票精选，每天 5-15 篇，主力 |
| arXiv cs.CL（大模型/NLP） | [RSS](https://export.arxiv.org/rss/cs.CL) | 原始流，LLM 每天强过滤挑 3-5 篇 |
| arXiv cs.MA（多智能体/Agent） | [RSS](https://export.arxiv.org/rss/cs.MA) | 原始流，LLM 每天强过滤挑 3-5 篇 |
| PaperWeekly | [RSS](https://wechat2rss.xlab.app/feed/3be891c2f4e526629ab055a297cc2cd6c1f0a563.xml) | 论文中文解读 |
| 我爱计算机视觉 | [RSS](https://wechat2rss.xlab.app/feed/b81ffcfff1107b5265cd7e39de610dc7ca72caf4.xml) | CV 论文+代码中文解读 |

---

## 候选池（已验证可用，暂未启用）

- [arXiv cs.LG](https://export.arxiv.org/rss/cs.LG) / [cs.CV](https://export.arxiv.org/rss/cs.CV) —— 量太大，一期先不接
- [少数派](https://sspai.com/feed) —— 效率工具，AI 浓度不高
- [Anthropic Engineering](https://www.anthropic.com/engineering) —— 可并入 Anthropic 抓取
- [HN 人气独立博客 90 个](https://github.com/vigorX777/ai-daily-digest) —— T4 扩展池
- 未收录的公众号（歸藏、小互、Founder Park 等）—— 可向 [Wechat2RSS](https://github.com/ttttmr/Wechat2RSS) 申请收录

## 已知风险

1. **公众号依赖 Wechat2RSS 公共服务**：延迟 24h 内，第三方服务存在失效可能，核心信息不依赖它
2. **网页抓取和 API 源**（GitHub Trending、Anthropic、掘金）：页面结构或接口变更会导致失效，需要抓取失败告警
3. **同一事件多源报道**：为保持信源边界，一期只在信源内部按链接去重，不做跨源合并
4. **arXiv 原始流量大**：后续接入前必须先确定过滤方式，不能直接展示未经筛选的原始流
