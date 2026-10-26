(function () {
  const content = document.getElementById('content');
  const nav = document.getElementById('tier-nav');

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
      return '信源';
    }
  }

  function sourceCard(source) {
    const card = node('article', 'source-card');
    card.id = 'source-' + source.id;
    const header = node('header', 'source-header');
    header.appendChild(node('h3', '', source.name));
    const homepage = source.homepage || source.url;
    const homeLink = node('a', 'source-home', domain(homepage) + ' ↗');
    homeLink.href = safeUrl(homepage);
    homeLink.target = '_blank';
    homeLink.rel = 'noopener';
    homeLink.title = '访问信源：' + homepage;
    header.appendChild(homeLink);
    if (source.status === 'error') {
      const status = node('span', 'source-status', source.stale ? '显示上次内容' : '暂不可用');
      status.title = source.error || '信源暂时不可用';
      header.appendChild(status);
    }
    header.appendChild(node('span', 'source-count', source.items.length + ' 条'));
    card.appendChild(header);

    const list = node('ol', 'items');
    list.id = 'items-' + source.id;
    source.items.forEach(function (item, index) {
      const row = node('li', 'item');
      if (index >= 6) row.hidden = true;
      const line = node('div', 'item-line');
      const link = node('a', 'item-title', item.title);
      link.href = safeUrl(item.url);
      link.target = '_blank';
      link.rel = 'noopener';
      const date = node('time', 'item-date', item.date.slice(5));
      date.dateTime = item.date;
      date.title = item.date;
      line.append(link, date);
      row.appendChild(line);
      if (item.description) row.appendChild(node('p', 'item-description', item.description));
      if (item.meta && item.meta.length) {
        const meta = node('div', 'item-meta');
        item.meta.forEach(function (value) { meta.appendChild(node('span', '', value)); });
        row.appendChild(meta);
      }
      list.appendChild(row);
    });
    card.appendChild(list);
    if (source.items.length > 6) {
      const button = node('button', 'source-expand', '展开全部 ' + source.items.length + ' 条');
      button.type = 'button';
      button.setAttribute('aria-expanded', 'false');
      button.setAttribute('aria-controls', list.id);
      button.addEventListener('click', function () {
        const expanded = button.getAttribute('aria-expanded') === 'true';
        Array.from(list.children).forEach(function (row, index) {
          if (index >= 6) row.hidden = expanded;
        });
        button.setAttribute('aria-expanded', String(!expanded));
        button.textContent = expanded ? '展开全部 ' + source.items.length + ' 条' : '收起';
      });
      card.appendChild(button);
    }
    return card;
  }

  function render(data) {
    const totalItems = data.sources.reduce(function (sum, source) { return sum + source.items.length; }, 0);
    const updated = new Date(data.generated_at);
    document.getElementById('update-meta').textContent =
      '近 30 天 · 更新于 ' + new Intl.DateTimeFormat('zh-CN', {
        year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false
      }).format(updated) + ' · ' + data.sources.length + ' 个信源 · ' + totalItems + ' 条内容';

    const errors = data.sources.filter(function (source) { return source.status === 'error'; });
    if (errors.length) {
      const notice = document.getElementById('notice');
      notice.hidden = false;
      notice.textContent = errors.length + ' 个信源暂时不可用：' + errors.map(function (source) { return source.name; }).join('、') + '。其余内容已正常更新。';
    }

    data.tiers.forEach(function (tier) {
      const tierSources = data.sources.filter(function (source) { return source.tier === tier.id; });
      if (!tierSources.length) return;
      const count = tierSources.reduce(function (sum, source) { return sum + source.items.length; }, 0);
      const link = node('a', 'tier-link');
      link.href = '#' + tier.id;
      link.dataset.tier = tier.id;
      link.append(node('span', 'tier-code', tier.id), node('span', '', tier.name));
      nav.appendChild(link);

      const section = node('section', 'tier');
      section.id = tier.id;
      const header = node('div', 'tier-header');
      header.append(node('span', 'tier-index', tier.id), node('h2', '', tier.name),
        node('p', 'tier-description', tier.description), node('span', 'tier-count', count + ' 条'));
      section.appendChild(header);

      data.regions.forEach(function (region) {
        const sources = tierSources.filter(function (source) { return source.region === region.id; });
        if (!sources.length) return;
        const regionSection = node('section', 'region');
        const regionHeading = node('h3', 'region-heading', region.name);
        regionHeading.appendChild(node('span', 'region-count', sources.length + ' 个信源'));
        const grid = node('div', 'source-grid');
        const activeSources = sources.filter(function (source) { return source.items.length > 0; });
        const emptySources = sources.filter(function (source) { return source.items.length === 0; });
        activeSources.forEach(function (source) { grid.appendChild(sourceCard(source)); });
        regionSection.append(regionHeading, grid);
        if (emptySources.length) {
          const empty = node('p', 'empty-sources');
          empty.appendChild(node('span', 'empty-sources-label', '本月暂无更新'));
          empty.appendChild(node('span', '', emptySources.map(function (source) { return source.name; }).join(' · ')));
          regionSection.appendChild(empty);
        }
        section.appendChild(regionSection);
      });
      content.appendChild(section);
    });

    if ('IntersectionObserver' in window) {
      const links = Array.from(nav.querySelectorAll('.tier-link'));
      const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          links.forEach(function (link) { link.classList.toggle('active', link.dataset.tier === entry.target.id); });
        });
      }, { rootMargin: '-15% 0px -70% 0px' });
      document.querySelectorAll('.tier').forEach(function (section) { observer.observe(section); });
    }
  }

  fetch('data/latest.json', { cache: 'no-cache' })
    .then(function (response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.json();
    })
    .then(render)
    .catch(function (error) {
      document.getElementById('update-meta').textContent = '内容载入失败';
      const message = node('div', 'load-error', '无法加载每日内容（' + error.message + '）。');
      const help = node('p');
      help.textContent = '本地预览请在项目根目录运行 ';
      help.appendChild(node('code', '', 'python3 scripts/serve.py'));
      help.appendChild(document.createTextNode('，然后访问 http://localhost:8000。'));
      message.appendChild(help);
      content.appendChild(message);
    });
})();
