#!/usr/bin/env python3
"""BordadoStudio — inicia o programa."""

import os
import sys

# permite rodar a partir de qualquer pasta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bordadostudio.app import main

if __name__ == "__main__":
    main()
