import os
import sys
# ensure project root is on sys.path so `import Forneria` works when this script
# is executed from the `tools/` directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Forneria.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
username = 'testadmin'
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, 'test@example.com', 'TestPass123!')
    print('CREATED')
else:
    print('EXISTS')
