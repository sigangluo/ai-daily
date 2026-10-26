(function () {
  const content = document.getElementById('content');
  const nav = document.getElementById('tier-nav');
  let DATA = null;
  let observer = null;

  const I18N = {
    zh: {
      title: '今天，AI 在发生什么。',
      copy: '资讯、开源项目与深度写作。按信源分区，中英文标题，点击直达原文。',
      updated: '近 30 天 · 更新于 ',
      sources: ' 个信源 · ',
      items: ' 条内容',
      itemShort: ' 条',
      allCategories: '全部分类',
      expand: function (n) { return '展开全部 ' + n + ' 条'; },
      collapse: '收起',
      noUpdates: '本月暂无更新',
      error: '暂不可用',
      stale: '显示上次内容',
      errorNotice: function (n, names) { return n + ' 个信源暂时不可用：' + names + '。其余内容已正常更新。'; },
      loadError: '内容载入失败',
      localHelp: '本地预览请在项目根目录运行 ',
      visit: '访问信源：',
      machine: '译',
      noMatch: '当前分类暂无内容',
      footer: '每日自动更新 · 内容版权归原信源所有，本站仅收录标题与链接',
      sourceList: '查看信源清单 ↗'
    },
    en: {
      title: 'What’s happening in AI today.',
      copy: 'AI news, open-source projects and deep reads, grouped by source. Original and Chinese titles with direct links.',
      updated: 'Last 30 days · Updated ',
      sources: ' sources · ',
      items: ' items',
      itemShort: '',
      allCategories: 'All categories',
      expand: function (n) { return 'Show all ' + n + ' items'; },
      collapse: 'Show less',
      noUpdates: 'No updates this month',
      error: 'Unavailable',
      stale: 'Previous content',
      errorNotice: function (n, names) { return n + ' sources are temporarily unavailable: ' + names + '. Everything else is up to date.'; },
      loadError: 'Could not load content',
      localHelp: 'For a local preview, run ',
      visit: 'Visit source: ',
      machine: 'MT',
      noMatch: 'No items in this category',
      footer: 'Updated daily · Rights belong to the original publishers. Only titles and links are indexed.',
      sourceList: 'View all sources ↗'
    }
  };

  const TIER_EN = {
    T1: ['Official', 'Model releases and official blogs'],
    T2: ['Media', 'Industry news and broader coverage'],
    T3: ['Community & Projects', 'Open source, new products and developer communities'],
    T4: ['Deep Reads', 'Low-frequency, high-quality writing']
  };
  const REGION_EN = { cn: 'China', intl: 'International' };

  function pickLanguage() {
    try {
      const saved = localStorage.getItem('ai-daily.lang');
      if (saved === 'zh' || saved === 'en') return saved;
    } catch (error) {}
    return /^zh/i.test(navigator.language || '') ? 'zh' : 'en';
  }

  let LANG = pickLanguage();

  function t(key, a, b) {
    const value = I18N[LANG][key];
    return typeof value === 'function' ? value(a, b) : value;
  }

  function node(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function safeUrl(value) {
    try {
      const url = new URL(value);
      return ['http:', 'https:'].includes(url.protocol) ? url.href : '#';
    } catch (error) {
      return '#';
    }
  }

  function domain(value) {
    try {
      return new URL(value).hostname.replace(/^www\./, '');
    } catch (error) {
      return LANG === 'zh' ? '信源' : 'Source';
    }
  }

  function itemTitle(item) {
    return LANG === 'zh' ? (item.title_zh || item.title) : item.title;
  }

  function itemUrl(item) {
    return LANG === 'zh' ? (item.url_zh || item.url) : item.url;
  }

  function sourceHomepage(source) {
    return LANG === 'zh' ? (source.homepage_zh || source.homepage || source.url) : (source.homepage || source.url);
  }

  function itemCategories(item) {
    return LANG === 'zh' ? (item.categories_zh || item.categories || []) : (item.categories || []);
  }

  function itemMeta(item) {
    return LANG === 'zh' ? (item.meta_zh || item.meta || []) : (item.meta || []);
  }

  function sourceCard(source) {
    const card = node('article', 'source-card');
    card.id = 'source-' + source.id;
    const header = node('header', 'source-header');
    header.appendChild(node('h3', '', source.name));
    const homepage = sourceHomepage(source);
    const homeLink = node('a', 'source-home', domain(homepage) + ' ↗');
    homeLink.href = safeUrl(homepage);
    homeLink.target = '_blank';
    homeLink.rel = 'noopener';
    homeLink.title = t('visit') + homepage;
    header.appendChild(homeLink);
    if (source.status === 'error') {
      const status = node('span', 'source-status', source.stale ? t('stale') : t('error'));
      status.title = source.error || t('error');
      header.appendChild(status);
    }
    const count = node('span', 'source-count', source.items.length + t('itemShort'));
    header.appendChild(count);
    card.appendChild(header);

    const categories = Array.from(new Set(source.items.flatMap(itemCategories))).sort(function (a, b) {
      return a.localeCompare(b, LANG === 'zh' ? 'zh-CN' : 'en');
    });
    let selected = '';
    if (categories.length) {
      const select = node('select', 'source-filter');
      select.setAttribute('aria-label', t('allCategories'));
      const all = node('option', '', t('allCategories'));
      all.value = '';
      select.appendChild(all);
      categories.forEach(function (category) {
        const option = node('option', '', category);
        option.value = category;
        select.appendChild(option);
      });
      select.addEventListener('change', function () {
        selected = select.value;
        drawList();
      });
      card.appendChild(select);
    }

    const list = node('ol', 'items');
    list.id = 'items-' + source.id;
    const expandButton = node('button', 'source-expand');
    expandButton.type = 'button';
    expandButton.setAttribute('aria-controls', list.id);

    function visibleItems() {
      return selected ? source.items.filter(function (item) { return itemCategories(item).includes(selected); }) : source.items;
    }

    function drawList() {
      const items = visibleItems();
      list.innerHTML = '';
      count.textContent = (selected ? items.length + '/' + source.items.length : items.length) + t('itemShort');
      items.forEach(function (item, index) {
        const row = node('li', 'item');
        if (index >= 6) row.hidden = true;
        const line = node('div', 'item-line');
        const link = node('a', 'item-title', itemTitle(item));
        link.href = safeUrl(itemUrl(item));
        link.target = '_blank';
        link.rel = 'noopener';
        const date = node('time', 'item-date', item.date.slice(5));
        date.dateTime = item.date;
        date.title = item.date;
        line.append(link, date);
        row.appendChild(line);
        if (item.description) row.appendChild(node('p', 'item-description', item.description));
        const categories = itemCategories(item);
        const meta = itemMeta(item);
        if (categories.length || meta.length || (LANG === 'zh' && item.title_zh_source === 'deepseek')) {
          const metaNode = node('div', 'item-meta');
          categories.forEach(function (value) { metaNode.appendChild(node('span', 'item-category', value)); });
          meta.forEach(function (value) { metaNode.appendChild(node('span', '', value)); });
          if (LANG === 'zh' && item.title_zh_source === 'deepseek') metaNode.appendChild(node('span', 'item-translation', t('machine')));
          row.appendChild(metaNode);
        }
        list.appendChild(row);
      });
      if (!items.length) list.appendChild(node('li', 'empty', t('noMatch')));
      expandButton.hidden = items.length <= 6;
      expandButton.textContent = t('expand', items.length);
      expandButton.setAttribute('aria-expanded', 'false');
    }

    expandButton.addEventListener('click', function () {
      const expanded = expandButton.getAttribute('aria-expanded') === 'true';
      Array.from(list.children).forEach(function (row, index) {
        if (index >= 6) row.hidden = expanded;
      });
      expandButton.setAttribute('aria-expanded', String(!expanded));
      expandButton.textContent = expanded ? t('expand', visibleItems().length) : t('collapse');
    });
    card.append(list, expandButton);
    drawList();
    return card;
  }

  function applyStatic() {
    document.documentElement.lang = LANG === 'zh' ? 'zh-CN' : 'en';
    document.title = LANG === 'zh' ? 'AI Daily — 按信源看 AI 每日动态' : 'AI Daily — AI news by source';
    document.getElementById('page-title').textContent = t('title');
    document.querySelector('.intro-copy').textContent = t('copy');
    document.getElementById('footer-text').textContent = t('footer');
    document.getElementById('sources-link').textContent = t('sourceList');
    document.querySelectorAll('.lang-switch button').forEach(function (button) {
      button.setAttribute('aria-pressed', String(button.dataset.lang === LANG));
    });
  }

  function render() {
    if (!DATA) return;
    applyStatic();
    nav.innerHTML = '';
    content.innerHTML = '';
    if (observer) observer.disconnect();

    const totalItems = DATA.sources.reduce(function (sum, source) { return sum + source.items.length; }, 0);
    const updated = new Intl.DateTimeFormat(LANG === 'zh' ? 'zh-CN' : 'en-US', {
      year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false
    }).format(new Date(DATA.generated_at));
    document.getElementById('update-meta').textContent = t('updated') + updated + ' · ' + DATA.sources.length + t('sources') + totalItems + t('items');

    const errors = DATA.sources.filter(function (source) { return source.status === 'error'; });
    const notice = document.getElementById('notice');
    notice.hidden = !errors.length;
    if (errors.length) {
      notice.textContent = t('errorNotice', errors.length, errors.map(function (source) { return source.name; }).join(LANG === 'zh' ? '、' : ', '));
    }

    DATA.tiers.forEach(function (tier) {
      const tierSources = DATA.sources.filter(function (source) { return source.tier === tier.id; });
      if (!tierSources.length) return;
      const count = tierSources.reduce(function (sum, source) { return sum + source.items.length; }, 0);
      const tierName = LANG === 'zh' ? tier.name : TIER_EN[tier.id][0];
      const tierDescription = LANG === 'zh' ? tier.description : TIER_EN[tier.id][1];
      const link = node('a', 'tier-link');
      link.href = '#' + tier.id;
      link.dataset.tier = tier.id;
      link.append(node('span', 'tier-code', tier.id), node('span', '', tierName));
      nav.appendChild(link);

      const section = node('section', 'tier');
      section.id = tier.id;
      const header = node('div', 'tier-header');
      header.append(node('span', 'tier-index', tier.id), node('h2', '', tierName),
        node('p', 'tier-description', tierDescription), node('span', 'tier-count', count + t('itemShort')));
      section.appendChild(header);

      DATA.regions.forEach(function (region) {
        const sources = tierSources.filter(function (source) { return source.region === region.id; });
        if (!sources.length) return;
        const regionSection = node('section', 'region');
        const regionName = LANG === 'zh' ? region.name : REGION_EN[region.id];
        const regionHeading = node('h3', 'region-heading', regionName);
        regionHeading.appendChild(node('span', 'region-count', sources.length + t('sources').replace(' · ', '')));
        const grid = node('div', 'source-grid');
        const activeSources = sources.filter(function (source) { return source.items.length > 0; });
        const emptySources = sources.filter(function (source) { return source.items.length === 0; });
        activeSources.forEach(function (source) { grid.appendChild(sourceCard(source)); });
        regionSection.append(regionHeading, grid);
        if (emptySources.length) {
          const empty = node('p', 'empty-sources');
          empty.appendChild(node('span', 'empty-sources-label', t('noUpdates')));
          empty.appendChild(node('span', '', emptySources.map(function (source) { return source.name; }).join(' · ')));
          regionSection.appendChild(empty);
        }
        section.appendChild(regionSection);
      });
      content.appendChild(section);
    });

    if ('IntersectionObserver' in window) {
      const links = Array.from(nav.querySelectorAll('.tier-link'));
      observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          links.forEach(function (link) { link.classList.toggle('active', link.dataset.tier === entry.target.id); });
        });
      }, { rootMargin: '-15% 0px -70% 0px' });
      document.querySelectorAll('.tier').forEach(function (section) { observer.observe(section); });
    }
  }

  document.querySelectorAll('.lang-switch button').forEach(function (button) {
    button.addEventListener('click', function () {
      if (button.dataset.lang === LANG) return;
      LANG = button.dataset.lang;
      try { localStorage.setItem('ai-daily.lang', LANG); } catch (error) {}
      render();
    });
  });

  fetch('data/latest.json', { cache: 'no-cache' })
    .then(function (response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.json();
    })
    .then(function (data) {
      DATA = data;
      render();
    })
    .catch(function (error) {
      applyStatic();
      document.getElementById('update-meta').textContent = t('loadError');
      const message = node('div', 'load-error', t('loadError') + '（' + error.message + '）');
      const help = node('p');
      help.textContent = t('localHelp');
      help.appendChild(node('code', '', 'python3 scripts/serve.py'));
      help.appendChild(document.createTextNode(LANG === 'zh' ? '，然后访问 http://localhost:8000。' : ', then open http://localhost:8000.'));
      message.appendChild(help);
      content.appendChild(message);
    });
})();
