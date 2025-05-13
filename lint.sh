#!/bin/bash

echo "🔍 Running linters and formatters..."

echo "1️⃣ black (code formatter)..."
poetry run black .

echo "2️⃣ isort (import sorter)..."
poetry run isort .

echo "3️⃣ flake8 (style checker)..."
poetry run flake8 .

echo "4️⃣ mypy (type checker)..."
poetry run mypy app/

echo "✅ Done!"