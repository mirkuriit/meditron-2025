# meditron-2025
Sechenov x MISIS

## Сборка
```
docker build -t mirkuriit/meditron-api:1 .
docker run --rm -p 8006:8006 -e FASTAPI_PORT=8006  mirkuriit/meditron-api:1
```