python3 tools/vault.py --infile=env.prod --outfile=src/.env
python3 tools/vault.py --infile=env.pgweb --outfile=pgweb/.env
cp requirements-prod.txt requirements.txt
docker build -t backend_base --file Dockerfile.api .
docker build -t nginx --file Dockerfile.nginx .
docker build -t pgweb --file Dockerfile.pgweb .
docker build -t nginx_pgweb --file Dockerfile.nginx-pgweb .

curl -d '{"app_type":"backend", "git_hash":"'`git rev-parse HEAD`'"}' -H "Content-Type: application/json" -H "Authorization: Bearer `cat .secret-key`" -X POST https://api.brigada.mx/api/internal/app_versions/
