import os
from multiprocessing import Process
from deepstream_all_save_images import deepstream_main
import time
import json


def check_files():
    if os.path.exists(os.path.join("config", "trigger.txt")):
        os.remove(os.path.join("config", "trigger.txt"))
        return "trigger"
    elif os.path.exists(os.path.join("config", "quit.txt")):
        os.remove(os.path.join("config", "quit.txt"))
        return "quit"
    else:
        return None

def read_config(config_file):
    try:
        with open(os.path.join("config", "config.json"), "r") as f:
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
    while True:
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