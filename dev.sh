set -e

python3.6 tools/vault.py --infile=env.dev --outfile=src/.env
cp requirements-dev.txt requirements.txt
docker-compose up --build -d
