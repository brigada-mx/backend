# 719s.mx

~~~sh
ansible-vault decrypt deploy/group_vars/*secret* --vault-password-file .ansible-vault-pass
~~~

## deploy
~~~sh
ansible-playbook -u root -i inventories/production --vault-password-file ../.ansible-vault-pass playbooks/deploy/webserver.yml playbooks/deploy/api.yml --tags="clone_repo,env_vars,virtualenv,migrate" --extra-vars="{'git_branch': 'master'}"

ansible-playbook -u root -i inventories/production --vault-password-file ../.ansible-vault-pass playbooks/service.yml --tags="api,jobs" --extra-vars="{'action': 'restarted'}"
~~~

## ngrok
~~~sh
cd ~
wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip
sudo apt-get install unzip
unzip ngrok-stable-linux-amd64.zip
rm ngrok-stable-linux-amd64.zip
./ngrok http 8000
~~~

## Images
We serve thumbnails using Amazon's [serverless-image-handler](https://docs.aws.amazon.com/solutions/latest/serverless-image-handler/deployment.html), which uses [Thumbor](https://github.com/thumbor/thumbor) behind the scenes.
