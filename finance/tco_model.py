"""TCO/ROI-модель проекта «Практика» (ЛЗ 3).

Единственный источник правды для чисел: те же формулы собраны в tco_model.xlsx
(generate_xlsx.py). Запуск: python finance/tco_model.py
Все суммы — в тенге. Горизонт: год 0 (внедрение) + 3 года эксплуатации.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# --- Параметры: [S*] — открытый источник, [A*] — допущение (см. ASSUMPTIONS) ---
P = {
    "usd_kzt": 445.65,           # [S6] курс НБ РК на 24.09.2026
    "discount_rate": 0.1625,     # [S7] базовая ставка НБ РК с 04.09.2026
    "vat": 0.16,                 # [S8] НДС с 01.01.2026
    "salary_edu": 315_100,       # [S1] ср. зарплата в образовании, I кв. 2026
    "salary_dev": 468_000,       # [S2] ср. зарплата Junior Python, 2026
    "payroll_factor": 1.15,      # [A1] начисления работодателя на ФОТ
    "hours_month": 168,          # [A2] рабочих часов в месяце
    "methodist_h_before": 4.0,   # [A3] ч/нед на сведение заявок сейчас (карточка ЛЗ1)
    "methodist_h_after": 1.0,    # [A3] ч/нед после внедрения (цель из карточки ЛЗ1)
    "active_weeks": 36,          # [A4] недель в году с потоком заявок
    "curators": 12,              # [A5] кураторов практики
    "curator_h_week": 0.5,       # [A5] ч/нед на выяснение статусов и сроков
    "curator_saving": 0.5,       # [A5] доля времени кураторов, которую снимает система
    "curator_weeks": 30,         # [A5] недель практики с отчётами
    "lost_cases_year": 8,        # [A16] потерянных заявок/жалоб в год
    "lost_case_hours": 3,        # [A16] ч на разбор одной потерянной заявки
    "ramp_y1": 0.8,              # [A6] реализация эффекта в год 1 (адаптация)
    "dev_hours": 480,            # [A7] разработка MVP (2 разработчика)
    "pm_ba_hours": 120,          # [A7] PM + аналитика
    "migration_hours": 16,       # [A8] перенос данных из Excel
    "users_trained": 15,         # [A9] методисты + кураторы
    "training_h_user": 2,        # [A9] часов обучения на пользователя
    "retraining_h_year": 15,     # [A9] ч/год на обучение новых кураторов
    "support_h_month": 4,        # [A10] поддержка собственной системы
    "vps_month": 4_800,          # [S3] hoster.kz Cloud 1-2-50 (1 vCPU, 2 ГБ)
    "backup_vps_month": 3_100,   # [S3] hoster.kz Cloud 1-1-25 под резервные копии
    "ws_license_usd": 1_176,     # [S5] Windows Server 2025 Standard, 16 ядер
    "sql_2core_usd": 3_945,      # [S5] SQL Server Standard, пакет 2 ядра
    "sql_packs": 2,              # [S5] минимум 4 ядра на сервер
    "b24_month": 30_400,         # [S4] Битрикс24 «Стандартный», оплата за год, без НДС
    "b24_setup_hours": 40,       # [A11] настройка воронок, форм, ролей
    "b24_support_h_month": 2,    # [A11] администрирование портала
    "b24_benefit_share": 0.8,    # [A11] типовая CRM закрывает ~80 % эффекта
    "decommission_hours": 16,    # [A12] выгрузка данных и вывод из эксплуатации
    "b24_decommission_hours": 8,  # [A12] выгрузка из Битрикс24
}

SOURCES = {
    "S1": "Бюро национальной статистики АСПиР РК. Заработная плата за I квартал 2026 года — stat.gov.kz/ru/news/zarabotnaya-plata-za-i-kvartal-2026-goda/",
    "S2": "Taylor.kz. Зарплата Python-разработчика в Казахстане 2026 (Junior — среднее 468 000 ₸) — taylor.kz/salaries/python",
    "S3": "Hoster.kz. Облачные серверы, прайс — hoster.kz/cloud/vps/",
    "S4": "Битрикс24 Казахстан. Тарифы и цены (без НДС) — bitrix24.kz/prices/",
    "S5": "Microsoft. SQL Server 2025 Pricing (PDF, $3 945 за 2 ядра Standard); Microsoft Store: Windows Server 2025 Standard 16 core ($1 176) — microsoft.com",
    "S6": "Национальный Банк РК. Официальный курс USD/KZT на 24.09.2026 = 445,65 ₸ — nationalbank.kz",
    "S7": "Национальный Банк РК. О снижении базовой ставки до 16,25 % (04.09.2026) — nationalbank.kz/ru/news/press-relizy/20266",
    "S8": "Налоговый кодекс РК (действует с 01.01.2026): ставка НДС 16 % — adilet.zan.kz",
}

ASSUMPTIONS = {
    "A1": "Начисления работодателя на ФОТ — коэффициент 1,15 (социальный налог и взносы, укрупнённо).",
    "A2": "168 рабочих часов в месяце (40 ч × 4,2 недели).",
    "A3": "Методист сейчас тратит 4 ч/нед на сведение заявок, после внедрения — 1 ч/нед (карточка проекта ЛЗ 1; подтвердить у заказчика).",
    "A4": "Поток заявок идёт 36 недель в году (два семестра).",
    "A5": "12 кураторов по 0,5 ч/нед выясняют статусы и сроки отчётов 30 недель в году; система снимает половину этого времени.",
    "A6": "В первый год эксплуатации реализуется 80 % эффекта (адаптация пользователей).",
    "A7": "Трудоёмкость MVP: 480 ч разработки + 120 ч PM/аналитики (уточняется в ЗС 5–6).",
    "A8": "Перенос исторических данных из Excel — 16 ч.",
    "A9": "Обучение: 15 пользователей × 2 ч в году 0; далее 15 ч/год на новых кураторов.",
    "A10": "Поддержка собственной системы — 4 ч/мес по ставке junior-разработчика (обновления, резервные копии, мелкие правки).",
    "A11": "Битрикс24: 40 ч настройки, 2 ч/мес администрирования; типовая CRM закрывает ~80 % эффекта (нет кабинета студента под наш процесс).",
    "A12": "Вывод из эксплуатации в конце года 3: 16 ч для своей системы, 8 ч для Битрикс24.",
    "A13": "Вариант В3-С: труд студенческой команды в году 0 университет не оплачивает (учебный проект), поддержку с года 1 берёт ИТ-отдел по рыночной ставке.",
    "A14": "Проприетарный стек размещается на том же VPS по модели BYOL; лицензии бессрочные, без Software Assurance; разработка по трудоёмкости как в В3.",
    "A15": "Эффект начинается с года 1; в году 0 стенд работает 4 месяца (1/3 годовой стоимости инфраструктуры/подписки).",
    "A16": "«Несколько раз в семестр» (карточка ЛЗ 1) = 8 потерянных заявок в год; разбор каждой (поиск, извинения, повторная маршрутизация) — 3 ч методиста.",
    "A17": "Нагрузка 30–40 заявок в неделю и до 15 сотрудников: сервера 1 vCPU / 2 ГБ достаточно для FastAPI + PostgreSQL (проверить нагрузочным тестом в ЗС 11).",
}


def hourly(salary: float) -> float:
    return salary * P["payroll_factor"] / P["hours_month"]


RATE_EDU = hourly(P["salary_edu"])
RATE_DEV = hourly(P["salary_dev"])


def saved_hours() -> float:
    methodist = (P["methodist_h_before"] - P["methodist_h_after"]) * P["active_weeks"]
    curators = P["curators"] * P["curator_h_week"] * P["curator_saving"] * P["curator_weeks"]
    lost = P["lost_cases_year"] * P["lost_case_hours"]
    return methodist + curators + lost


def annual_benefit() -> float:
    return saved_hours() * RATE_EDU


@dataclass
class Option:
    name: str
    costs: list[float]                                    # годы 0..3
    benefit_share: float = 1.0
    benefits: list[float] = field(default_factory=list)

    def __post_init__(self):
        b = annual_benefit() * self.benefit_share
        self.benefits = [0.0, b * P["ramp_y1"], b, b]

    def scaled(self, cost_k: float = 1.0, benefit_k: float = 1.0) -> Option:
        o = Option(self.name, [c * cost_k for c in self.costs], self.benefit_share)
        o.benefits = [b * benefit_k for b in self.benefits]
        return o

    @property
    def tco(self) -> float:
        return sum(self.costs)

    @property
    def total_benefit(self) -> float:
        return sum(self.benefits)

    @property
    def roi(self) -> float | None:
        return (self.total_benefit - self.tco) / self.tco if self.tco else None

    @property
    def npv(self) -> float:
        r = P["discount_rate"]
        return sum((b - c) / (1 + r) ** t for t, (b, c) in enumerate(zip(self.benefits, self.costs)))

    @property
    def payback_years(self) -> float | None:
        """Срок окупаемости в годах от начала эксплуатации (линейная интерполяция)."""
        if not self.tco:
            return None
        cum = 0.0
        for t, (b, c) in enumerate(zip(self.benefits, self.costs)):
            prev, cum = cum, cum + b - c
            if t > 0 and cum >= 0:
                return t - 1 + (-prev / (b - c))
        return None


def training_y0() -> float:
    return P["users_trained"] * P["training_h_user"] * RATE_EDU


def own_build(name: str, dev_paid: bool, licenses: float = 0.0) -> Option:
    infra = (P["vps_month"] + P["backup_vps_month"]) * 12
    dev = (P["dev_hours"] + P["pm_ba_hours"]) * RATE_DEV if dev_paid else 0.0
    y0 = dev + licenses + P["migration_hours"] * RATE_DEV + training_y0() + infra / 3
    run = infra + P["support_h_month"] * 12 * RATE_DEV + P["retraining_h_year"] * RATE_EDU
    return Option(name, [y0, run, run, run + P["decommission_hours"] * RATE_DEV])


def licenses_proprietary() -> float:
    usd = P["ws_license_usd"] + P["sql_2core_usd"] * P["sql_packs"]
    return usd * P["usd_kzt"] * (1 + P["vat"])


def options() -> list[Option]:
    b24_year = P["b24_month"] * 12 * (1 + P["vat"])
    b24_run = b24_year + P["b24_support_h_month"] * 12 * RATE_DEV + P["retraining_h_year"] * RATE_EDU
    b24_y0 = (P["b24_setup_hours"] + P["migration_hours"]) * RATE_DEV + training_y0() + b24_year / 3
    return [
        Option("В0. Ничего не делать (Excel + почта)", [0.0] * 4, benefit_share=0.0),
        Option("В1. Купить готовое: Битрикс24 «Стандартный»",
               [b24_y0, b24_run, b24_run, b24_run + P["b24_decommission_hours"] * RATE_DEV],
               P["b24_benefit_share"]),
        own_build("В2. Своя разработка, проприетарный стек (Windows Server + SQL Server)", True,
                  licenses_proprietary()),
        own_build("В3. Своя разработка, открытый стек (Linux + PostgreSQL + Python)", True),
        own_build("В3-С. Открытый стек силами студенческой команды", False),
    ]


SCENARIOS = [("База", 1.0, 1.0), ("Затраты +30 %", 1.3, 1.0),
             ("Эффект 50 %", 1.0, 0.5), ("Затраты +30 % и эффект 50 %", 1.3, 0.5)]


def fmt(x: float | None, pct: bool = False) -> str:
    if x is None:
        return "—"
    return f"{x * 100:,.0f} %".replace(",", " ") if pct else f"{x:,.0f}".replace(",", " ")


if __name__ == "__main__":
    print(f"Ставка методиста/куратора: {RATE_EDU:,.0f} ₸/ч; разработчика: {RATE_DEV:,.0f} ₸/ч")
    print(f"Сэкономлено часов в год: {saved_hours():.0f}")
    print(f"Годовой эффект (100 %): {annual_benefit():,.0f} ₸; cost of delay ≈ {annual_benefit() / 12:,.0f} ₸/мес")
    print(f"Лицензии проприетарного стека: {licenses_proprietary():,.0f} ₸")
    for scen, ck, bk in SCENARIOS:
        print(f"\n== {scen} ==")
        for o in options():
            s = o.scaled(ck, bk)
            pb = s.payback_years
            print(f"{s.name[:58]:58} TCO {fmt(s.tco):>10} выгода {fmt(s.total_benefit):>10} "
                  f"ROI {fmt(s.roi, True):>7} NPV {fmt(s.npv):>11} окуп. {'—' if pb is None else f'{pb:.1f}'}")
            if scen == "База":
                print("   по годам:", [fmt(c) for c in s.costs], [fmt(b) for b in s.benefits])
