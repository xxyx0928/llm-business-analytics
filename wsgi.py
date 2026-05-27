#!/usr/bin/env python3
import os
from app import app

# Vercel需要这个变量
application = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
