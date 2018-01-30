python3 tools/vault.py --infile=src/env.dev --outfile=src/.env
cd src
docker-compose up --build -d
