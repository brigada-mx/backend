python3 tools/vault.py --infile=env.prod --outfile=src/.env
rm -dr src/static
cp requirements-prod.txt requirements.txt
docker build -t backend_base --file Dockerfile.api .
docker build -t nginx --file Dockerfile.nginx .
