#!/usr/bin/env bash
# Завдання 1: програмне вивантаження SQALE-метрик з публічного REST API SonarQube Cloud.
# Використання:  ./scripts/fetch_sonarcloud.sh [project_key]
# Результат:     report.json у корені проєкту (сира відповідь сервера) + лог запиту в data/api-call.log
set -euo pipefail
cd "$(dirname "$0")/.."

PROJECT_KEY="${1:-apache_ofbiz-framework}"
ENDPOINT="https://sonarcloud.io/api/measures/component"
METRICS="ncloc,sqale_index,sqale_rating"
URL="${ENDPOINT}?component=${PROJECT_KEY}&metricKeys=${METRICS}"

echo "GET ${URL}"
HTTP_CODE=$(curl -sS -o report.json -w "%{http_code}" "${URL}")
echo "HTTP ${HTTP_CODE}"

mkdir -p data
{
  echo "date:     $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "request:  GET ${URL}"
  echo "status:   HTTP ${HTTP_CODE}"
  echo "response:"
  cat report.json
  echo
} > data/api-call.log

if [ "${HTTP_CODE}" != "200" ]; then
  echo "Помилка: сервер повернув HTTP ${HTTP_CODE}. Відповідь:"; cat report.json; echo
  exit 1
fi

# Додатково: метадані проєкту (назва, організація) для картки об'єкта аудиту
curl -sS "https://sonarcloud.io/api/components/show?component=${PROJECT_KEY}" -o data/project.json || true

echo "Сира відповідь збережена в report.json:"
python3 -m json.tool report.json
