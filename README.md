# 0RAYS-CTFd
[3.6.1 CTFd](https://github.com/CTFd/CTFd/releases/tag/3.6.1) + [CTFd-whale](https://github.com/JBNRZ/ctfd-whale/commit/08a4a92b80bcffa0efa5b49bdb8f01f4d9b5bc0a)

# Before start

- conf/nginx/http.conf
```c
// change it to your own domain
server_name *.training.0rays.club
```

- conf/frp/frps.ini
```c
// change it to your own domain
subdomain_host = training.0rays.club
```

- docker-compose.yml
```yaml
- HDU_OA_CLIENT_ID=7Fa0bJwCH7mTXKsB
- HDU_OA_CLIENT_SECRET=j7OhxWunxuK8FlDlHbEiUvKXMJ6Ef07Z
- HDU_OA_REDIRECT_URI=https://api.0rays.club/ctfd/redirect 
```

# Start
```bash
sed -i "s/\r//g" docker-entrypoint.sh
docker swarm init
docker node update --label-add name=linux-1 $(docker node ls -q)
docker compose up -d
```


