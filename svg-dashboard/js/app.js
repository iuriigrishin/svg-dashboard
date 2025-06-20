const ENDPOINT = 'ВАШ_URL';
const REFRESH_MS = 10000;
const TABS = ['Вкладка 1', 'Вкладка 2'];

const nav = document.getElementById('tabs');
const panes = document.getElementById('panes');

TABS.forEach((name, i) => {
  const btn = document.createElement('button');
  btn.textContent = name;
  btn.dataset.idx = i;
  nav.append(btn);

  const pane = document.createElement('section');
  pane.className = 'pane';
  pane.id = `pane-${i}`;
  pane.innerHTML = `<svg id="svg-${i}-0"></svg><svg id="svg-${i}-1"></svg>`;
  panes.append(pane);
});

nav.addEventListener('click', e => {
  if (e.target.tagName !== 'BUTTON') return;
  nav.querySelectorAll('button').forEach(b => b.classList.toggle('active', b === e.target));
  panes.querySelectorAll('.pane').forEach(p => p.classList.toggle('active', p.id === `pane-${e.target.dataset.idx}`));
});
nav.querySelector('button').click();

async function fetchData() {
  const res = await fetch(ENDPOINT, { cache: 'no-cache' });
  return await res.json();
}

function draw(svg, data) {
  const w = svg.clientWidth, h = svg.clientHeight, pad = 30;
  const g = d3.select(svg).html('').append('g').attr('transform', `translate(${pad},${pad})`);
  const xs = d3.scaleLinear().domain(d3.extent(data, d => +d.x)).range([0, w - 2 * pad]);
  const ys = d3.scaleLinear().domain(d3.extent(data, d => +d.y)).range([h - 2 * pad, 0]);

  g.selectAll('circle')
    .data(data)
    .enter()
    .append('circle')
    .attr('cx', d => xs(+d.x))
    .attr('cy', d => ys(+d.y))
    .attr('r', 5);
}

async function refresh() {
  try {
    const data = await fetchData();
    TABS.forEach((_, i) => {
      draw(document.getElementById(`svg-${i}-0`), data);
      draw(document.getElementById(`svg-${i}-1`), data);
    });
  } catch (e) {
    console.error('Ошибка загрузки:', e);
  }
}
refresh();
setInterval(refresh, REFRESH_MS);
