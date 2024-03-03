gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout=0 student_activity.wsgi:application & 
python -m celery -A student_activity worker -l info & 
python -m celery -A student_activity beat -l info &  
python manage.py consumer

# Run this commands sepratly in the ECS services.