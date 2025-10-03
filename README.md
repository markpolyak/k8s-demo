# k8s-ml-demo
Материалы для семинара по Kubernetes

---

##  Структура репозитория

```
k8s-ml-demo/
├── README.md                          # Этот файл
├── student/                           # Материалы для слушателей
│   ├── student-guide.pdf              # Руководство для слушателей
│   ├── homework-assignment.pdf        # Практическое задание
├── app/                               # Исходный код ML API
│   ├── main.py                        # FastAPI приложение
│   ├── requirements.txt               # Python зависимости
│   └── Dockerfile                     # Dockerfile для сборки образа
├── k8s/                               # Kubernetes манифесты
│   ├── postgres-deployment.yaml       # PostgreSQL
│   ├── redis-deployment.yaml          # Redis
│   ├── ml-api-deployment.yaml         # ML API Service
│   └── ml-api-hpa.yaml                # HorizontalPodAutoscaler
└── docker-compose.yml                 # Для сравнения с K8s
```

## Инструкция

1. **Установите ПО** (следуйте `student-guide.pdf`):
   - Docker Desktop
   - Minikube
   - kubectl

2. **Запустите Minikube**:
   ```bash
   minikube start --memory=4096 --cpus=2
   ```

3. **Выполните домашнее задание** (`homework-assignment.pdf`):
   - Создайте простое ML приложение
   - Разверните в Kubernetes
   - Настройте автомасштабирование
   - Напишите отчет

4. **Полезные ресурсы** (см. `student-guide.pdf`):
   - Официальная документация Kubernetes
   - Интерактивные туториалы
   - Видео курсы
   - Сообщества для помощи

---

## Системные требования

### Минимальные:
- **CPU:** 2 ядра
- **RAM:** 8 GB (4 GB для Minikube + 4 GB для системы)
- **Диск:** 20 GB свободного места
- **ОС:** Windows 10/11, macOS 10.14+, Linux (Ubuntu 20.04+)

### Рекомендуемые:
- **CPU:** 4 ядра
- **RAM:** 16 GB
- **Диск:** 40 GB SSD
- **Интернет:** Стабильное соединение для загрузки образов

---

## Полезные ссылки

### Документация:
- [Kubernetes Official](https://kubernetes.io/docs/home/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)

### Интерактивное обучение:
- [Play with Kubernetes](https://labs.play-with-k8s.com/)
- [KillerCoda K8s Scenarios](https://killercoda.com/kubernetes)
- [Kubernetes Tutorial](https://kubernetes.io/docs/tutorials/)

### Инструменты:
- [k9s](https://k9scli.io/) - терминальный UI
- [Lens](https://k8slens.dev/) - desktop IDE
- [Helm](https://helm.sh/) - пакетный менеджер

---

## Troubleshooting

### Проблема: Minikube не запускается

**Windows:**
```powershell
# Проверьте Hyper-V или включите WSL 2
minikube start --driver=hyperv
# или
minikube start --driver=docker
```

**macOS/Linux:**
```bash
# Попробуйте другой драйвер
minikube start --driver=docker
# или
minikube start --driver=virtualbox
```

### Проблема: ImagePullBackOff в подах

```bash
# Проверьте, что образ существует
docker search YOUR_USERNAME/ml-api

# Проверьте имя образа в манифесте
kubectl describe pod <pod-name>

# Загрузите образ вручную в Minikube
minikube ssh docker pull YOUR_USERNAME/ml-api:v1
```

### Проблема: Metrics server не работает

```bash
# Переустановите addon
minikube addons disable metrics-server
minikube addons enable metrics-server

# Подождите 1-2 минуты
kubectl top nodes
```

---

## Дополнительные материалы

### Для углубленного изучения:

**Книги:**
- "Kubernetes in Action" by Marko Lukša
- "The Kubernetes Book" by Nigel Poulton
- "Kubernetes Patterns" by Bilgin Ibryam

**Онлайн курсы:**
- [Kubernetes Fundamentals (Linux Foundation)](https://training.linuxfoundation.org/training/kubernetes-fundamentals/)
- [Kubernetes for Developers (Udemy)](https://www.udemy.com/course/kubernetes-for-developers/)

**Сертификации:**
- [CKA - Certified Kubernetes Administrator](https://www.cncf.io/certification/cka/)
- [CKAD - Certified Kubernetes Application Developer](https://www.cncf.io/certification/ckad/)
