ansible-playbook -i ./inventory/ec2.py \
      --limit "tag_type_worker" \
      -u ubuntu \
      --extra-vars "master=$1" \
      --private-key ~/.ssh/SoRT.pem worker.yaml -vvvv
