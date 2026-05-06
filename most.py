#!/usr/bin/env python3
"""most.py — запуск моста ReplitTermux. python most.py"""
import sys, os
# Добавляем папку с most.py в путь, чтобы импорты внутри пакета работали
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import main
main()
