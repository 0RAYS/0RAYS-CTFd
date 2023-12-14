# 0RAYS-CTFd
[3.6.1 CTFd](https://github.com/CTFd/CTFd/releases/tag/3.6.1) + [CTFd-whale](https://github.com/JBNRZ/ctfd-whale/commit/08a4a92b80bcffa0efa5b49bdb8f01f4d9b5bc0a) + [hdu-oauth](https://github.com/JBNRZ/hdu-oauth)

# Before start

- conf/nginx/http.conf
```c
// change it to your own domain
server_name *.your_domain
```

- conf/frp/frps.ini
```c
// change it to your own domain
subdomain_host = *.your_domain
```

- docker-compose.yml
```
...
```

# Start
```bash
sed -i "s/\r//g" docker-entrypoint.sh
docker swarm init
docker node update --label-add name=linux-1 $(docker node ls -q)
docker compose up -d
```


