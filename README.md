# 0RAYS-CTFd
3.6.0 最新版 CTFd + [CTFd-whale](https://github.com/JBNRZ/ctfd-whale/commit/08a4a92b80bcffa0efa5b49bdb8f01f4d9b5bc0a)

# Start
```bash
sed -i "s/\r//g" docker-entrypoint.sh
docker swarm init
docker node update --label-add name=linux-1 $(docker node ls -q)
docker compose up -d
```
