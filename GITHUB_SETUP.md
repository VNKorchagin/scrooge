# GitHub и CI/CD Настройка

## 1. Создание репозитория на GitHub

```bash
# Добавьте remote (замените на ваш репозиторий)
git remote add origin https://github.com/VNKorchagin/scrooge.git

# Сделайте первый коммит
git add .
git commit -m "Initial commit: Scrooge budget tracker"

# Push на GitHub
git branch -M main
git push -u origin main
```

## 2. Настройка GitHub Secrets

В репозитории перейдите в **Settings → Secrets and variables → Actions** и добавьте:

| Secret | Описание | Пример |
|--------|----------|--------|
| `SSH_PRIVATE_KEY` | Приватный SSH ключ для доступа к серверу | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `SERVER_HOST` | IP или домен сервера | `192.168.1.100` или `scrooge.example.com` |
| `SERVER_USER` | SSH пользователь | `root` или `ubuntu` |
| `SSH_PORT` | SSH порт (опционально, по умолчанию 22) | `22` |
| `DEPLOY_PATH` | Путь к проекту на сервере | `/opt/scrooge` |
| `DB_PASSWORD` | Пароль базы данных | `your-secure-password` |
| `SECRET_KEY` | JWT секрет | `your-super-secret-key` |

## 3. Подготовка сервера

### 3.1 Создание SSH ключа

На вашем локальном компьютере:
```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions
# Не устанавливайте пароль (нажмите Enter дважды)
```

Скопируйте публичный ключ на сервер:
```bash
ssh-copy-id -i ~/.ssh/github_actions.pub user@your-server
```

Содержимое приватного ключа (`~/.ssh/github_actions`) вставьте в GitHub Secret `SSH_PRIVATE_KEY`.

### 3.2 Настройка сервера

На сервере выполните:

```bash
# Установите Docker и Docker Compose (если не установлены)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Добавьте пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker

# Создайте директорию для проекта
sudo mkdir -p /opt/scrooge
sudo chown $USER:$USER /opt/scrooge

# Клонируйте репозиторий
cd /opt/scrooge
git clone https://github.com/VNKorchagin/scrooge.git .

# Создайте .env файл
cat > .env << EOF
DB_PASSWORD=your-secure-db-password
SECRET_KEY=your-super-secret-jwt-key-$(openssl rand -hex 32)
EOF
```

### 3.3 Первый запуск

```bash
cd /opt/scrooge
docker-compose up -d --build
docker-compose exec backend alembic upgrade head
```

## 4. Проверка CI/CD

После настройки secrets, любой push в `main` ветку автоматически:
1. Подключится к серверу по SSH
2. Выполнит `git pull`
3. Пересоберёт контейнеры
4. Применит миграции
5. Покажет статус деплоя

Проверьте в разделе **Actions** вашего репозитория.

## 5. Ручной деплой (если CI/CD не работает)

```bash
# На сервере
cd /opt/scrooge
./deploy.sh
```

## Безопасность

1. **Никогда не коммитьте** `.env` файл с реальными секретами
2. Используйте сложные пароли и ключи
3. Ограничьте доступ к серверу по IP (в файрволе)
4. Регулярно обновляйте Docker образы

## Troubleshooting

### Ошибка доступа по SSH
```bash
# На сервере проверьте права
ls -la ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

### Контейнеры не перезапускаются
```bash
# На сервере
docker-compose down
docker system prune -f
docker-compose up -d --build
```

### Ошибка миграций
```bash
# На сервере
docker-compose exec backend alembic current
docker-compose exec backend alembic history
```
