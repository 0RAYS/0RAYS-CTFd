# 0RAYS-CTFd
[3.7.4 CTFd](https://github.com/CTFd/CTFd/releases/tag/3.7.4) + [CTFd-whale](https://github.com/JBNRZ/ctfd-whale) + [hdu-oauth](https://github.com/JBNRZ/hdu-oauth) + submission-notice

# Before start
- conf/nginx/nginx.conf
```ini
# change it to your own domain
server_name *.your_domain
```

- conf/frp/frps.ini
```ini
# change it to a random strings
token = token
# change it to your own domain
subdomain_host = your_domain
```

- conf/frp/frpc.ini
```ini
# change it to a random strings
token = token
# change these two item
admin_user = username
admin_pwd = password
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
      - SUBMISSION_WEBHOOK_URL=[url]
      - WEBHOOK_SESSION_TOKEN=[token]
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

  db:
    image: mariadb:10.11
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
    # This command is required to set important mariadb defaults
    command: [mysqld, --character-set-server=utf8mb4, --collation-server=utf8mb4_unicode_ci, --wait_timeout=28800, --log-warnings=0]

  cache:
    image: redis:4
    restart: always
    volumes:
    - ./data/redis:/data
    networks:
      internal:

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
      frp_connect:

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
      frp_containers:
      frp_connect:

networks:
  default:
  internal:
    internal: true
  frp_connect:
    internal: true
    attachable: true
    driver: overlay
  frp_containers:
    attachable: true
    driver: overlay
```

# Start
- start
```shell
sed -i "s/\r//g" docker-entrypoint.sh
docker swarm init
docker node update --label-add name=linux-1 $(docker node ls -q)
docker compose up -d
```

- ctfd-whale config
![config-1](./images/config1.png)
![config-2](./images/config2.png)
