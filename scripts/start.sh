#!/usr/bin/env bash
set -euo pipefail
LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$LAB_ROOT"
if ! command -v npm >/dev/null 2>&1; then
  echo "Instale Node.js 22.12 ou superior para preparar a interface."
  exit 1
fi
node -e 'const [major, minor] = process.versions.node.split(".").map(Number); if (major < 22 || (major === 22 && minor < 12)) { console.error("A interface precisa de Node.js 22.12 ou superior."); process.exit(1); }'
cd frontend
npm ci --no-audit --no-fund
npm run build
cd "$LAB_ROOT"
exec ./scripts/lab.sh serve --open "$@"
