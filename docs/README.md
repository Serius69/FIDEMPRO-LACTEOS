# Findempro - Sistema de Apoyo a Decisiones Financieras

Sistema web para apoyo en la toma de decisiones financieras dirigido a PYMES del sector lácteo.

## Características

- 📊 Análisis probabilístico de demanda
- 🔄 Simulación de escenarios financieros
- 📈 Dashboard interactivo
- 🔐 Autenticación con Google OAuth
- 📱 Diseño responsive

## Tecnologías

- **Backend**: Django 4.2.11
- **Frontend**: Bootstrap 5, jQuery
- **Base de datos**: MySQL 8.0
- **Cache**: Redis
- **Task Queue**: Celery
- **Contenedores**: Docker

## Instalación Rápida

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/findempro.git
cd findempro
venv\Scripts\activate
cd requirements
pip install -r development.tx
cd ..

python manage.py makemigrations
python manage.py migrate

python manage.py runserver
