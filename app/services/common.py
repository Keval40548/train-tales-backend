from datetime import datetime


def calc_elapsed_time(landing_time):
    delta = datetime.now() - landing_time
    total_seconds = delta.total_seconds()
    hours, remainder = divmod(int(total_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int((total_seconds - int(total_seconds)) * 1000)

    return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"
