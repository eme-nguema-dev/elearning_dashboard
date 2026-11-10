import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controller.notificaciones import ejecutar_todas_notificaciones

if __name__ == "__main__":
    ejecutar_todas_notificaciones()