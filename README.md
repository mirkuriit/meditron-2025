# meditron-2025
Sechenov x MISIS

Сервис для оптимизации дозировок препаратов противоопухолеовой терапии рака молочной железы.

## Backend   
Стек используемых технологий:
- python
- FastAPI - фреймворк для разработки высоконагруженных api
- Docker - инстурмент для контейнеризации и изолированной развертки приложения

### Сборка и запуск

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
  

__build & run__
```shell
cd backend
docker build -t meditron-api .
 
docker run --rm -p ${FASTAPI_PORT}:${FASTAPI_PORT} -e FASTAPI_PORT=${FASTAPI_PORT} meditron-api

### Или указать явно

docker run --rm -p 8010:8010 -e FASTAPI_PORT=8010 meditron-api
```
свагер с описанием ручек будет доступен по адресу `http://host:FASTAPI_PORT/meditron-api/docs`

(host = localhost) если собрано локально

## Frontend
Стек используемых технологий:
- html
- css
- javascript
- nginx - веб-сервер для раздачи статических файлов
- Docker - инстурмент для контейнеризации и изолированной развертки приложения

### Сборка и запуск

Склонировать репозиторий  
```shell
git clone git@github.com:mirkuriit/meditron-2025.git
```

```
cd med_front_ai
```

__build & run__ example
```
docker build -t meditron-frontend .
docker run -p 8000:80 meditron-frontend
```

### CORS 

Для корректного взаимодействия между бекендом и фронтендом часто приходится настраивать cors. В проекте они находятся по пути
`meditron-2025/backend/src/main.py`

```Python

...
fastapi_app.add_middleware(
    CORSMiddleware,
    ### Разрешенные фронтенду адреса
    allow_origins=['http://localhost:8000', 'http://localhost:63342', 'http://localhost:5500', 'http://89.169.174.45:8000'],
    ...
)
...
```

## ML 

Стек используемых технологий

- sklearn - библиотека машинного обучения
- pandas - библиотека для анализа и предобработки данных
- matplotlib - библиотека для отрисовки графиков

Используемая модель - __CoxPHFitter__ (Регрессионная модель кокса)

### Pipline

#### EDA -> DATA PREPROCESSING -> KaplCoxPHFitteranMeierFitter

## Math Models

см [README.md](https://github.com/mirkuriit/meditron-2025/blob/main/math_model/README.md)