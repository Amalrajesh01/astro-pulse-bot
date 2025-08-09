from datetime import datetime

def get_current_phase():
    current_month = datetime.now().month
    if 1 <= current_month <= 3:
        return 'phase_1'
    elif 4 <= current_month <= 6:
        return 'phase_2'
    elif 7 <= current_month <= 9:
        return 'phase_3'
    else:
        return 'phase_4'
