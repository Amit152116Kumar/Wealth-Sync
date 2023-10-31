@echo off
docker build -t wealth-sync:1.0 .
docker run -p 8080:8080 --network bridge --env-file .\config.env wealth-sync:1.0
```