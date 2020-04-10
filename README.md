# Rabbit Ws
## Необходимый софт
* Docker
* Docker-compose

## Установка
В файл .env нужно пробросить такие параметры среды:
* RABBITMQ_DEFAULT_HOST
* RABBITMQ_DEFAULT_USER
* RABBITMQ_DEFAULT_PASS
* MYSQL_HOST
* MYSQL_DATABASE
* MYSQL_USER
* MYSQL_PASSWORD
* SECRET_KEY

SECRET_KEY используется для JWT авторизации. Это секретный ключ, которым подписываются токены.
Для теста, можете использовать мой сервис, для этого в SECRET_KEY, можна поставить значение: 
**1p66ish3%#defzp!6w-))$8=0oc8#FDJAKLJifofweqopru123**

Чтобы залогиниться, можно перейти по ссылке: https://yochered.pythonanywhere.com/api/login/

И там ввести логин: **test**
            пароль: **123123ff**
            
И затем при подключении к веб-сокетам прокинуть access_token в cookie.
## Запуск
Из корня проекта:
```
docker-compose up -d

Флаг -d позволяет запустить сервер в фоновом режиме
```

## Дефолтный порт ```8888```
Можно изменить в docker-compose.yml файле

## Просмотр логов
```
docker-compose logs
```