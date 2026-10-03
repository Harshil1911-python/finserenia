# =============================================================
# SERENIA ACCOUNTING — Procfile
# Used by Heroku-style platforms. Render uses render.yaml instead,
# but this is kept for portability.
# =============================================================

web: cd backend && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120
worker: cd backend && celery -A config worker -l info -Q default,reports,payroll,notifications
beat: cd backend && celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
release: cd backend && python manage.py migrate && python manage.py seed_initial_data
