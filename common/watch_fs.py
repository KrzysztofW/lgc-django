#!/usr/bin/python3

import time
import os
import socket
import sys
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from tcp_socket import TcpClient
from lgc_types import LGCError

DIRECTORY_TO_WATCH = "/tmp/1"
INVALID_FILE_DIR = "/tmp/bad"
DB_ERROR_FILE_DIR = "/tmp/db"
HOSTS = ("localhost", "kw-net.com")
PORT = 14376
RETRY_TIMEOUT = 5

class Watcher:
    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        event_handler.handle_queued_files()

        self.observer.schedule(event_handler, DIRECTORY_TO_WATCH,
                               recursive=False)
        self.observer.start()
        try:
            while True:
                if event_handler.working == False:
                    event_handler.handle_queued_files()
                time.sleep(RETRY_TIMEOUT)
        except:
            self.observer.stop()
            print("Observer error")

        self.observer.join()

class Handler(FileSystemEventHandler):
    working = False
    ls_in_progress = False

    def __init__(self):
        self.sock = TcpClient()
        self.handle_queued_files()

    def handle_queued_file(self, queued_file):
        res = LGCError.OK
        try:
        #while True:
            f = open(queued_file, "r")
            data = f.read()
            f.close()
            self.sock.sock_connect(HOSTS)
            self.sock.sock_send(data)
            res = self.sock.sock_receive().decode()
            if res == LGCError.OK:
                os.remove(queued_file)
            elif res == LGCError.INVALID_DATA:
                # XXX append timestamp to the new file's name
                os.rename(queued_file, os.path.join(INVALID_FILE_DIR,
                                                    os.path.basename(queued_file)))
            elif res == LGCError.DB_ERROR:
                os.rename(queued_file, os.path.join(DB_ERROR_FILE_DIR,
                                                    os.path.basename(queued_file)))
        except OSError as e:
            print("OS Exception: %s" % e)
            return -1
        except Exception as e:
            print("Runtime exception occured:", e)
            return -1
        finally:
            if (res != LGCError.OK):
                print("got error:", res)
            self.sock.sock_close()
        return 0

    def handle_queued_files(self):
        self.ls_in_progress = True
        for fq in os.listdir(DIRECTORY_TO_WATCH):
            queued_file = os.path.join(DIRECTORY_TO_WATCH, fq)
            if self.handle_queued_file(queued_file) < 0:
                break;
        self.ls_in_progress = False

    def on_any_event(self, event):
        if event.is_directory:
            return None

        #elif event.event_type == 'created':
        #    # Take any action here when a file is first created.
        #    print("Received created event - %s." % event.src_path)

        elif event.event_type == 'modified':
            if self.ls_in_progress:
                return
            self.working = True
            self.handle_queued_file(event.src_path)
            self.working = False

            # Taken any action here when a file is modified.
            #print("Received modified event - %s." % event.src_path)

        #elif event.event_type == 'deleted':
        #    # Taken any action here when a file is modified.
        #    print("Received deleted event - %s." % event.src_path)

if __name__ == '__main__':
    w = Watcher()
    w.run()

