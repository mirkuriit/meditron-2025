# meditron-2025
Sechenov x MISIS

Сервис для оптимизации дозировок препаратов противоопухолеовой терапии рака молочной железы.

## Backend   
Стек используемых технологий:
- python
- FastAPI - фреймворк для разработки высоконагруженных api
- Docker - инстурмент для контейнеризации и изолированной развертки приложения

## Сборка и запуск

Склонировать репозиторий
```shell
git clone git@github.com:mirkuriit/meditron-2025.git
```

Установить переменные окружения

```shell
cp example.env .env
set -a
source .env
set +a
```  
  

build & run 
```shell
cd backend
docker build -t meditron-api .
 
docker run --rm -p ${FASTAPI_PORT}:${FASTAPI_PORT} -e FASTAPI_PORT=${FASTAPI_PORT} meditron-api

### Или указать явно

docker run --rm -p 8010:8010 -e FASTAPI_PORT=8010 meditron-api
```
свагер с описанием ручек будет доступен по адресу `http://host:FASTAPI_PORT/meditron-api/docs`

(host = localhost) если собрано локально


## Сборка
```
docker build -t mirkuriit/meditron-api:1 .
docker run --rm -p 8006:8006 -e FASTAPI_PORT=8006  mirkuriit/meditron-api:1
```