python3 tools/vault.py --infile=env.prod --outfile=src/.env
cp requirements-prod.txt requirements.txt
cp Dockerfile.api Dockerfile
docker build -t backend_base .
