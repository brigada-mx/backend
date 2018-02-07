# 719s.mx


## Dev
We use [Docker](https://docs.docker.com/docker-for-mac/) and `docker-compose` in development to package and deploy our application.

To start docker containers, run `docker-compose up --build -d`. To see which containers are running, run `docker-compose ps`. To stop all containers, run `docker-compose stop`.

To blow all containers away and build them from scratch, use `docker-compose rm` and then `docker-compose up --build -d`.

To decrypt env vars in `env.dev` and run dev, execute `./dev.sh`.


### Data with Git Large File Storage
We store data for localities, municipalities, states and establishments in the [data](https://github.com/919MX/data) repo using [git lfs](https://git-lfs.github.com/). Large file storage allows us to work with these files using normal git commands.

To install git lfs, run `brew install git-lfs` and then `git lfs install`. After this, you can simply use normal git commands to work with files in the data repo.


### Load initial data
First, install `git lfs` and clone data from <https://github.com/919MX/data>.

~~~sh
# dump data, THIS IS NOT NECESSARY if you're not a dev
pg_dump --user custom --host 127.0.0.1 --port 5432 -a -t map_locality -t map_sciangroup -t 
map_establishment -t map_municipality -t map_state > /tmp/dump.sql

# load it to docker container from data repository
docker cp ../data/dump/dump.sql 919_db:/dump.sql
# run command on docker container to load data
docker exec -it 919_db psql -h 127.0.0.1 -p 5432 -U postgres -f /dump.sql
# remove dump from docker container
docker exec -it 919_db rm /dump.sql
~~~


#### Locality search index
After localities have been loaded to DB, execute `locality_search_index.sql` to build a full text search index on `name`, `municipality_name` and `state_name` of localities.

Based on [this awesome article](http://rachbelaid.com/postgres-full-text-search-is-good-enough/).

I also built a similar index [using Algolia](https://www.algolia.com/apps/X7TC2B45DA/dashboard), but the free tier only allows us 10000 documents.

~~~sh
COPY (SELECT id, cvegeo, name, municipality_name, state_name FROM map_locality WHERE has_data=true) TO '/tmp/localities_index.csv' CSV;
docker cp 919_db:/tmp/localities_index.csv ../data/algolia/
~~~

The search results may be of higher quality, and they're faster. But we can't put all of the countries localities in the index, which means we have to rebuild it every time we get new data on damaged buildings. PostgreSQL's full text search is good enough.


## Deploy


## Env vars
Application configuration is stored in environment variables. These are stored in the `env.dev` and `env.prod` files.

`dev.sh` decrypts env vars in `env.dev` and then runs our containers. These env vars are sourced by `docker-compose.yml` and our containers.


### Editing env vars
Make sure you have the `.vault-password` file, with the correct password, in the root of the repo. To decrypt env vars, run `python3 tools/vault.py --infile=env.<dev|prod>`. To encrypt them again run `python3 tools/vault.py --infile=env.<dev|prod> --encrypt`.


### Committing
To make sure unencrypted env vars don't get committed, run `cp pre-commit .git/hooks` from the root of this repo. The `pre-commit` hook fails if any env files are not encrypted.


## ngrok
~~~sh
cd ~
wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip
sudo apt-get install unzip
unzip ngrok-stable-linux-amd64.zip
rm ngrok-stable-linux-amd64.zip
./ngrok http 8000
~~~


## Forms
Forms admin [here](https://kobo.humanitarianresponse.info/#/forms). Online form [here](https://ee.humanitarianresponse.info/x/#Yhgh).


## Images
We serve thumbnails using Amazon's [serverless-image-handler](https://docs.aws.amazon.com/solutions/latest/serverless-image-handler/deployment.html), which uses [Thumbor](https://github.com/thumbor/thumbor) behind the scenes.

Manage this stack [here](https://console.aws.amazon.com/cloudformation/home?region=us-east-1).
