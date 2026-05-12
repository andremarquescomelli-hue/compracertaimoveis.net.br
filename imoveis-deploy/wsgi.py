import sys
import os

path = '/home/SEU_USERNAME/imoveis-crm'
if path not in sys.path:
    sys.path.insert(0, path)

os.chdir(path)

from app import app as application
