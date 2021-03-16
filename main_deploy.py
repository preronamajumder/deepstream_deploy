import os
from multiprocessing import Process
from deepstream_all_save_images import deepstream_main
import time
import json
import cv2


def check_files():
    if os.path.exists(os.path.join("check", "trigger.txt")):
        os.remove(os.path.join("check", "trigger.txt"))
        return "trigger"
    elif os.path.exists(os.path.join("check", "quit.txt")):
        os.remove(os.path.join("check", "quit.txt"))
        return "quit"
    else:
        return None

def gstreamer_pipeline(
    sensor_id=0,
    sensor_mode=3,
    capture_width=640,
    capture_height=480,
    display_width=640,
    display_height=480,
    framerate=15,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=%d sensor-mode=%d ! "
        "video/x-raw(memory:NVMM), "
        "width=(int)%d, height=(int)%d, "
        "format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            sensor_mode,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

def check_feed(src_type, src):
    if src_type == "mipi":
        cap = cv2.VideoCapture(gstreamer_pipeline(sensor_id=src), cv2.CAP_GSTREAMER)
    else:
        cap = cv2.VideoCapture(src)
    while True:
        ret, frame = cap.read()
        break
    print(src_type, src, ret)
    return ret

def camera_check(config):
    source_type = config["source_type"]
    if source_type == "rtsp":
        sources = config["source"]
        camera_ok = []
        for stream, rtsp in sources.items():
            camera_ok.append(check_feed("rtsp", rtsp))
    elif source_type == "usb":
        camera_ok = [check_feed("usb", 0)]
    elif source_type == "mipi":
        camera_ok = [mipi_check("mipi", 0)]
    if all(camera_ok):
        with open("check/trigger.txt", "w") as f:
            f.write("")

def read_config(config_file):
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            print(config)    

        if len(list(config)) == 0:
            print("No configurations provided in json file")
            return None

        src = ["rtsp", "mipi", "usb"]
        source_type = config["source_type"]
        if source_type not in src:
            print("Wrong source type")
            return None
        if source_type == "rtsp":
            sources = config["source"]
            if len(list(sources)) == 0:
                print("No source provided in json file")
                return None
            for key, value in sources.items():
                if value == "":
                    print("No source provided in json file")
                    return None
        display = config["display"]
        if not isinstance(display, bool):
            print("wrong value for 'display' in json file. Valid usage is 'display': true or 'display': false")
            return None
        MUXER_OUTPUT_WIDTH = config["processing_width"]
        if type(MUXER_OUTPUT_WIDTH)!=type(1):
            print("wrong value for 'processing_width' in json file. Should be integer. eg. 640")
            return None
        MUXER_OUTPUT_HEIGHT = config["processing_height"]
        if type(MUXER_OUTPUT_HEIGHT) != type(1):
            print("wrong value for 'processing_height' in json file. Should be integer. eg. 480")
            return None
        TILED_OUTPUT_WIDTH = config["tiler_width"]
        if type(TILED_OUTPUT_WIDTH)!=type(1):
            print("wrong value for 'tiler_width' in json file. Should be integer. eg. 640")
            return None
        TILED_OUTPUT_HEIGHT = config["tiler_height"]
        if type(TILED_OUTPUT_HEIGHT) != type(1):
            print("wrong value for 'tiler_height' in json file. Should be integer. eg. 480")
            return None
        image_timer = config["image_timer"]
        if type(image_timer) != type(1):
            print("wrong value for 'image_timer' in json file. Should be integer. eg. 600")
            return None
        queue_size = config["queue_size"]
        if type(queue_size) != type(1):
            print("wrong value for 'queue_size' in json file. Should be integer and greater than 0. e.g. 20")
            return None
        else:
            if queue_size < 1:
                print("'queue_size' cannot be 0 or less. Switching to default value 20.")
                queue_size = 20
                time.sleep(5)

        return config

    except Exception as e:
        print(e)
        print("Error in json file")
        return None

def terminate_process(running_process):
    for process in running_process:
        if process.is_alive():
            print("Terminating deepstream")
            time.sleep(3)
            process.terminate()
        process.join()
        running_process.remove(process)
    return running_process

def check_process(running_process):
    for process in running_process:
        if not process.is_alive():
            process.terminate()
            process.join()
            running_process.remove(process)
    return running_process

def main():

    running_process = []
    start = True
    while True:

        if start:
            start = False
            config = read_config("config.json")
            if config is None:
                continue
            camera_check(config)
                
        status = check_files()
        if status == "trigger":
            print("trigger found")
            time.sleep(3)
            
            config = read_config("config.json")
            if config is None:
                continue

            running_process = terminate_process(running_process)
            print("Starting Deepstream")
            time.sleep(3)
            p = Process(target=deepstream_main, args=(config,))
            p.start()
            running_process.append(p)

        if status == "quit":
            print("quit found")
            time.sleep(3)
            running_process = terminate_process(running_process)

        # if status is None:
        #     for process in running_process:
        #         if not process.is_alive():
        #             print("No files found")
            

        print("running processes: ", len(running_process))
        running_process = check_process(running_process)

        time.sleep(1)
            

if __name__ == "__main__":
    main()