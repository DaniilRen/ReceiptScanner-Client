import os
import sys
import datetime
import re
import flet as ft
import base64

""" Encode file to base64 string"""
def encode_base64(file_path):
	with open(file_path, "rb") as f:
		return base64.b64encode(f.read()).decode("utf-8")


""" Decode base64 string to binary """ 
def decode_base64(b64_string):
	if ',' in b64_string:
		b64_string = b64_string.split(',')[1]
	try:
		img_bin = base64.b64decode(b64_string)
	except Exception as e:
		print(f"Exception while enconding base64 data: {e}")
		return None 
	return img_bin


""" Clamp size of frame with proportions """
def clamp_shape(shape, target_size=600):
	width, height = shape[1], shape[0]
	if width >= height:
		return (int(height*target_size/width), target_size)
	else:
		return (target_size, int(width*target_size/height))
	

""" Добавление файла """
def upload_file_base64(b64_string, path):
	img_bin = decode_base64(b64_string)
	if img_bin is None:
		return False
	with open(path, 'wb') as f:
		f.write(img_bin)
	return True


""" Convert sql date to text format """
def date_to_text(date: str) -> str:
	dt = datetime.datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %Z')
	return dt.strftime('%d.%m.%Y')\
	

""" Check and convert date from textfields to valid sql date format """
def date_to_sql(date: str):
	try:
		d, m, y = date.strip().replace(':', '-').replace('.', '-').split('-')
		date = f"{y}-{m}-{d}"
		if not re.fullmatch(r'^\d{4}-(0?[1-9]|1[0-2])-(0?[1-9]|[12]\d|3[01])$', date):
			return None
		return date
	except Exception:
		return None



""" Utils for file attachment """

""" 
Update page data for storing attached file.
attachment: screenshot / picked
"""
def update_attachment_data(self, path, name, base64, attachment):
	if attachment == "screenshot" and self.file_path != None:
		os.remove(self.file_path)
		print("Attached file buffer is not empty. File has been replaced")
	self.file_path = path
	self.file_name_text.value = f"Выбран файл: {name}"
	self.frame_base64 = base64


def pick_file(self, e):
	self.file_picker.pick_files(
			allow_multiple=False,
			allowed_extensions=["png", "jpg", "jpeg"]
	)


def file_picked(self, e: ft.FilePickerResultEvent):
	if e.files:
		file = e.files[0]
		update_attachment_data(self, file.path, file.name, encode_base64(file.path), "picked")
		self.file_name_text.value = f"Выбран файл: {file.name}"
	else:
		update_attachment_data(self, None, "Файл не выбран", None, "picked")
		self.submit_button.disabled = True
	self.update()


""" Alert dialog handlers """
def show_dialog(self, text="", desc=""):
	self.page.dialog.title.content.value = text
	self.page.dialog.content.value = desc
	self.page.open(self.page.dialog)
	self.page.update()
	print("Dialog opened")

def close_dialog(self):
	self.page.close(self.page.dialog)
	self.page.update()
	print("Dialog closed")


def get_filtered_items(items, start, end, category):
	try:
		if start == end == "all":
			return [r for r in items if r["category"] == category]
		elif category == 'all':
	
			return [r for r in items if start <= date_to_sql(date_to_text(r["creation_date"])) <= end]
		else:
			return [r for r in items if r["category"] == category and \
				start <= date_to_sql(date_to_text(r["creation_date"])) <= end]
	except Exception as e:
		print(e)
		return None