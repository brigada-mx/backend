# 719s.mx

~~~sh
ansible-vault decrypt deploy/group_vars/*secret* --vault-password-file .ansible-vault-pass
~~~

## deploy
~~~sh
ansible-playbook -u root -i inventories/production --vault-password-file ../.ansible-vault-pass playbooks/deploy/webserver.yml playbooks/deploy/api.yml --tags="clone_repo,env_vars,virtualenv,migrate" --extra-vars="{'git_branch': 'master'}"

ansible-playbook -u root -i inventories/production --vault-password-file ../.ansible-vault-pass playbooks/service.yml --tags="api,jobs" --extra-vars="{'action': 'restarted'}"
~~~
