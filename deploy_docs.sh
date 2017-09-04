#!/bin/bash
set -e

# Desencrypt key. Note: id_rsa_qldocs.pub must be added to repo's keys!
openssl aes-256-cbc -K $encrypted_79127a601abf_key -iv $encrypted_79127a601abf_iv -in id_rsa_qldocs.enc -out id_rsa_qldocs -d
chmod 600 id_rsa_qldocs
eval `ssh-agent -s`
ssh-add id_rsa_qldocs
rm id_rsa_qldocs

# Workaround mkdocs lack of support for ssh remote.
git config user.name "deploy_docs_sh"
git config user.email "docs@quantumleap.com"
git remote add gh-ssh "git@github.com:smartsdk/ngsi-timeseries-api.git"
git fetch gh-ssh && git fetch gh-ssh +gh-pages:gh-pages

mkdocs gh-deploy -v --clean --remote-name gh-ssh
