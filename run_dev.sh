python3 tools/vault.py --infile=env.dev --outfile=.env
cp requirements-dev.txt requirements.txt
docker-compose up --build -d
