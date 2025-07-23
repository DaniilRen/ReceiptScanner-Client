import cv2 as cv
import base64


""" 
Class for capturing frames from camera
creates opencv VideoCapture object and gets frams from it
src - video source (0/-1 = device camera)
"""
class Stream():
	def __init__(self, src=0):
		self.create_stream(src)
		self.frame_shape = None

	def get_frame_raw(self):
		if not self.available:
			return False
		ret, frame = self.cap.read()
		if not ret:
			return False
		return frame

	def to_base64(self, frame):
		_, buffer = cv.imencode('.jpg', frame)
		return base64.b64encode(buffer).decode('utf-8')

	# frame in base64 encoding
	def get_frame(self):
		return self.to_base64(self.apply_filter(self.get_frame_raw()))

	def release(self):
		if self.available:
			self.cap.release()
			self.available = False

	def create_stream(self, src=0):
		self.cap = cv.VideoCapture(src)
		self.available = self.cap.isOpened()

	def apply_filter(self, src):
		self.frame_shape = (640, 360)
		frame = cv.cvtColor(src, cv.COLOR_BGR2HSV)
		frame = frame[120:480, 0:640]
		
		mask = cv.inRange(frame, (0, 0, 120), (255, 255, 255))

		gaussian = cv.GaussianBlur(frame, (0, 0), 2.0)
		frame = cv.addWeighted(frame, 2.0, gaussian, -1.0, 0)

		frame = cv.bitwise_and(frame, frame, mask=mask)
		frame = cv.rotate(frame, cv.ROTATE_90_CLOCKWISE)
		frame = cv.cvtColor(frame, cv.COLOR_HSV2BGR)
		return frame
	