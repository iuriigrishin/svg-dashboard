/* ============ ИНИЦИАЛИЗАЦИЯ И ОРКЕСТРАЦИЯ ДАШБОРДА ============
   DOM, состояние, селектор листов, polling. Цвета — в paint.js,
   сетевые запросы — в api.js, адрес бэкенда — в config.js.
*/

const side = {
  left: {
    box: document.getElementById('left-map'),
    sel: document.getElementById('left-selector'),
    freshEl: document.getElementById('left-freshness'),
    sheet: null, state: {}
  },
  right: {
    box: document.getElementById('right-map'),
    sel: document.getElementById('right-selector'),
    freshEl: document.getElementById('right-freshness'),
    sheet: null, state: {}
  }
};

(async function init() {
  Object.values(side).forEach(ctx => {
    ctx.box.appendChild(
      document.getElementById('svg-template').content.cloneNode(true)
    );
    cropSvgToPaths(ctx.box.querySelector('svg'));
    ctx.scoreEl = ctx.box.parentElement.querySelector('.scoreboard');
  });

  const sheets = await fetchSheets();
  buildSelector(side.left, sheets);
  buildSelector(side.right, sheets);

  side.left.sheet = sheets[0];
  side.right.sheet = sheets[1] || sheets[0];

  startPolling(side.left);
  startPolling(side.right);
})();

function cropSvgToPaths(svg) {
  const paths = svg.querySelectorAll('path');
  if (!paths.length) return;

  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  paths.forEach(p => {
    const b = p.getBBox();
    minX = Math.min(minX, b.x);
    minY = Math.min(minY, b.y);
    maxX = Math.max(maxX, b.x + b.width);
    maxY = Math.max(maxY, b.y + b.height);
  });

  svg.setAttribute('viewBox', `${minX - PAD} ${minY - PAD} ${maxX - minX + PAD * 2} ${maxY - minY + PAD * 2}`);
  svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
}

function buildSelector(ctx, sheetNames) {
  const btn = ctx.sel.querySelector('.sel-btn');
  const list = ctx.sel.querySelector('.sel-list');

  btn.textContent = sheetNames[0] + ' ▼';

  btn.onclick = () => {
    list.style.display = (list.style.display === 'block') ? 'none' : 'block';
  };

  sheetNames.forEach(name => {
    const it = document.createElement('div');
    it.className = 'item';
    it.textContent = name;
    it.onclick = () => {
      ctx.sheet = name;
      btn.textContent = name + ' ▼';
      list.style.display = 'none';
      refresh(ctx, true);
    };
    list.appendChild(it);
  });

  document.addEventListener('click', e => {
    if (!ctx.sel.contains(e.target)) list.style.display = 'none';
  });
}

function startPolling(ctx) {
  refresh(ctx, true);
  setInterval(() => refresh(ctx, false), POLL_INTERVAL);
}

async function refresh(ctx, force) {
  if (!ctx.sheet) return;
  try {
    const dat = await fetchSheetData(ctx.sheet);
    if (!dat) return;

    for (let n = 1; n <= TASK_COUNT; n++) {
      const path = ctx.box.querySelector(`#path-${n}`);
      if (!path) continue;
      path.style.fill = colorForSquare(dat, n);
    }

    if (ctx.scoreEl) {
      ctx.scoreEl.querySelector('.team1').textContent = dat.team1Name || '';
      ctx.scoreEl.querySelector('.score1').textContent = dat.team1Score || '';
      ctx.scoreEl.querySelector('.team2').textContent = dat.team2Name || '';
      ctx.scoreEl.querySelector('.score2').textContent = dat.team2Score || '';
    }

    if (ctx.freshEl) {
      const now = new Date();
      const min = now.getMinutes().toString().padStart(2, '0');
      const sec = now.getSeconds().toString().padStart(2, '0');
      ctx.freshEl.textContent = `Обновлено в ${min}:${sec}`;
    }
  } catch (err) {
    console.error('refresh:', err);
  }
}
