python3 tools/vault.py --infile=env.prod --outfile=src/.env
python3 tools/vault.py --infile=env.pgweb --outfile=pgweb/.env

echo "export CUSTOM_GIT_COMMIT_HASH='`git rev-parse HEAD`'" >> src/.env

cp requirements-prod.txt requirements.txt
docker build -t backend_base --file Dockerfile.api .
docker build -t nginx --file Dockerfile.nginx .
docker build -t pgweb --file Dockerfile.pgweb .
docker build -t nginx_pgweb --file Dockerfile.nginx-pgweb .
