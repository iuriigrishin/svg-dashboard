/* ============ ОБРАЩЕНИЯ К БЭКЕНДУ ============
   Всё общение с Cloudflare Worker / Apps Script — только тут.
*/

async function fetchWithRetry(url, retries = 3, delay = 1000) {
  for (let i = 0; i < retries; i++) {
    try {
      const r = await fetch(url);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return await r.json();
    } catch (err) {
      console.warn(`Попытка ${i + 1} не удалась:`, err);
      if (i < retries - 1) await new Promise(res => setTimeout(res, delay * (i + 1)));
    }
  }
  return null;
}

async function fetchSheets() {
  const data = await fetchWithRetry(`${GAS_URL}?action=sheets`);
  return data || ['J1 vs J2'];
}

async function fetchSheetData(sheetName) {
  return await fetchWithRetry(`${GAS_URL}?sheet=${encodeURIComponent(sheetName)}`);
}
