import random
import io
import os
import threading
import time
import sys
from datetime import datetime
from Queue import Queue, Empty
import grpc
from FeatureExtractionApi_pb2 import Image
import FeatureExtractionApi_pb2_grpc
import cv2
#from picamera import PiCamera
#from picamera.exc import PiCameraMMALError, PiCameraError
from datetime import datetime
FPS = 15
SERVER_URL = '200.126.23.95:50052'
"""
resultados: grabando 60s a res 640x480
Tiempo adicional que tarda en terminar de enviar todos los frames capturados
~ 10FPS: 1:47
~ 15FPS: 3:08
~ 30FPS: 440 secs
~ 5: 30 secs
"""

class VideoRecorder:

    def __init__(self):
        "docstring"
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            raise IOError("Error al reconocer la camara USB")
        self.set_camera_params()
        # print self.camera.get(cv2.CAP_PROP_FRAME_WIDTH), self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        # channel = grpc.insecure_channel('200.126.23.95:50052')
        # self.grpc_stub = FeatureExtractionApi_pb2_grpc.FeatureExtractionStub(channel)
        self.recording_stop = True
        self.image_queue = Queue()
        self.count = 0
        self.sent_count = 0
        self.grabbing = False

    def set_camera_params(self):
        # self.camera.set(3,1296)
        # self.camera.set(4,972)
        self.camera.set(3, 640)
        self.camera.set(4, 480)

    def capture_continuous(self, filename):
        self.count = 1
        self.grabbing = True
        while True:
            start = time.time()
            ret, frame = self.camera.read()
            #frame=cv2.flip(frame,0)
            bytesImg= cv2.imencode(".jpg",frame)[1].tostring()
            self.image_queue.put(Image(source=bytesImg,file_name=filename,timestamp=str(datetime.now())))
            if self.recording_stop:
                break
            # time.sleep(0.09)#~10.18 secs
            # time.sleep(0.18)# ~ 5.3 secs
            # time.sleep(0.05) # ~ 16.6 secs
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            # print self.count
            self.count += 1
            time.sleep(max(1./FPS - (time.time() - start), 0))
        self.grabbing = False

    def generate_videos_iterator(self):
        self.sent_count = 0
        while not self.recording_stop or not self.image_queue.empty() or self.grabbing:
            try:
                yield self.image_queue.get(block=True, timeout=1)
                self.image_queue.task_done()
                print "sent",self.sent_count, "of", self.count, "captured"
                self.sent_count += 1
            except Empty as ex:
                print ("No data in image queue")
        print ("Done generating images")

    def start_recording(self, filename):
        try:
            channel = grpc.insecure_channel(SERVER_URL)
            if not self.ping(channel):
                raise
            self.grpc_stub = FeatureExtractionApi_pb2_grpc.FeatureExtractionStub(channel)
            threading.Thread(target=self.capture_continuous, args=(filename, )).start()
            videos_iterator = self.generate_videos_iterator()
            response = self.grpc_stub.processVideo(videos_iterator)
            print(response)
        except:
            print ("GRPC")

    def ping(self, channel=None):
        if channel is None:
            channel = grpc.insecure_channel('200.126.23.95:50052')
        try:
            grpc.channel_ready_future(channel).result(timeout=1)
            return True
        except grpc.FutureTimeoutError as e:
            print ("Couldnt connect to GRPC SERVER")
            return False


    def record(self, filename):
        self.recording_stop = False
        self.image_queue = Queue()
        threading.Thread(target=self.start_recording, args=(filename, )).start()

    def stop_record(self, callback=None):
        self.recording_stop = True
        time.sleep(5)
        self.image_queue.join()
        if callback:
            callback()


    def get_progress(self):
        try:
            return "{} %".format(int(self.sent_count * 100.0 / self.count))
        except:
            return "0 %"
        # return "{}/{}".format(self.sent_count, self.count)

    def clean(self):
        self.camera.release()
        print ("Camera released")
        # self.camera.close()

    def calc_fps(self, time_elapsed):
        return self.count / time_elapsed.total_seconds()



if __name__ == "__main__":
    vid_recorder = VideoRecorder()
    print ("Set vid recorder")
    # vid_recorder.camera.wait_recording(5)
    time.sleep(2)
    start = datetime.now()
    print("Start" , str(start.time()))
    print(start)
    vid_recorder.record("test")
    print("*Recording")
    #raw_input()
    time.sleep(60)
    stop_recording = datetime.now()
    recording_time = stop_recording - start
    vid_recorder.stop_record()
    print("RECORDING TIME", str(recording_time))
    fps = vid_recorder.calc_fps(recording_time)
    print("FPS:", fps)
    time_sending = datetime.now() - stop_recording
    print("Time needed to send", str(time_sending))

    vid_recorder.clean()

# RESULTS
