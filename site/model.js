// TCO/ROI-модель ЛЗ 3 для калькулятора на сайте. Формулы те же, что в finance/tco_model.py;
// совпадение чисел проверяет tests/test_site.py (через node).
(function (root) {
  const sum = (a) => a.reduce((x, y) => x + y, 0);

  // fin — блок finance из data.js; s — { methodistBefore, supportHours, costK, benefitK }
  function evaluate(fin, s) {
    const saved = (s.methodistBefore - fin.methodist_after) * fin.active_weeks + fin.other_hours;
    const bf = (Math.max(saved, 0) / fin.saved_hours) * s.benefitK;
    const r = fin.discount_rate;
    return fin.options.map((o) => {
      const costs = o.costs.map((c, t) => (c - o.support[t] + o.support[t] * (s.supportHours / fin.support_base)) * s.costK);
      const benefits = o.benefits.map((b) => b * bf);
      const tco = sum(costs);
      const ben = sum(benefits);
      const npv = costs.reduce((acc, c, t) => acc + (benefits[t] - c) / Math.pow(1 + r, t), 0);
      let payback = null;
      if (tco) {
        let cum = 0;
        for (let t = 0; t < costs.length; t++) {
          const prev = cum;
          const cf = benefits[t] - costs[t];
          cum += cf;
          if (t > 0 && cum >= 0) { payback = t - 1 + (-prev / cf); break; }
        }
      }
      return { name: o.name, costs, benefits, tco, benefit: ben, roi: tco ? (ben - tco) / tco : null, npv, payback };
    });
  }

  const api = { evaluate };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.PraktikaModel = api;
})(typeof window !== "undefined" ? window : globalThis);
