import grpc
import random
from FeatureExtractionApi_pb2 import Image
import FeatureExtractionApi_pb2_grpc
import time
from datetime import datetime
#import cv2
import sys
import picamera
import io
def generate_videos_iterator(mode,filename):
    #img = cv2.imread('images.jpg')
    #cap = cv2.VideoCapture(0)
    if mode == 1:
        while True:
            ret, frame = cap.read()
            bytesImg= cv2.imencode(".jpg",frame)[1].tostring()
           # cv2.imshow('frame',frame)
            print ("Enviando ... ")
            yield FeatureExtractionApi_pb2.Image(source=bytesImg,file_name=filename)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()

    if mode == 0:
        camera = picamera.PiCamera()
	#camera.resolution = (640,480)
        camera.resolution = (1296,972)
	#camera.resolution = (2592,1944)
        #camera.resolution = (1280,720)
        #camera.framerate = 5
        camera.hflip = True
        camera.vflip = True
        camera.saturation = -60
        camera.brightness = 60
        time.sleep(10)
    try:
        stream = io.BytesIO()
        count = 1
        start = time.time()
        # Use the video-port for captures...
        for foo in camera.capture_continuous(stream, 'jpeg',use_video_port=True):
            print("New frame: #",count)
            stream.seek(0)
            yield Image(source=stream.read(), file_name=filename, timestamp = str(datetime.now()))
            #if time.time() - start > 20:
            #     break
            stream.seek(0)
            stream.truncate()  
            count += 1
    finally:
        pass

	#for _ in range(0, 10):
	#	yield Image(source="hola",file_name=filename)
    		#time.sleep(random.uniform(0.5, 1.5))

def runClient(mode,filename):
    channel = grpc.insecure_channel('200.126.23.95:50052')
    stub = FeatureExtractionApi_pb2_grpc.FeatureExtractionStub(channel)
    videos_iterator = generate_videos_iterator(mode,filename)
    response = stub.processVideo(videos_iterator)
    print (response)


if __name__ == '__main__':
    print (sys.argv)
    runClient(0, "cam.txt")
    # if len(sys.argv) >= 0:
    #     if sys.argv[1] == "raspicam":
    #         mode = 0
    #     elif sys.argv[1] == "usb":
    #         mode = 1
    #     else:
    #         print ('Invalid mode: (raspicam o usb)')
    #         sys.exit(2)
    #     fileName = sys.argv[2]
    #     mode = 0
    #     fileName = "cam3"
    #     runClient(mode,fileName)
    # else:
    #     print ('Invalid arguments')
    #     sys.exit(2)

#video()
