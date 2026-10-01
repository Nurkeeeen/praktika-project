/* Сайт-портфолио проекта «Практика». Данные — window.SITE_DATA из data.js (scripts/build_site.py). */
(function () {
  "use strict";
  const D = window.SITE_DATA;
  const $ = (sel, root = document) => root.querySelector(sel);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const nf = new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 });
  const money = (x) => nf.format(Math.round(x)) + " ₸";
  const pct = (x) => (x === null || x === undefined ? "—" : (x > 0 ? "+" : "") + Math.round(x * 100) + " %");
  const years = (x) => (x === null || x === undefined ? "не окупается" : x.toFixed(1).replace(".", ",") + " г.");
  const repoUrl = "https://github.com/" + D.meta.repo;

  const RELEASE = { skeleton: "Ходячий скелет", mvp: "MVP (релиз 1)", r2: "Релиз 2", later: "Потом" };
  const STATUS = {
    submitted: "Подана", forwarded: "Передана работодателю", interview: "Собеседование",
    accepted: "Принят(а)", rejected: "Отказ", withdrawn: "Отозвана",
  };
  const lab = (id) => D.labs.find((l) => l.id === id);
  const SHORT = { "В0": "В0 · Ничего не делать", "В1": "В1 · Битрикс24", "В2": "В2 · Windows + SQL Server",
    "В3": "В3 · Открытый стек, подрядчик", "В3-С": "В3-С · Открытый стек, своя команда" };
  const short = (name) => SHORT[name.split(".")[0]] || name;

  /* ---------------- общие компоненты ---------------- */
  function tiles(items) {
    return `<div class="grid tiles">${items.map((t) => `
      <div class="card tile"><div class="label">${esc(t.label)}</div>
      <div class="value">${esc(t.value)}</div>${t.hint ? `<div class="hint">${esc(t.hint)}</div>` : ""}</div>`).join("")}</div>`;
  }

  function table(cols, rows, opts = {}) {
    const head = cols.map((c) => `<th class="${c.num ? "num" : ""}">${esc(c.label)}</th>`).join("");
    const body = rows.map((r) => `<tr class="${opts.rowClass ? opts.rowClass(r) : ""}">${cols.map((c) => {
      const raw = typeof c.get === "function" ? c.get(r) : r[c.key];
      const cls = [c.num ? "num" : "", c.cls ? c.cls(r) : ""].join(" ").trim();
      return `<td class="${cls}">${c.html ? raw : esc(raw)}</td>`;
    }).join("")}</tr>`).join("");
    return `<div class="table-wrap ${opts.scroll ? "table-scroll" : ""}"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
  }

  function report(id) {
    const l = lab(id);
    return `<details class="report"><summary>Полный текст отчёта<a class="dl" href="${esc(l.file)}" download>Скачать .docx ↓</a></summary>
      <div class="doc">${l.html}</div></details>`;
  }

  function header(id, eyebrow, title, lead) {
    return `<div class="eyebrow">${esc(eyebrow)}</div><h2>${esc(title)}</h2>${lead ? `<p class="lead">${lead}</p>` : ""}`;
  }

  /* ---------------- подсказка у графиков ---------------- */
  const tip = $("#tooltip");
  function bindTip(el) {
    el.addEventListener("mousemove", (e) => {
      const t = e.target.closest("[data-tip]");
      if (!t) { tip.classList.remove("show"); return; }
      tip.innerHTML = t.dataset.tip;
      tip.style.left = Math.min(e.clientX + 14, innerWidth - 300) + "px";
      tip.style.top = e.clientY + 14 + "px";
      tip.classList.add("show");
    });
    el.addEventListener("mouseleave", () => tip.classList.remove("show"));
  }

  /* Горизонтальные столбики. items: [{label, value, tip}]; diverging — отрицательные влево от нуля. */
  function hbar(items, { format = (v) => nf.format(v), diverging = false, labelW = 300, W = 760, valueCol = false } = {}) {
    const rowH = 30, barH = 16, top = 6;
    const padR = valueCol ? 120 : 110;
    const H = top + items.length * rowH + 6;
    const vals = items.map((i) => i.value);
    const min = diverging ? Math.min(0, ...vals) : 0;
    const max = Math.max(0, ...vals);
    const span = max - min || 1;
    const plotW = W - labelW - padR;
    const x = (v) => labelW + ((v - min) / span) * plotW;
    const x0 = x(0);
    const r = 4;
    const parts = [`<line class="axis" x1="${x0}" x2="${x0}" y1="0" y2="${H}"/>`];
    items.forEach((it, i) => {
      const y = top + i * rowH + (rowH - barH) / 2;
      const xv = x(it.value);
      const w = Math.abs(xv - x0);
      const neg = it.value < 0;
      const cls = diverging ? (neg ? "neg" : "pos") : "";
      // скругление только на конце столбика, у базовой линии — прямой угол
      const rr = Math.min(r, w / 2, barH / 2);
      const d = w < 0.5 ? "" : neg
        ? `M${x0},${y} H${xv + rr} Q${xv},${y} ${xv},${y + rr} V${y + barH - rr} Q${xv},${y + barH} ${xv + rr},${y + barH} H${x0} Z`
        : `M${x0},${y} H${xv - rr} Q${xv},${y} ${xv},${y + rr} V${y + barH - rr} Q${xv},${y + barH} ${xv - rr},${y + barH} H${x0} Z`;
      const label = it.label.length > 44 ? it.label.slice(0, 42) + "…" : it.label;
      const tipHtml = esc(it.tip || `${it.label}: ${format(it.value)}`);
      parts.push(`<g data-tip="${tipHtml}">
        <rect class="hit" x="0" y="${top + i * rowH}" width="${W}" height="${rowH}"/>
        <text x="${labelW - 10}" y="${y + barH / 2 + 4}" text-anchor="end">${esc(label)}</text>
        ${d ? `<path class="bar ${cls}" d="${d}"/>` : ""}
        ${valueCol
          ? `<text class="val" x="${W}" y="${y + barH / 2 + 4}" text-anchor="end">${esc(format(it.value))}</text>`
          : `<text class="val" x="${neg ? xv - 6 : xv + 6}" y="${y + barH / 2 + 4}" text-anchor="${neg ? "end" : "start"}">${esc(format(it.value))}</text>`}
      </g>`);
    });
    return `<div class="chart"><svg viewBox="0 0 ${W} ${H}" role="img">${parts.join("")}</svg></div>`;
  }

  /* ---------------- Обзор ---------------- */
  function renderOverview() {
    const fin = D.finance.options;
    const rec = fin[fin.length - 1];
    const done = D.checklist.filter((c) => c.status === "done").length;
    const stories = D.backlog.stories;
    $("#overview").innerHTML = `
      <div class="card hero">
        <div>
          <div class="eyebrow">Сквозной проект курса «Управление IT-проектами» · осень 2026</div>
          <h1>«Практика»</h1>
          <p>Система приёма и маршрутизации заявок студентов на практику и вакансий от работодателей-партнёров
          карьерного центра университета. Здесь собрана вся работа: лабораторные, бизнес-кейс, требования,
          базы студентов и вакансий и работающий прототип.</p>
          <div class="actions">
            <a class="btn primary" href="#lz4">Смотреть требования</a>
            <a class="btn" href="${repoUrl}" target="_blank" rel="noopener">Репозиторий</a>
            <a class="btn" href="${repoUrl}/issues" target="_blank" rel="noopener">Бэклог в Issues</a>
          </div>
        </div>
        <div class="team">
          <div class="eyebrow">Команда</div>
          ${D.meta.team.map((p) => `<div class="person"><div class="avatar">${esc(p.name[0])}</div>
            <div><b>${esc(p.name)}</b><span>${esc(p.role)}</span></div></div>`).join("")}
          <div class="eyebrow" style="margin-top:8px">Модель поставки</div>
          <div>Hybrid: вехи по неделям курса, внутри — итерации с демо заказчику раз в 2–3 недели</div>
        </div>
      </div>
      <div style="height:16px"></div>
      ${tiles([
        { label: "Лабораторных сдано", value: `${D.labs.length} из 15`, hint: `артефактов портфолио готово: ${done}` },
        { label: "Демо-база", value: `${D.db.students.length} / ${D.db.vacancies.length}`, hint: "студентов / вакансий (данные вымышлены)" },
        { label: "Бэклог", value: `${stories.length} историй`, hint: `${stories.reduce((a, s) => a + s.points, 0)} Story Points, ${D.nfr.length} НФТ` },
        { label: "NPV рекомендованного варианта", value: money(rec.npv), hint: "открытый стек силами команды, 3 года" },
      ])}
      <div class="grid two">
        <div class="card"><h3 class="sub" style="margin-top:0">Прогресс по курсу</h3>
          <ul class="timeline">${D.checklist.map((c) => `<li><span class="wk">Нед. ${esc(c.week)}</span>
            <span class="art">${esc(c.artifact)}${c.note ? `<small>${esc(c.note)}</small>` : ""}</span>
            <span class="status ${c.status}">${{ done: "Готово", progress: "В работе", todo: "Впереди" }[c.status]}</span></li>`).join("")}</ul>
        </div>
        <div class="card html-block">${D.projectCard}</div>
      </div>`;
  }

  /* ---------------- ЛЗ 1 ---------------- */
  function renderLz1() {
    const req = D.lz1.requirements.map((r) => ({ ...r, count: +r.count }));
    $("#lz1").innerHTML = header("lz1", "Неделя 1", "Реверс-инжиниринг рынка труда и разбор провала",
      "10 вакансий PM-ролей в Казахстане с hh.kz разобраны на требования. По частоте требований составлена карта компетенций и план закрытия пробелов. Разобран провал Knight Capital: убыток более $460 млн за 45 минут из-за ручного деплоя.") +
      tiles([
        { label: "Вакансий в выборке", value: D.lz1.vacancies.length, hint: "hh.kz, 10.09.2026" },
        { label: "Требований выделено", value: req.length, hint: "после объединения формулировок" },
        { label: "Самое частое", value: "80 %", hint: "опыт от 1 года и коммуникация с заказчиком" },
        { label: "Сертификаты PMP/PSM", value: "20 %", hint: "рынок ценит поведение, а не бумагу" },
      ]) +
      `<div class="card"><h3 class="sub" style="margin-top:0">Как часто требование встречается в 10 вакансиях</h3>
        ${hbar(req.map((r) => ({ label: r.requirement, value: r.count, tip: `${r.requirement}<br>${r.count} из 10 вакансий · ${r.group}` })),
          { format: (v) => v + " из 10" })}
      </div>
      <h3 class="sub">Выборка вакансий</h3>
      ${table([
        { label: "№", key: "id" }, { label: "Роль", key: "title" }, { label: "Работодатель", key: "employer" },
        { label: "Город", key: "city" },
        { label: "Ссылка", html: true, get: (r) => `<a href="${esc(r.url)}" target="_blank" rel="noopener">hh.kz ↗</a>` },
      ], D.lz1.vacancies)}
      ${report("lz1")}`;
  }

  /* ---------------- ЛЗ 2 ---------------- */
  function renderLz2() {
    const cases = [
      ["(а) Госорган: документооборот по тендеру", "Predictive", "ТЗ зафиксировано тендером, цена ошибки и регуляторность высокие"],
      ["(б) Стартап: непроверенная гипотеза", "Adaptive", "максимальная неопределённость, откат дешёвый"],
      ["(в) Банк: монолит → облако", "Hybrid", "compliance-гейты снаружи, миграция по частям внутри"],
      ["Наш проект «Практика»", "Hybrid", "вехи — недели курса; заказчик доступен раз в 2–3 недели"],
    ];
    $("#lz2").innerHTML = header("lz2", "Неделя 2", "Выбор модели поставки и рабочее пространство",
      "Три кейса сравнены по шести критериям: неопределённость, цена ошибки, регуляторность, зрелость заказчика, распределённость команды, тип контракта. Для своего проекта решение оформлено в ADR-001, рабочее пространство развёрнуто на GitHub.") +
      `<div class="grid tiles">${cases.map(([c, mdl, why], i) => `<div class="card tile" ${i === 3 ? 'style="border-color:var(--accent)"' : ""}>
        <div class="label">${esc(c)}</div><div class="value">${esc(mdl)}</div><div class="hint">${esc(why)}</div></div>`).join("")}</div>
      <div class="card html-block">${D.adr.find((a) => a.id === "0001")?.html || ""}</div>
      ${report("lz2")}`;
  }

  /* ---------------- ЛЗ 3 ---------------- */
  const calcState = { methodistBefore: D.finance.methodist_before, supportHours: D.finance.support_base, costK: 1, benefitK: 1 };

  function renderLz3() {
    const F = D.finance;
    const rec = F.options[F.options.length - 1];
    const sliders = [
      ["methodistBefore", "Методист тратит на заявки сейчас", 1, 6, 0.5, (v) => v.toFixed(1).replace(".", ",") + " ч/нед", "Допущение A3; после внедрения — 1 ч/нед"],
      ["supportHours", "Поддержка своей системы", 0, 12, 1, (v) => v + " ч/мес", "Допущение A10 (ИТ-отдел)"],
      ["costK", "Множитель затрат", 0.7, 1.6, 0.05, (v) => "× " + v.toFixed(2).replace(".", ","), "1,30 — сценарий «затраты +30 %»"],
      ["benefitK", "Доля реализованного эффекта", 0.3, 1.5, 0.05, (v) => Math.round(v * 100) + " %", "50 % — сценарий «эффект вдвое меньше»"],
    ];
    $("#lz3").innerHTML = header("lz3", "Неделя 3", "Бизнес-кейс, финансовая модель и устав",
      "Пять вариантов решения сравнены по TCO, ROI и NPV на 3 года. Цены взяты из 8 открытых источников, допущения вынесены отдельным списком. Ниже калькулятор на той же модели, что и Excel-файл: двигайте допущения и смотрите, какой вариант остаётся выгодным.") +
      tiles([
        { label: "Годовой эффект", value: money(F.annual_benefit), hint: `${Math.round(F.saved_hours)} ч времени персонала в год` },
        { label: "Рекомендация", value: "В3-С", hint: "открытый стек силами студенческой команды" },
        { label: "NPV рекомендации", value: money(rec.npv), hint: `ROI ${pct(rec.roi)}, окупаемость ${years(rec.payback)}` },
        { label: "Лицензии Windows + SQL Server", value: money(F.licenses), hint: "≈ 10 годовых эффектов — поэтому открытый стек" },
      ]) +
      `<div class="card"><div class="calc">
        <div>
          <h3 class="sub" style="margin-top:0">Допущения</h3>
          ${sliders.map(([k, label, mn, mx, st, fmt, hint]) => `<div class="slider">
            <label for="s-${k}">${esc(label)} <output id="o-${k}"></output></label>
            <input type="range" id="s-${k}" min="${mn}" max="${mx}" step="${st}" value="${calcState[k]}">
            <small>${esc(hint)}</small></div>`).join("")}
          <div class="toolbar">${F.scenarios.map((s, i) => `<button class="chip" type="button" data-scn="${i}">${esc(s.name)}</button>`).join("")}</div>
          <div class="verdict" id="verdict"></div>
        </div>
        <div>
          <h3 class="sub" style="margin-top:0">NPV за 3 года по вариантам (ставка 16,25 %)</h3>
          <div id="npv-chart"></div>
          <div class="legend"><span><i style="background:var(--pos)"></i>окупается</span><span><i style="background:var(--neg)"></i>убыточен</span></div>
          <div id="calc-table" style="margin-top:14px"></div>
        </div>
      </div></div>
      <details class="report"><summary>Источники цен и допущения модели</summary><div class="doc">
        <h4>Источники (дата обращения 24.09.2026)</h4><ul>${Object.entries(F.sources).map(([k, v]) => `<li><b>${k}</b> ${esc(v)}</li>`).join("")}</ul>
        <h4>Допущения</h4><ul>${Object.entries(F.assumptions).map(([k, v]) => `<li><b>${k}</b> ${esc(v)}</li>`).join("")}</ul>
      </div></details>
      <p style="margin-top:12px"><a class="btn" href="files/tco_model.xlsx" download>Скачать Excel-модель ↓</a></p>
      ${report("lz3")}`;

    const fmtOf = Object.fromEntries(sliders.map(([k, , , , , fmt]) => [k, fmt]));
    const update = () => {
      for (const k in fmtOf) $("#o-" + k).textContent = fmtOf[k](calcState[k]);
      const res = window.PraktikaModel.evaluate(F, calcState);
      const best = res.slice(1).reduce((a, b) => (b.npv > a.npv ? b : a));
      $("#npv-chart").innerHTML = hbar(res.slice(1).map((o) => ({
        label: short(o.name), value: o.npv,
        tip: `${o.name}<br>NPV ${money(o.npv)} · ROI ${pct(o.roi)} · TCO ${money(o.tco)}`,
      })), { format: money, diverging: true, labelW: 210, W: 600, valueCol: true });
      $("#calc-table").innerHTML = table([
        { label: "Вариант", html: true, get: (o) => `<span title="${esc(o.name)}">${esc(short(o.name))}</span>` },
        { label: "TCO", num: true, get: (o) => money(o.tco) },
        { label: "Выгода", num: true, get: (o) => money(o.benefit) },
        { label: "ROI", num: true, get: (o) => pct(o.roi), cls: (o) => (o.roi < 0 ? "neg" : "") },
        { label: "NPV", num: true, get: (o) => money(o.npv), cls: (o) => (o.npv < 0 ? "neg" : "") },
        { label: "Окупаемость", num: true, get: (o) => (o.tco ? years(o.payback) : "—") },
      ], res, { rowClass: (o) => (o === best && best.npv > 0 ? "highlight" : "") });
      $("#verdict").innerHTML = best.npv > 0
        ? `<b>Выгоднее всего: ${esc(short(best.name))}</b>NPV ${money(best.npv)}, окупаемость ${years(best.payback)}`
        : `<b>Ни один вариант не окупается</b>При таких допущениях рационально «ничего не делать» (В0) — это и есть условие go / no-go из бизнес-кейса.`;
    };
    for (const k in fmtOf) {
      $("#s-" + k).addEventListener("input", (e) => { calcState[k] = +e.target.value; update(); });
    }
    $("#lz3").querySelectorAll("[data-scn]").forEach((b) => b.addEventListener("click", () => {
      const s = F.scenarios[+b.dataset.scn];
      Object.assign(calcState, { methodistBefore: F.methodist_before, supportHours: F.support_base, costK: s.ck, benefitK: s.bk });
      for (const k in fmtOf) $("#s-" + k).value = calcState[k];
      update();
    }));
    bindTip($("#npv-chart"));
    update();
  }

  /* ---------------- ЛЗ 4 ---------------- */
  function renderLz4() {
    const B = D.backlog;
    const S = B.stories;
    const sp = (rel) => S.filter((s) => rel.includes(s.release)).reduce((a, s) => a + s.points, 0);
    $("#lz4").innerHTML = header("lz4", "Неделя 4", "Стейкхолдеры, требования и product discovery",
      "Матрица стейкхолдеров (включая скрытых: ИТ-отдел, юрист по ПДн, ИБ), план коммуникаций, сценарии интервью, story map с границей MVP, бэклог из 20 историй с критериями Given–When–Then и 18 измеримых нефункциональных требований.") +
      tiles([
        { label: "Историй в бэклоге", value: S.length, hint: `${sp(["skeleton", "mvp", "r2", "later"])} SP всего` },
        { label: "MVP к февралю 2027", value: sp(["skeleton", "mvp"]) + " SP", hint: `из них ходячий скелет — ${sp(["skeleton"])} SP` },
        { label: "Нефункциональных требований", value: D.nfr.length, hint: `${D.nfr.filter((n) => n.auto).length} уже проверяются автотестами` },
        { label: "Эпиков", value: Object.keys(B.epics).length, hint: "от каталога вакансий до аналитики" },
      ]) +
      `<figure class="card figure"><a href="assets/story-map.png" target="_blank" rel="noopener"><img src="assets/story-map.png" alt="Story map проекта: семь шагов пути пользователя, истории по релизам" loading="lazy"></a>
        <figcaption>Story map: сверху — путь пользователя, ниже — истории по релизам; красная линия — граница MVP. Нажмите, чтобы открыть крупно.</figcaption></figure>
      <h3 class="sub">Бэклог</h3>
      <div class="toolbar" id="bl-tools">
        <input class="search" id="bl-q" type="search" placeholder="Поиск по историям…" aria-label="Поиск по историям">
        <select class="search" id="bl-epic" aria-label="Эпик"><option value="">Все эпики</option>
          ${Object.entries(B.epics).map(([k, v]) => `<option value="${k}">${k} · ${esc(v)}</option>`).join("")}</select>
        ${["skeleton", "mvp", "r2"].map((r) => `<button class="chip" type="button" data-rel="${r}" aria-pressed="false">${RELEASE[r]}</button>`).join("")}
        <span class="count" id="bl-count"></span>
      </div>
      <div id="bl-table"></div>
      <h3 class="sub">Нефункциональные требования</h3>
      ${table([
        { label: "ID", get: (r) => r.id + (r.auto ? " ✔" : ""), cls: () => "nowrap" }, { label: "Категория", key: "category" },
        { label: "Требование", key: "requirement" }, { label: "Метрика / порог", key: "metric" },
        { label: "Как проверяем", key: "verify" },
      ], D.nfr, { scroll: true })}
      <p class="lead" style="margin-top:8px;font-size:13px">✔ — требование уже проверяется автотестом прототипа в CI.</p>
      ${report("lz4")}`;

    const st = { q: "", epic: "", rel: new Set() };
    const draw = () => {
      const q = st.q.toLowerCase();
      const rows = S.filter((s) => (!st.epic || s.epic === st.epic) && (!st.rel.size || st.rel.has(s.release)) &&
        (!q || (s.id + s.title + s.story).toLowerCase().includes(q)));
      $("#bl-count").textContent = `${rows.length} из ${S.length} · ${rows.reduce((a, s) => a + s.points, 0)} SP`;
      $("#bl-table").innerHTML = table([
        { label: "ID", key: "id", cls: () => "nowrap" },
        { label: "История", html: true, get: (s) => `<b>${esc(s.title)}</b><br><span style="color:var(--ink-2)">${esc(s.story)}</span>
          <details style="margin-top:4px"><summary style="cursor:pointer;color:var(--accent-ink)">Критерии приёмки (${s.acceptance.length})</summary>
          <ul style="margin:6px 0 0;padding-left:18px">${s.acceptance.map((a) => `<li>${esc(a)}</li>`).join("")}</ul></details>` },
        { label: "Эпик", get: (s) => `${s.epic} · ${B.epics[s.epic]}` },
        { label: "Релиз", html: true, get: (s) => `<span class="tag ${s.release}">${RELEASE[s.release]}</span>` },
        { label: "SP", num: true, key: "points" },
      ], rows);
    };
    $("#bl-q").addEventListener("input", (e) => { st.q = e.target.value; draw(); });
    $("#bl-epic").addEventListener("change", (e) => { st.epic = e.target.value; draw(); });
    $("#bl-tools").querySelectorAll("[data-rel]").forEach((b) => b.addEventListener("click", () => {
      const r = b.dataset.rel;
      st.rel.has(r) ? st.rel.delete(r) : st.rel.add(r);
      b.setAttribute("aria-pressed", st.rel.has(r));
      draw();
    }));
    draw();
  }

  /* ---------------- Базы данных ---------------- */
  function renderDb() {
    const db = D.db;
    const byId = (list) => Object.fromEntries(list.map((x) => [x.id, x]));
    const emp = byId(db.employers), stu = byId(db.students), vac = byId(db.vacancies), cur = byId(db.curators);
    const views = {
      students: {
        label: `Студенты (${db.students.length})`, rows: db.students,
        cols: [{ label: "ФИО", key: "full_name" }, { label: "Группа", key: "group_name" }, { label: "Программа", key: "program" },
          { label: "Курс", key: "course_year", num: true }, { label: "GPA", key: "gpa", num: true },
          { label: "Навыки", get: (r) => r.skills.split(";").join(", ") }, { label: "Куратор", get: (r) => cur[r.curator_id]?.full_name || "" }],
      },
      vacancies: {
        label: `Вакансии (${db.vacancies.length})`, rows: db.vacancies,
        cols: [{ label: "Вакансия", key: "title" }, { label: "Работодатель", get: (r) => emp[r.employer_id]?.name || "" },
          { label: "Тип", get: (r) => (r.kind === "job" ? "работа" : "практика") }, { label: "Город", key: "city" },
          { label: "Формат", get: (r) => ({ office: "офис", remote: "удалённо", hybrid: "гибрид" }[r.work_format]) },
          { label: "Навыки", get: (r) => r.skills_required.split(";").join(", ") }, { label: "Мест", key: "slots", num: true },
          { label: "Приём до", key: "deadline" }, { label: "Статус", get: (r) => (r.status === "open" ? "открыта" : "закрыта") }],
      },
      employers: {
        label: `Работодатели (${db.employers.length})`, rows: db.employers,
        cols: [{ label: "Организация", key: "name" }, { label: "Отрасль", key: "industry" }, { label: "Город", key: "city" },
          { label: "Контакт", key: "contact_email" }, { label: "Договор до", key: "agreement_until" }],
      },
      applications: {
        label: `Заявки (${db.applications.length})`, rows: db.applications,
        cols: [{ label: "№", key: "id", num: true }, { label: "Студент", get: (r) => stu[r.student_id]?.full_name || "" },
          { label: "Вакансия", get: (r) => vac[r.vacancy_id]?.title || "" },
          { label: "Работодатель", get: (r) => emp[vac[r.vacancy_id]?.employer_id]?.name || "" },
          { label: "Статус", get: (r) => STATUS[r.status] }, { label: "Подана", get: (r) => r.submitted_at.slice(0, 10) }],
      },
    };
    const counts = {};
    db.applications.forEach((a) => { counts[a.status] = (counts[a.status] || 0) + 1; });
    $("#db").innerHTML = header("db", "Прототип", "Базы данных: студенты, вакансии, заявки",
      "Демо-база прототипа: все люди, компании и контакты вымышлены (закон РК о персональных данных), поэтому их можно показывать публично. Та же база отдаётся через API, см. «Как запустить».") +
      `<div class="card"><h3 class="sub" style="margin-top:0">Заявки по статусам</h3>
        <div id="status-chart">${hbar(Object.keys(STATUS).filter((k) => counts[k]).map((k) => ({ label: STATUS[k], value: counts[k], tip: `${STATUS[k]}: ${counts[k]} заявок` })), { labelW: 220 })}</div>
        <p class="lead" style="margin:8px 0 0;font-size:13px">У 100 % заявок есть история смены статусов — это главная метрика бизнес-кейса («доля заявок с прослеживаемым статусом»).</p>
      </div>
      <div style="height:16px"></div>
      <div class="tabs" role="tablist">${Object.entries(views).map(([k, v], i) => `<button class="tab" role="tab" type="button" data-view="${k}" aria-selected="${i === 0}">${esc(v.label)}</button>`).join("")}</div>
      <div class="toolbar"><input class="search" id="db-q" type="search" placeholder="Поиск…" aria-label="Поиск по таблице"><span class="count" id="db-count"></span></div>
      <div id="db-table"></div>`;
    bindTip($("#status-chart"));
    let view = "students", q = "";
    const draw = () => {
      const v = views[view];
      const ql = q.toLowerCase();
      const rows = v.rows.filter((r) => !ql || v.cols.map((c) => (c.get ? c.get(r) : r[c.key])).join(" ").toLowerCase().includes(ql));
      $("#db-count").textContent = `${rows.length} из ${v.rows.length}`;
      $("#db-table").innerHTML = table(v.cols, rows, { scroll: true });
    };
    $("#db").querySelectorAll("[data-view]").forEach((b) => b.addEventListener("click", () => {
      view = b.dataset.view;
      $("#db").querySelectorAll("[data-view]").forEach((x) => x.setAttribute("aria-selected", x === b));
      draw();
    }));
    $("#db-q").addEventListener("input", (e) => { q = e.target.value; draw(); });
    draw();
  }

  /* ---------------- ADR, файлы, запуск ---------------- */
  function renderAdr() {
    $("#adr").innerHTML = header("adr", "Журнал решений", "Архитектурные и управленческие решения",
      "Каждое значимое решение записано по шаблону MADR: контекст, рассмотренные варианты, решение, последствия.") +
      `<div class="grid">${D.adr.map((a) => `<details class="report" style="margin:0"><summary>${esc(a.html.match(/<h1>(.*?)<\/h1>/)?.[1].replace(/<[^>]+>/g, "") || "ADR-" + a.id)}</summary>
        <div class="card html-block" style="margin-top:8px">${a.html}</div></details>`).join("")}</div>`;
  }

  function renderFiles() {
    $("#files").innerHTML = header("files", "Скачать", "Файлы лабораторных") +
      `<ul class="list-plain">${D.downloads.map((f) => `<li><span class="kind">${esc(f.kind)}</span>
        <a href="${esc(f.file)}" download>${esc(f.name)}</a></li>`).join("")}</ul>`;
  }

  function renderRun() {
    $("#run").innerHTML = header("run", "Прототип", "Как запустить систему",
      "Сайт показывает документы и данные. Работающий API с подачей заявок и сменой статусов запускается отдельно.") +
      `<div class="grid two">
        <div class="card"><h3 class="sub" style="margin-top:0">На своём компьютере</h3>
          <pre><code>git clone ${repoUrl}.git
cd praktika-project
pip install -r requirements-dev.txt
python -m uvicorn app.main:app --port 8000</code></pre>
          <p>Затем откройте <code>http://127.0.0.1:8000</code> — интерактивная документация API.</p></div>
        <div class="card"><h3 class="sub" style="margin-top:0">В браузере через GitHub Codespaces</h3>
          <p>В репозитории: <b>Code → Codespaces → Create codespace on main</b>. После установки:</p>
          <pre><code>uvicorn app.main:app --host 0.0.0.0 --port 8000</code></pre>
          <p>Откройте предложенный адрес и допишите <code>/docs</code>.</p>
          <a class="btn" href="${repoUrl}/codespaces" target="_blank" rel="noopener">Открыть Codespaces ↗</a></div>
      </div>`;
    $("#footer").innerHTML = `Собрано автоматически из репозитория <a href="${repoUrl}">${esc(D.meta.repo)}</a>
      ${D.meta.sha ? `(коммит ${esc(D.meta.sha)})` : ""} · ${esc(D.meta.built)}. Черновики подготовлены с помощью AI-ассистента Claude;
      команда проверяет факты и отвечает за содержание.`;
  }

  /* ---------------- навигация и тема ---------------- */
  function initNav() {
    const links = [...document.querySelectorAll("#nav a")];
    const obs = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) links.forEach((a) => a.classList.toggle("active", a.getAttribute("href") === "#" + e.target.id));
      });
    }, { rootMargin: "-40% 0px -55% 0px" });
    document.querySelectorAll("main section").forEach((s) => obs.observe(s));
    $("#repo-link").href = repoUrl;
    $("#theme-btn").addEventListener("click", () => {
      const root = document.documentElement;
      const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
      root.dataset.theme = dark ? "light" : "dark";
      try { localStorage.setItem("theme", root.dataset.theme); } catch (e) { /* приватный режим */ }
    });
  }

  renderOverview();
  renderLz1();
  renderLz2();
  renderLz3();
  renderLz4();
  renderDb();
  renderAdr();
  renderFiles();
  renderRun();
  initNav();
  bindTip($("#lz1"));
})();
