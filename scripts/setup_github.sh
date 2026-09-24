#!/usr/bin/env bash
# Настройка репозитория на GitHub по соглашениям ЛЗ 2: метки и защита main.
# Нужен GitHub CLI (https://cli.github.com) и `gh auth login`.
# Запуск из корня репозитория после первого push: bash scripts/setup_github.sh
set -euo pipefail

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "Репозиторий: $REPO"

label() { gh label create "$1" --color "$2" --description "$3" --force; }

# Типы задач
label "type:epic"  "3E4B9E" "Крупный блок ценности"
label "type:story" "1D76DB" "Пользовательская история"
label "type:task"  "0E8A16" "Техническая задача"
label "type:bug"   "D73A4A" "Ошибка"
label "type:spike" "FBCA04" "Исследование с таймбоксом"
label "type:adr"   "5319E7" "Архитектурное решение"
# Приоритеты
label "priority:high"   "B60205" "Высокий приоритет"
label "priority:medium" "D93F0B" "Средний приоритет"
label "priority:low"    "C2E0C6" "Низкий приоритет"
# Лабораторные
for n in $(seq 1 15); do label "зс-$n" "EDEDED" "Лабораторное занятие $n"; done

# Защита main: PR + 1 одобрение + зелёный CI (для приватных репозиториев нужен платный план)
gh api -X PUT "repos/$REPO/branches/main/protection" --input - <<'JSON'
{
  "required_status_checks": {"strict": true, "contexts": ["test"]},
  "enforce_admins": false,
  "required_pull_request_reviews": {"required_approving_review_count": 1},
  "restrictions": null
}
JSON
echo "Готово. Доску GitHub Projects создайте вручную (см. README, раздел «Что добавить на GitHub»)."
