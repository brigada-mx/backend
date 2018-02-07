python3 tools/vault.py --infile=env.dev --outfile=src/.env
cp requirements-dev.txt requirements.txt
rm -f src/celerybeat.pid
docker-compose up --build -d
