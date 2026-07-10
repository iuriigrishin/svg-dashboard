/* ============ ПОКРАСКА КЛЕТОК КАРТЫ ============
   Единственное место, где решается, каким цветом залить клетку задачи.
   Правки цветовой логики (условного форматирования дашборда) — только тут,
   остальной код (app.js) ничего не знает про конкретные цвета.
*/

const TASK_COUNT = 43;

function colorForSquare(dat, n) {
  const done1 = dat[`square_${n}`];
  const done2 = dat[`square_${n}_team2`];
  const zero1 = dat[`square_${n}_only0`];
  const zero2 = dat[`square_${n}_team2_only0`];

  if (done1 && done2) return 'gold';
  if (done1)          return 'green';
  if (done2)          return 'orange';
  if (zero1 && zero2) return 'gray';
  return '';
}
