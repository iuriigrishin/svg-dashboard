/* ============ SETTINGS ============
   Единственное место с адресом бэкенда. После provision.py адрес
   Cloudflare Worker подставляется сюда автоматически — руками
   трогать не нужно, если только не меняете инфраструктуру вручную.
*/

const GAS_URL = 'https://blue-shape-5fbb.iurkagrishin187.workers.dev';
const POLL_INTERVAL = 10000;   // ms — как часто опрашивать Worker
const PAD           = 12;      // px — зазор вокруг SVG-карты
