# Brigada


## Dev
We use [Docker](https://docs.docker.com/docker-for-mac/) and `docker-compose` in development to package and deploy our application.

To decrypt env vars in `env.dev` and run dev, execute `./dev.sh`. To see which containers are running, run `docker-compose ps`. To stop all containers, run `docker-compose stop`.

To blow containers away and build them from scratch, use `docker-compose rm` then `./dev.sh`.


### Logs
__PostgreSQL__: open `/var/lib/postgresql/data/postgresql.conf` in the __db__ container, also at `dbdata/postgresql.conf`, and add the following:

~~~sh
logging_collector = 'on'
log_statement = 'all'
log_line_prefix = '%t'
~~~

Then restart the db container, `docker-compose restart db`. Tail logs like this:

~~~sh
less +F dbdata/pg_log/`ls -1 dbdata/pg_log/ | tail -1`
~~~


## Deploy
For devs only. Run `./build.sh`. This will decrypt production env vars and build the `backend_base` and `nginx` images. Tag and push these images to [ECR](https://us-west-2.console.aws.amazon.com/ecs/home?region=us-west-2#/repositories/), then deploy from the AWS Elastic Beanstalk console.

~~~sh
# log in
aws ecr get-login --no-include-email --region us-west-2

# example: push the latest nginx image to ECR
docker tag nginx:latest 306439459454.dkr.ecr.us-west-2.amazonaws.com/nginx:latest
docker push 306439459454.dkr.ecr.us-west-2.amazonaws.com/nginx:latest
~~~

__Make sure Elastic Beanstalk IAM user has permissions to read from ECR__. If not deploy will fail.


## Endpoints
NGINX forces HTTPS for requests to these endpoints. It also compresses responses.

- API: <https://api.brigada.mx/api/>
- Celery flower: <https://api.brigada.mx/flower/>
- Django admin: <https://api.brigada.mx/admin/>


## AWS
We manage our infrastructure with AWS. We deploy to Elastic Beanstalk multi container Docker environments. This means the same `Dockerfile`s that build our images in dev build them in production.


### SSL
We use ACM to generate certificates. __ACM certificates can only be used with AWS load balancers and CloudFront distributions,__ but this is what we use to serve both our web app and our API. Here's an [excellent tutorial](https://gist.github.com/bradwestfall/b5b0e450015dbc9b4e56e5f398df48ff) on how to set up CloudFront for sites served by S3. 

Our landing page is served from S3 without CloudFront, because [we don't need SSL for the landing page](https://stackoverflow.com/questions/42441828/https-on-s3-without-cloudfront-possible).

__The certificate must be created in `us-east-1` region to be used with CloudFront__. This isn't well-documented. See certificate [here](https://console.aws.amazon.com/acm/home?region=us-east-1).

Traffic between our backend AWS instances is not encrypted, because [it's not necessary](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/configuring-https-endtoend.html).

>>Terminating secure connections at the load balancer and using HTTP on the backend may be sufficient for your application. __Network traffic between AWS resources cannot be listened to by instances that are not part of the connection__, even if they are running under the same account.


### RDS and ElastiCache
Our PostgreSQL and Redis instances are managed by [RDS](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/AWSHowTo.RDS.html) and [ElastiCache](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/AWSHowTo.ElastiCache.html).

There are many ways to grant RDS/ElastiCache ingress access to EC2 instances, for example:

- find the __default VPC security group__ that is assigned to both ElastiCache and RDS instances
- add ingress rules to this group on ports 5432 and 6379 for `919-api` and `919-celery-beat` environment security groups

However, this creates an explicit dependency between the EC2 instance and our data stores. This means __we won't be able rebuild or terminate our environment__.

If you try to do so, __you're entering a world of pain__. Instead of failing fast, AWS kill your EC2 instances, then hang for an hour or more while it periodically informs you that your security groups can't be deleted.

Here's how to do it right: [Grant Elastic Beanstalk environment access to RDS and ElastiCache automatically](https://notebookheavy.com/2017/06/22/elastic-beanstalk-rds-automatic-access/).

Basically, create a security group called `redis-postgres-read`. Then find the __default VPC security group__ for RDS/ElastiCache and add ingress rules on ports 5432 and 6379 for the `redis-postgres-read` security group. Finally, add this group to __EC2 security groups__ in __Configuration > Instances__ in the Elastic Beanstalk environment console.


#### Testing connections
To test connectivity between EC2 instances and data stores:

~~~sh
# ssh into ec2 box and test connectivity
nc -v pg-919.cexrnsicl0n4.us-west-2.rds.amazonaws.com 5432
nc -v redis.jmyuno.ng.0001.usw2.cache.amazonaws.com 6379

# to test credentials for conencting to postgres
sudo yum install postgresql-devel
PGPASSWORD=password psql -h pg-919.cexrnsicl0n4.us-west-2.rds.amazonaws.com -U postgres -d postgres
~~~


## Load initial data
This must be done in both dev and production.

First, install `git lfs` and clone data from <https://github.com/919MX/data>.

~~~sh
# dump data, THIS IS NOT NECESSARY if you're not a dev
pg_dump -U postgres -a -t map_locality -t map_sciangroup -t map_establishment -t map_municipality -t map_state > /tmp/dump.sql
docker cp 919_db:/tmp/dump.sql ../data/dump/

# load it to docker container from data repository
docker cp ../data/dump/dump.sql 919_db:/dump.sql
# run command on docker container to load data
docker exec -it 919_db psql -h 127.0.0.1 -p 5432 -U postgres -f /dump.sql
# remove dump from docker container
docker exec -it 919_db rm /dump.sql

# or, in production
scp -i ~/.ssh/fortana ../data/dump/dump.sql ssh ec2-user@<ec2_instance_ip>:/home/ec2-user/
# then, from ec2 instance
sudo yum install postgresql-devel
PGPASSWORD=password psql -h pg-919.cexrnsicl0n4.us-west-2.rds.amazonaws.com -U postgres -d postgres -f dump.sql
rm dump.sql
~~~


### Mapbox tileset locality CSV
~~~sql
copy (SELECT cvegeo, ST_X(location) as longitude, ST_Y(location) as latitude, meta ->> 'total' as total FROM map_locality where has_data = true) to '/tmp/mapbox_localities.csv' with CSV DELIMITER ',';
docker cp 919_db:/tmp/mapbox_localities.csv ../data/damage/
~~~


### Locality search index
After localities have been loaded to DB, execute `locality_search_index.sql` to build a full text search index on `name`, `municipality_name` and `state_name` of localities.

Based on [this awesome article](http://rachbelaid.com/postgres-full-text-search-is-good-enough/).

I also built a similar index [using Algolia](https://www.algolia.com/apps/X7TC2B45DA/dashboard), but the free tier only allows us 10000 documents.

~~~sql
COPY (SELECT id, cvegeo, name, municipality_name, state_name FROM map_locality WHERE has_data=true) TO '/tmp/localities_index.csv' CSV;
docker cp 919_db:/tmp/localities_index.csv ../data/algolia/
~~~

The search results may be of higher quality, and they're faster. But we can't put all the localities in the index, which means we have to rebuild it every time we get new data on damaged buildings. PostgreSQL's full text search is good enough.


## Copy production data to dev
~~~sql
# connect to local database
delete from users_organizationusertoken;
delete from users_donorusertoken;
delete from users_organizationuser;
delete from users_donoruser;
delete from map_share;
delete from map_volunteeropportunity;
delete from map_volunteerapplication;
delete from map_donation;
delete from map_submission;
delete from map_testimonial;
delete from map_actionlog;
delete from map_action;
delete from map_donor;
delete from map_organization;
delete from users_volunteeruser;
~~~

~~~sh
# in EC2 dashboard, find "default VPC security group", and add ingress access to "My IP"

PGPASSWORD=password pg_dump -h pg-919.cexrnsicl0n4.us-west-2.rds.amazonaws.com -U postgres -a -t users_volunteeruser -t map_organization -t map_donor -t map_action -t map_actionlog -t map_testimonial -t map_submission -t map_donation -t map_volunteerapplication -t map_volunteeropportunity -t map_share -t users_donoruser -t users_organizationuser -t users_donorusertoken -t users_organizationusertoken > /tmp/dump.sql

docker cp /tmp/dump.sql 919_db:/dump.sql
docker exec -it 919_db psql -h 127.0.0.1 -p 5432 -U postgres -f /dump.sql
~~~


## Env vars
Application configuration is stored in environment variables. These are stored in the `env.dev` and `env.prod` files.

`dev.sh` decrypts env vars in `env.dev` then runs our containers. These env vars are sourced by `docker-compose.yml` and our containers.


### Editing env vars
Make sure you have the `.vault-password` file, with the correct password, in the root of the repo. To decrypt env vars, run `python3 tools/vault.py --infile=env.<dev|prod>`. To encrypt them again run `python3 tools/vault.py --infile=env.<dev|prod> --encrypt`.


### Committing
To make sure unencrypted env vars don't get committed, run `cd .git/hooks && ln -s ../../pre-commit && cd -` from the root of this repo. The `pre-commit` hook fails if env files are not encrypted, or if code doesn't pass `mypy` checks.


## ngrok
~~~sh
cd ~
wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip
sudo apt-get install unzip
unzip ngrok-stable-linux-amd64.zip
rm ngrok-stable-linux-amd64.zip
./ngrok http 8000
~~~


## Kobo Forms
Forms admin [here](https://kobo.humanitarianresponse.info/#/forms). Online form [here](https://ee.humanitarianresponse.info/x/#Yhgh).

We have a periodic job that syncs images from Kobo's backend to [this S3 bucket](https://s3.console.aws.amazon.com/s3/buckets/719s/?region=us-west-2).


## Images
We serve thumbnails using Amazon's [serverless-image-handler](https://docs.aws.amazon.com/solutions/latest/serverless-image-handler/deployment.html), which uses [Thumbor](https://github.com/thumbor/thumbor) behind the scenes.

Manage this stack [here](https://console.aws.amazon.com/cloudformation/home?region=us-east-1).


## Passwords and Random Strings
~~~
openssl rand -base64 40
~~~


## Create StaffUser
~~~sh
# ssh into ec2 instance

# ssh into docker container
sudo docker exec -it <container_id> /bin/ash

source .env
python manage.py staffuser --email <email> --password <password> --full_name <full_name>
~~~


## Email our Users
From the root of the repo, run `python3 tools/org_users_to_contacts.py --outfile ~/Desktop/contacts.csv`. If this fails, make sure you have Python 3.6 or greater installed. The easiest way to do this is run `brew install python`.

This script will create a CSV with all of our organization users that can be imported to Google Contacts.


## pgweb for read-only access to our DB
The quick and dirty way. Password-protected, but no SSL.
~~~sh
wget https://github.com/sosedoff/pgweb/releases/download/v0.9.11/pgweb_linux_amd64.zip
unzip pgweb_linux_amd64.zip
mv pgweb_linux_amd64.zip pgweb

./pgweb --url postgres://postgres:password@pg-919.cexrnsicl0n4.us-west-2.rds.amazonaws.com:5432/postgres --bind=0.0.0.0 --readonly --auth-user brigada --auth-pass <auth-pass> &

# http://<ec2-ip>:8081/
~~~

A much better way, running in a multi-container, single instance docker env. Uses <https://github.com/DanielDent/docker-nginx-ssl-proxy> and <https://github.com/sosedoff/pgweb>. This depends on instances in this EB environment having read access to PostgreSQL.

Lives at <pgweb.brigada.mx>. The connection is read-only, password protected and runs over SSL. This solution is safe and decoupled from the API.


## Linting and Code Style
Enforced by `flake8` linter.

~~~sh
pip install flake8
pip install flake8-commas
~~~

Check `.flake8` for rules. Run linter on all files, ignoring line length warnings: `flake8 . | grep -v E501`.


### Type Checking with Mypy
~~~sh
pip install mypy
~~~

Check `mypy.ini` for [config options](http://mypy.readthedocs.io/en/latest/config_file.html).

Mypy cheat sheet: <http://mypy.readthedocs.io/en/latest/cheat_sheet_py3.html>.

- `mypy --no-incremental src`
- `mypy src --no-incremental --check-untyped-defs`

The `--no-incremental` flag disables cache. This is a bit slower, but necessary until [this bug](https://github.com/python/mypy/issues/4287) is fixed.
