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

- docker-compose.yml []中为需要修改的内容
```yaml
version: '3'

services:
  # raise: exec /opt/CTFd/docker-entrypoint.sh: No such File or Directory
  # the main reason is '\r', exec 'sed -i "s/\r//g" docker-entrypoint.sh' to remove this character
  ctfd:
    build: .
    user: root
    restart: always
    ports:
      - "8000:8000"
    environment:
      - UPLOAD_FOLDER=/var/uploads
      - DATABASE_URL=mysql+pymysql://[mysql_user]:[mysql_user_password]@db/[database]
      - REDIS_URL=redis://cache:6379
      - WORKERS=1
      - LOG_FOLDER=/var/log/CTFd
      - ACCESS_LOG=-
      - ERROR_LOG=-
      - REVERSE_PROXY=true
      - HDU_OA_CLIENT_ID=[secret]
      - HDU_OA_CLIENT_SECRET=[secret]
      - HDU_OA_REDIRECT_URI=[url]
    volumes:
      - ./data/CTFd/logs:/var/log/CTFd
      - ./data/CTFd/uploads:/var/uploads
      - .:/opt/CTFd
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on:
      - db
    networks:
      default:
      internal:
        ipv4_address: 172.26.0.11

  nginx:
    image: nginx:stable
    restart: always
    volumes:
      - ./conf/nginx/http.conf:/etc/nginx/nginx.conf
    ports:
      - "8001:8001"
    depends_on:
      - ctfd
    networks:
      default:
      internal:
        ipv4_address: 172.26.0.12

  db:
    image: mariadb:10.4.12
    restart: always
    environment:
      - MYSQL_ROOT_PASSWORD=[mysql_root_password]
      - MYSQL_USER=[mysql_user]
      - MYSQL_PASSWORD=[mysql_user_password]
      - MYSQL_DATABASE=[database]
    volumes:
      - ./data/mysql:/var/lib/mysql
    networks:
      internal:
        ipv4_address: 172.26.0.13
    # This command is required to set important mariadb defaults
    command: [mysqld, --character-set-server=utf8mb4, --collation-server=utf8mb4_unicode_ci, --wait_timeout=28800, --log-warnings=0]

  cache:
    image: redis:4
    restart: always
    volumes:
    - ./data/redis:/data
    networks:
      internal:
        ipv4_address: 172.26.0.14

  frps:
    image: glzjin/frp
    restart: always
    volumes:
      - ./conf/frp/frps.ini:/conf/frps.ini
    entrypoint:
      - /usr/local/bin/frps
      - -c
      - /conf/frps.ini
    ports:
      - "10000-10100:10000-10100"
    networks:
      default:
      internal:
        ipv4_address: 172.26.0.15
      frp_connect:
        ipv4_address: 172.27.0.11

  frpc:
    image: glzjin/frp
    restart: always
    volumes:
      - ./conf/frp/frpc.ini:/conf/frpc.ini
    entrypoint:
      - /usr/local/bin/frpc
      - -c
      - /conf/frpc.ini
    depends_on:
      - frps
    networks:
      internal:
        ipv4_address: 172.26.0.16
      frp_containers:
        ipv4_address: 172.28.0.11
      frp_connect:
        ipv4_address: 172.27.0.12

networks:
  default:
  internal:
    internal: true
    ipam:
      config:
        - subnet: 172.26.0.0/24
  frp_connect:
    internal: true
    attachable: true
    driver: overlay
    ipam:
      config:
        - subnet: 172.27.0.0/24
  frp_containers:
    attachable: true
    driver: overlay
    ipam:
      config:
        - subnet: 172.28.0.0/16

```

# Start
```bash
sed -i "s/\r//g" docker-entrypoint.sh
docker swarm init
docker node update --label-add name=linux-1 $(docker node ls -q)
docker compose up -d
```


