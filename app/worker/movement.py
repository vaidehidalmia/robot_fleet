import math

from app.worker.config import STEP_SIZE, ARRIVAL_THRESHOLD

def move_toward(current_x, current_y, target_x, target_y):
    dx = target_x - current_x
    dy = target_y - current_y
    distance = math.hypot(dx, dy)

    if distance < ARRIVAL_THRESHOLD:
        return distance, target_x, target_y, True  # arrived

    ratio = STEP_SIZE / distance
    new_x = current_x + dx * ratio
    new_y = current_y + dy * ratio

    return STEP_SIZE, new_x, new_y, False