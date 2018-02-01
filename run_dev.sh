python3 tools/vault.py --infile=src/env.dev --outfile=src/.env
cd src
cp requirements-dev.txt requirements.txt
docker-compose up --build -d
