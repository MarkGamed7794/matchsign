import multiprocessing, os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide" # I shouldn't have to do this, and yet here we are

import data_request, led.display, constants
from led.draw_lib import MatrixDraw

def main():
    conn_recieve, conn_send = multiprocessing.Pipe(True)

    # Remove any cached data
    if(os.path.isfile(constants.TBA_CACHE_FILEPATH)):
        os.remove(constants.TBA_CACHE_FILEPATH)
        with open(constants.TBA_CACHE_FILEPATH, "w") as cache:
            cache.write("")

    draw_process = multiprocessing.Process(target=led.display.main, args=[conn_recieve])
    draw_process.start()
    print(f"[MAIN] Draw process started. PID={draw_process.pid}")

    request_process = multiprocessing.Process(target=data_request.main, args=[conn_send])
    request_process.start()
    draw_process.join()
    request_process.kill()

if __name__ == "__main__":
    main()