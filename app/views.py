import flet as ft
import lib.controls as controls
import lib.utils as utils
from lib.stream import Stream
from lib.timer import Timer
import requests
import json
import os
import urllib.parse
import datetime
import cv2 as cv
import base64


""" Auth """
class LoginView(ft.View):
	def __init__(self, page: ft.Page):
		super().__init__("/login")
		self.page = page

		self.username = ft.TextField(label="Логин", width=300)
		self.password = ft.TextField(label="Пароль", width=300, password=True, can_reveal_password=True)
		self.result_text = ft.Text()
		self.login_button = ft.ElevatedButton(text="Войти", on_click=self.login_click)

		form = ft.Column(
			[
				ft.Text("Вход в систему", size=24, weight=ft.FontWeight.BOLD),
				self.username,
				self.password,
				self.login_button,
				self.result_text,
			],
			alignment=ft.MainAxisAlignment.CENTER,
			horizontal_alignment=ft.CrossAxisAlignment.CENTER,
			spacing=10,
			expand=False,
		)
		container = ft.Container(
			content=form,
			alignment=ft.alignment.center,
			expand=True,
		)

		self.controls.append(container)
	
	""" Login button handler """
	def login_click(self, e):
		credentials = {
			'username': self.username.value.strip(),
			'password': self.password.value.strip()
		}
		self.result_text.value = "Выполняется вход..."
		self.result_text.update()
		resp = requests.get(f'{self.page.ROOT_URL}/login', json=credentials)
		print(resp)
		if resp.status_code in (200, 204):
			token = resp.json()['access_token']
			self.page.current_session_username = credentials['username']
			self.page.request_headers = {'Authorization': f'Bearer {token}'}
			self.page.special_request_headers = {
				'Content-Type': 'application/json',
				'Authorization': f'Bearer {token}'
			}
			self.result_text.value = "Успешный вход!"
			self.page.go("/items")
		else:
			self.result_text.value = "Неверный логин или пароль"
		self.update()


""" Main items table with filters """
class ItemsView(ft.View):
	def __init__(self, page: ft.Page):
		super().__init__("/items")
		self.page = page

		# Info panel with items count
		self.item_count = ft.Text(value=f"Всего позиций: 0")

		# Blank table for items
		self.table = ft.DataTable(
			columns=[
				ft.DataColumn(ft.Text("Дата")),
				ft.DataColumn(ft.Text("Категория")),
				ft.DataColumn(ft.Text("Сумма")),
				ft.DataColumn(ft.Text("Фото")),
			],
			rows=[],
			expand=True
		)
		
		self.controls.append(ft.AppBar(title=ft.Text("База данных"), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST))
		self.start_filter_field = ft.TextField(label="Начальная дата")
		self.end_filter_field = ft.TextField(label="Конечная дата")
		self.category_dropdown = ft.Dropdown(
				label="Категория",
				options=[ft.dropdown.Option("", "Все")] + [ft.dropdown.Option(c["category"]) for c in self.load_categories(return_categories=True)],
				value="Все"
		)
		self.reload_button = ft.IconButton(
			icon=ft.Icons.REFRESH,
			tooltip="Reload",
			on_click=self.reset_filter
		)
		self.category_button = ft.ElevatedButton(
			"Категории", 
			icon=ft.Icons.CATEGORY, 
			on_click=lambda e: self.page.go('/category')
		)
		self.user_button = ft.ElevatedButton(
			"Пользователи", 
			icon=ft.Icons.PERSON, 
			on_click=lambda e: self.page.go('/user')
		)
		self.controls.append(
			ft.Column([
				ft.Row([
					self.category_button,
					self.user_button,
					ft.ElevatedButton(
						"Сформировать отчет", 
						on_click=self.get_report
					),
					ft.ElevatedButton(
						"Добавить объект", 
						on_click=lambda e: self.page.go('/newitem')
					),
					self.reload_button
				]),
				ft.Row([
					self.category_dropdown,
					self.start_filter_field,
					self.end_filter_field,
					ft.ElevatedButton(
						"Отфильтровать", 
						on_click=self.apply_filter
					)
				]),
			])
		),

		self.controls.append(self.item_count)
		
		self.controls.append(ft.ListView(controls=[self.table], expand=True, height=400))
		self.page.dialog = ft.AlertDialog(
			title=ft.Container(ft.Text(""), alignment=ft.alignment.center),
			content=ft.Text(""),
			actions=[
				ft.TextButton("OK", on_click=lambda e: utils.close_dialog(self))
			],
			actions_alignment=ft.MainAxisAlignment.CENTER,
		)

		self.reload_items()

	""" Add item row to table """
	def add_row(self, item):
		date_ = utils.date_to_text(item['creation_date'])

		def on_photo_click(e):
			# Setting params to show item info on click
			img_path = urllib.parse.quote(os.path.join(self.page.STORAGE_PATH, 'temp', item['file_name']))
			category = urllib.parse.quote(item['category'])
			id_ = urllib.parse.quote(str(item['id']))
			date = urllib.parse.quote(date_)
			sum_ = urllib.parse.quote(str(item['sum']))
			route = f"/detailedview?id={id_}&img={img_path}&category={category}&date={date}&sum={sum_}"
			self.page.go(route)

		self.table.rows.append(
			ft.DataRow(
				cells=[
					ft.DataCell(ft.Text(date_, selectable=True)),
					ft.DataCell(ft.Text(item['category'], selectable=True)),
					ft.DataCell(ft.Text(item['sum'], selectable=True)),
					# ft.DataCell(ft.Text(photo))
					controls.ClickableDatacell( 
						text='Посмотреть фото', 
						on_tap=on_photo_click
					)
				],
			)
		)
		self.page.update()

	""" 
	Load list of available categories from server
	return_categories (boolean) - return list of categories as result
	"""
	def load_categories(self, return_categories=False):
		resp = requests.get(f'{self.page.ROOT_URL}/categories', headers=self.page.request_headers)
		if resp.status_code in [200, 204]:
			self.page.categories = resp.json()
			if return_categories: 
				return resp.json()

	""" Load file image from server and save it to local storage """
	def load_photo(self, item):
		resp = requests.get(f"{self.page.ROOT_URL}/files/{item['id']}", headers=self.page.request_headers)
		with open(os.path.join(self.page.STORAGE_PATH, 'temp', item['file_name']), 'wb') as f:
			f.write(resp.content)

	""" Load items from buffer and add them to table """
	def reload_items(self):
		self.table.rows.clear()
		if self.page.loaded_items is None:
			self.load_all_items()
			current_items = self.page.loaded_items
		else:
			if self.page.filtered_items is None: 
				current_items = self.page.loaded_items
			else:
				current_items = self.page.filtered_items
			
			for item in current_items:
				self.add_row(item)

		self.page.update()
		self.update_count(current_items)

	""" Get list of all items from server """
	def load_all_items(self):
		resp = requests.get(f'{self.page.ROOT_URL}/item/all', headers=self.page.request_headers)
		if resp.status_code in [200, 204]:
			loaded_items = []
			for item in resp.json():
				loaded_items.append(item)
				self.load_photo(item)
			self.page.loaded_items = loaded_items
			for item in self.page.loaded_items:
				self.add_row(item)
		print("=> Loaded all items from server")

	""" Reset filter fields and updates items table """
	def reset_filter(self, e=None):
		self.start_filter_field.value = None
		self.end_filter_field.value = None
		self.category_dropdown.value = "Все"
		self.page.filtered_items = None
		self.page.loaded_items = None
		self.reload_items()
		print("=> Filter was reset")

	""" Get item filtered by date"""	
	def apply_filter(self, e):
		start = utils.date_to_sql(self.start_filter_field.value)
		end = utils.date_to_sql(self.end_filter_field.value)
		category = self.category_dropdown.value
		if start is None and end is None:
			start = "all"
			end = "all"
		if category in [None, "Все"]:
			category = "all"
		if all([start, end, category]):
			# if no filters set, load all items
			if start == end == category == "all":
				self.reset_filter() 
				return
			else:
				filtered = utils.get_filtered_items(self.page.loaded_items, start, end, category)
				if not filtered is None:
					self.page.filtered_items = filtered
					self.reload_items()
					print("=> Items table filtered")
				else:
					print("! Error while filtering items")

	""" 
	Get report from server.
	Uses filtered items, 
	otherwise returns report about all items 
	"""
	def get_report(self, e):
		if self.page.filtered_items is None:
			items = self.page.loaded_items
		else:
			items = self.page.filtered_items
		id_list = json.dumps({
			"id_list": [int(item['id']) for item in items]
		})
		resp = requests.get(f'{self.page.ROOT_URL}/report', data=id_list, headers=self.page.special_request_headers)
		print(resp)
		if resp.status_code in [200, 204]:
			filename = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.pdf'
			path = os.path.join(self.page.STORAGE_PATH, filename)
			with open(path, 'wb') as f:
				f.write(resp.content)
				utils.show_dialog(self, text="Отчет сформирован", desc=f"Путь к файлу: {path}")
				print("=> Report loaded")

	def update_count(self, items):
		try:
			self.item_count.value = f"Всего позиций: {len(items)}"
			self.item_count.update()
		except Exception as e:
			print(e)

""" Detailed item view with image and other info"""
class DetailedView(ft.View):
	def __init__(self, page: ft.Page, id, image_src: str, category: str, date: str, sum: str):
		super().__init__(route="/detailedview")
		self.page = page
		self.id = id

		self.delete_button = ft.ElevatedButton(
			text="Удалить",
			icon=ft.Icons.DELETE, 
			on_click=lambda e: utils.show_dialog(self,
			 "Вы уверены, что хотите удалить этот объект?", 
			 "Позже его нельзя будет восстановить"
			 )
		)

		# Кнопка "Назад" в AppBar
		self.appbar = ft.AppBar(
			leading=ft.IconButton(
				icon=ft.Icons.ARROW_BACK,
				tooltip="Назад",
				on_click=lambda e: self.page.go("/items")
			),
			actions=[self.delete_button],
			title=ft.Text("Просмотр изображения"),
			bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
		)

		# Изображение
		img = ft.Image(
			src=image_src,
			width=400,
			# height=300,
			fit=ft.ImageFit.CONTAIN,
			border_radius=10,
		)

		# Тексты под изображением
		category_text = ft.Text(
			f"Категория: {category}",
			size=14,
			text_align=ft.TextAlign.CENTER,
			expand=True,
		)
		date_text = ft.Text(
			f"Дата: {date}",
			size=14,
			text_align=ft.TextAlign.CENTER,
			expand=True,
		)
		sum_text = ft.Text(
			f"Сумма: {sum}",
			size=14,
			text_align=ft.TextAlign.CENTER,
			expand=True,
		)

		# Центрируем контент с помощью Row и Column
		self.content = ft.Column(
			controls=[
				ft.Row(
					controls=[date_text, category_text, sum_text],
					alignment=ft.MainAxisAlignment.CENTER,
					vertical_alignment=ft.CrossAxisAlignment.CENTER,
					expand=True
				),
				img
			],
			alignment=ft.MainAxisAlignment.CENTER,
			horizontal_alignment=ft.CrossAxisAlignment.CENTER,
			spacing=10,
			expand=True,
			height=400, scroll=ft.ScrollMode.AUTO
		)

		self.page.dialog = ft.AlertDialog(
			title=ft.Container(ft.Text(""), alignment=ft.alignment.center),
			content=ft.Text(""),
			actions=[
				ft.TextButton("Отмена", on_click=lambda e: utils.close_dialog(self)),
				ft.TextButton("Удалить", on_click=self.delete_item)
			],
			actions_alignment=ft.MainAxisAlignment.CENTER,
		)

		# Добавляем AppBar и контент во View
		self.controls.append(self.appbar)
		self.controls.append(self.content)
	

	def delete_item(self, e=None):
		response = requests.delete(f"{self.page.ROOT_URL}/delete-item/{int(self.id)}",  headers=self.page.special_request_headers)
		print(response)
		if response.status_code in (200, 204):
			print(f"=> Deleted item id={id}")
			utils.close_dialog(self)
			self.page.filtered_items = None
			self.page.loaded_items = None
			self.page.go("/items")



""" Creating new item """
class NewItemView(ft.View):
	def __init__(self, page: ft.Page):
		super().__init__(route='/newitem')
		self.page = page
		self.stream = Stream()

		self.file_picker = ft.FilePicker(on_result=lambda e: utils.file_picked(self, e))
		self.page.overlay.append(self.file_picker)
		self.file_path = None

		# AppBar
		self.appbar = ft.AppBar(
			leading=ft.IconButton(
				icon=ft.Icons.ARROW_BACK,
				tooltip="Назад",
				on_click=self.on_exit
			),
			title=ft.Text("Добавление"),
			bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
		)

		# Поля формы
		self.category_dropdown = ft.Dropdown(
				label="Категория",
				options=[ft.dropdown.Option(c["category"]) for c in self.page.categories],
		)
		self.sum_field = ft.TextField(
			label="Сумма",
			hint_text="Введите сумму",
			keyboard_type=ft.KeyboardType.NUMBER,
			width=200
		)
		self.date_field = ft.TextField(
			label="Дата",
			width=200,
			value=datetime.date.today().strftime('%d.%m.%Y'),
		)

		self.file_name_text = ft.Text("Файл не выбран", italic=True, size=12)

		self.attach_button = ft.ElevatedButton(
			"Прикрепить изображение",
			on_click=lambda e : utils.pick_file(self, e)
		)

		self.submit_button = ft.ElevatedButton(
			"Отправить",
			on_click=self.submit,
			disabled=True
		)

		# Левая колонка — форма
		self.form = ft.Column(
			controls=[
				self.category_dropdown,
				self.sum_field,
				self.date_field,
				self.attach_button,
				self.file_name_text,
				self.submit_button,
			],
			spacing=15,
			width=300,
			alignment=ft.MainAxisAlignment.START,
		)

		# Правая колонка — видеопоток
		self.photo_label = ft.Text("Новая фотография", size=16)

		# Контейнер для видео/плейсхолдера
		self.photo_placeholder = ft.Container(
			width=300,
			height=300,
			bgcolor=ft.Colors.GREY_800,
			border_radius=8,
			alignment=ft.alignment.center,
		)

		# Кнопка "Сделать фото"
		self.photo_button = ft.ElevatedButton(
			"Сделать фото",
			icon=ft.Icons.PHOTO_CAMERA,
			on_click=self.take_photo,
			disabled = True
		)

		# Кнопка для старта стрима с камеры
		self.toggle_camera_button = ft.ElevatedButton(
			"Включить камеру",
			on_click=self.toggle_camera
		)

		self.photo_column = ft.Column(
			controls=[
				self.photo_label,
				self.photo_placeholder,
				ft.Row(
					controls=[
						self.photo_button,
						self.toggle_camera_button
					],
					alignment=ft.MainAxisAlignment.CENTER,
					spacing=50,
				)
			],
			spacing=15,
			alignment=ft.MainAxisAlignment.START,
			horizontal_alignment=ft.CrossAxisAlignment.CENTER,
			# width=220,
		)

		# Основной контейнер — горизонтальный ряд из двух колонок
		self.main_row = ft.Column(
			controls=[ft.Row(
			controls=[
				self.form,
				self.photo_column,
			],
			alignment=ft.MainAxisAlignment.CENTER,
			spacing=50,
		)],
			alignment=ft.MainAxisAlignment.CENTER,
			horizontal_alignment=ft.CrossAxisAlignment.CENTER,
			spacing=10,
			expand=True,
			scroll=ft.ScrollMode.AUTO
		)

		self.controls.append(self.appbar)
		self.controls.append(self.main_row)

		self.page.dialog = ft.AlertDialog(
			title=ft.Container(ft.Text(""), alignment=ft.alignment.center),
			content=ft.Text(""),
			actions=[
				ft.TextButton("OK", on_click=lambda e: utils.close_dialog(self))
			],
			actions_alignment=ft.MainAxisAlignment.CENTER,
		)

		# timer to update frames from video stream
		self.camera_on = False
		self.cap_timer = Timer(self.page.TIMER_RATE, self.update_frame)
		self.cap_timer.start()
		# timer to check submit form data
		self.check_timer = Timer(0.002, self.check_fieds_data)
		self.check_timer.start()

	""" Check fields data to enable submit button """
	def check_fieds_data(self):
		try:
			category = self.category_dropdown.value
			sum_ = self.sum_field.value
			date_ = self.date_field.value
			img_base64 = self.frame_base64
			if all([category, sum_, date_, img_base64]):
				self.submit_button.disabled = False
			else:
				self.submit_button.disabled = True
		except Exception as e:
			self.submit_button.disabled = True
		finally:
			try:
				self.submit_button.update()
			except:
				print("Submit button disabled")

	""" Release camera """
	def close_camera_connection(self):
		self.camera_on = False
		self.stream.release()
		self.photo_placeholder.content = None
		self.photo_placeholder.width = 400
		self.photo_placeholder.height = 400
		self.photo_placeholder.update()

	""" Open or close camera stream """
	def toggle_camera(self, e=None):
		if not self.camera_on:
			print("=> Stream started")
			if not self.stream.available:
				self.stream.create_stream() 
			self.camera_on = True
			self.photo_button.disabled = False
			self.toggle_camera_button.text = "Выключить камеру"
		else:
			print("=> Stream stopped")
			self.close_camera_connection()
			self.photo_button.disabled = True
			self.toggle_camera_button.text = "Включить камеру"
		self.photo_button.update()
		self.toggle_camera_button.update()

	""" Activates on page exit. Releases camera, stops update-frame timer and removes temp files """
	def on_exit(self, e=None):
		self.close_camera_connection()
		self.cap_timer.stop()
		self.check_timer.stop()
		if not self.file_path is None:
			os.remove(self.file_path)
		print(f"=> Stream stopped, cap released. Temp files removed")
		self.page.go("/items")
		
	""" Update frame in photo_placeholder """
	def update_frame(self, e=None):
		if not self.camera_on: 
			return

		frame_base64 = self.stream.get_frame()
		if frame_base64:
			# Creating base64 image and put it into placeholder
			frame_shape = utils.clamp_shape(self.stream.frame_shape)
			self.photo_placeholder.width = frame_shape[1]
			self.photo_placeholder.height = frame_shape[0]
			self.photo_placeholder.content = ft.Image(
				src_base64=frame_base64,
				width=self.photo_placeholder.width,
				height=self.photo_placeholder.height,
				fit=ft.ImageFit.CONTAIN,
			)

		self.photo_placeholder.update()

	""" Make photo and save it to local storage """
	def take_photo(self, e):
		frame_base64 = self.stream.get_frame()
		if frame_base64:
			print("=> Made photo")
			utils.show_dialog(self, "Фото сделано!", "Фотография была прикреплена к форме отправки")
			
			filename = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.png'
			utils.upload_file_base64(frame_base64, os.path.join(self.page.STORAGE_PATH, 'temp', filename))
			utils.update_attachment_data(self, os.path.join(self.page.STORAGE_PATH, 'temp', filename), filename, frame_base64, "screenshot")
		else:
			print("! Base64 converting error, photo was not made")
			utils.show_dialog(self, "Ошибка", "Некорректный источник")
		self.page.update()

	""" Submit data from item creation form """
	def submit(self, e):
		category = self.category_dropdown.value
		sum_ = self.sum_field.value
		date_ = self.date_field.value
		img_base64 = self.frame_base64
		try:
			sum_float = float(sum_)
			date_ = utils.date_to_sql(date_)
			if date_ is None:
				print(f"Wrong 'date' field format")
				utils.show_dialog(self, "Ошибка", "Дата введена некорректно. Придерживаетесь формата: 01.01.2001")
				return

		except Exception as e:
			print(f"! Error while converting data: {e}")
			utils.show_dialog(self, "Ошибка", "Сумма введена некорректно. В поле суммы необходимо вносить только числовые значения")
			return

		new_item = json.dumps({
			"category": category,
			"sum": sum_float,
			"creation_date": date_,
			"image": img_base64
		})
		response = requests.post(f'{self.page.ROOT_URL}/add-item', data=new_item, headers=self.page.special_request_headers)
		print(response)
		utils.show_dialog(self, "Объект сохранен", "Чтобы увидеть изменения, перезагрузите страницу")
		self.page.update()


""" Creating new category """
class CategoryView(ft.View):
	def __init__(self, page: ft.Page):
		super().__init__(route='/category')
		self.page = page
		self.new_category_field = ft.TextField(label="Новая категория", width=300)
		self.add_button = ft.ElevatedButton(text="Добавить", on_click=self.add_category)
		self.reload_button = ft.IconButton(
			icon=ft.Icons.REFRESH,
			tooltip="Reload",
			on_click=self.load_categories
		)

		# AppBar
		self.appbar = ft.AppBar(
			leading=ft.IconButton(
				icon=ft.Icons.ARROW_BACK,
				tooltip="Назад",
				on_click=self.on_exit
			),
			title=ft.Text("Категории документов"),
			bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
		)

		# Blank table for items
		self.table = ft.DataTable(
			columns=[
				ft.DataColumn(ft.Text("")),
				ft.DataColumn(ft.Text("")),
			],
			rows=[],
			expand=True
		)

		self.main_content = ft.Column(
			controls=[
				ft.Row(
					controls=[
						self.new_category_field,
						self.add_button,
						self.reload_button
					],
					alignment=ft.MainAxisAlignment.CENTER,
					spacing=50,
				),
				ft.ListView(controls=[self.table], expand=True)
			],
			alignment=ft.MainAxisAlignment.CENTER,
			horizontal_alignment=ft.CrossAxisAlignment.CENTER,
			spacing=10,
			expand=True,
			scroll=ft.ScrollMode.AUTO
		)

		self.page.dialog = ft.AlertDialog(
			title=ft.Container(ft.Text(""), alignment=ft.alignment.center),
			content=ft.Text(""),
			actions=[
				ft.TextButton("OK", on_click=lambda e: utils.close_dialog(self))
			],
			actions_alignment=ft.MainAxisAlignment.CENTER,
		)

		self.controls.append(self.appbar)	
		self.controls.append(self.main_content)

		self.load_categories()

	""" Add new category to db """
	def add_category(self, e=None):
		category = self.new_category_field.value
		if not "".join(category.split(" ")).isalnum():
			print(f"Wrong 'category' field format")
			utils.show_dialog(self, "Заполните данные!", "Поле с названием новой категории не может быть пустым")
		else:
			new_category = json.dumps({
				"category": category,
			})
			response = requests.post(f'{self.page.ROOT_URL}/add-category', data=new_category, headers=self.page.special_request_headers)
			print(response)
			if response.status_code in (200, 204):
				utils.show_dialog(self, "Категория сохранена", "Данные таблицы обновлены")
				self.load_categories()
				self.page.update()
			else:
				utils.show_dialog(self, "Ошибка!", "Такая категория уже существует. Выберите другое название")
		
	
	""" Add item row to table """
	def add_row(self, category):
		self.table.rows.append(
			ft.DataRow(
				cells=[
					ft.DataCell(ft.Text(category["category"], selectable=True)),
					ft.DataCell(
						ft.Container(
							content=ft.ElevatedButton(
								text="Удалить",
								icon=ft.Icons.DELETE,
								on_click=lambda e: self.delete_category(category=category)
							),
							alignment=ft.alignment.center_right,
							expand=True, 
						)
					)
				]
			)
		)
		self.page.update()

	""" Load list of available categories from server """
	def load_categories(self, e=None):
		resp = requests.get(f'{self.page.ROOT_URL}/categories', headers=self.page.request_headers)
		if resp.status_code in [200, 204]:
			self.table.rows.clear()
			self.page.categories = resp.json()
			for category in self.page.categories:
				self.add_row(category)
			print("=> Loaded categories")

	def delete_category(self, e=None, category=None):
		if any([category["category"]==item["category"] for item in self.page.loaded_items]):
			utils.show_dialog(self, "Категория используется!", "Нельзя удалить категорию, которая используется одним или более объектом")
			return
		id = category["id"]
		response = requests.delete(f"{self.page.ROOT_URL}/delete-category/{id}",  headers=self.page.special_request_headers)
		print(response)
		if response.status_code in (200, 204):
			print(f"=> Deleted category id={id}")
			utils.show_dialog(self, "Категория удалена", "Данные таблицы обновлены")
			self.load_categories()
	
	def on_exit(self, e=None):
		self.page.go('/items')


""" Creating new user """
class UserView(ft.View):
	def __init__(self, page: ft.Page):
		super().__init__(route='/user')
		self.page = page
		self.username_field = ft.TextField(label="Имя пользователя", width=300)
		self.password_field = ft.TextField(label="Пароль", width=300)
		self.admin_rights_dropdown = ft.Dropdown(
				label="Администратор",
				options=[ft.dropdown.Option(1, "Да"), ft.dropdown.Option(0, "Нет")],
				width=200
		)
		self.add_button = ft.ElevatedButton(text="Добавить", on_click=self.add_user)
		self.reload_button = ft.IconButton(
			icon=ft.Icons.REFRESH,
			tooltip="Reload",
			on_click=self.load_users
		)

		# AppBar
		self.appbar = ft.AppBar(
			leading=ft.IconButton(
				icon=ft.Icons.ARROW_BACK,
				tooltip="Назад",
				on_click=self.on_exit
			),
			title=ft.Text("Список пользователей"),
			bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
		)

		# Blank table for items
		self.table = ft.DataTable(
			columns=[
				ft.DataColumn(ft.Text("Имя пользователя")),
				ft.DataColumn(ft.Text("Права администратора")),
				ft.DataColumn(ft.Text(""))
			],
			rows=[],
			expand=True
		)

		self.main_content = ft.Column(
			controls=[
				ft.Row(
					controls=[
						self.username_field,
						self.password_field,
						self.admin_rights_dropdown,
						self.add_button,
						self.reload_button
					],
					alignment=ft.MainAxisAlignment.CENTER,
					spacing=50,
				),
				ft.ListView(controls=[self.table], expand=True)
			],
			alignment=ft.MainAxisAlignment.CENTER,
			horizontal_alignment=ft.CrossAxisAlignment.CENTER,
			spacing=10,
			expand=True,
			scroll=ft.ScrollMode.AUTO
		)

		self.page.dialog = ft.AlertDialog(
			title=ft.Container(ft.Text(""), alignment=ft.alignment.center),
			content=ft.Text(""),
			actions=[
				ft.TextButton("OK", on_click=lambda e: utils.close_dialog(self))
			],
			actions_alignment=ft.MainAxisAlignment.CENTER,
		)

		self.controls.append(self.appbar)	
		self.controls.append(self.main_content)

		self.load_users()

	""" Add new user to db """
	def add_user(self, e=None):
		username = self.username_field.value
		password = self.password_field.value
		admin = self.admin_rights_dropdown.value
		if not str(username).isalnum() or not str(password).isalnum() or int(admin) not in [0, 1]:
			print(f"! Wrong input data format")
			utils.show_dialog(self, "Заполните данные!", "Проверьте, что в каждом поле указано значение")
		else:
			new_user = json.dumps({
				"username": username,
				"password": password,
				"admin": int(admin)
			})
			response = requests.post(f'{self.page.ROOT_URL}/add-user', data=new_user, headers=self.page.special_request_headers)
			print(response)
			if response.status_code in (200, 204):
				utils.show_dialog(self, "Пользователь сохранен", "Данные таблицы обновлены")
				self.load_users()
				self.page.update()
			else:
				utils.show_dialog(self, "Ошибка!", "Пользователь с таким именем уже существует")
		
	
	""" Add item row to table """
	def add_row(self, user):
		username = user["username"]
		if user["admin"] == 0:
			admin = 'Нет'
		else:
			admin = 'Да'
		self.table.rows.append(
			ft.DataRow(
				cells=[
					ft.DataCell(ft.Text(username, selectable=True)),
					ft.DataCell(ft.Text(admin, selectable=False)),
					ft.DataCell(
						ft.Container(
							content=ft.ElevatedButton(
								text="Удалить",
								icon=ft.Icons.DELETE,
								on_click=lambda e: self.delete_user(username=username)
							),
							alignment=ft.alignment.center_right,
							expand=True, 
						)
					)
				]
			)
		)
		self.page.update()

	""" Load list of active users from server """
	def load_users(self, e=None):
		resp = requests.get(f'{self.page.ROOT_URL}/users', headers=self.page.request_headers)
		if resp.status_code in [200, 204]:
			self.table.rows.clear()
			for user in resp.json():
				self.add_row(user)
			print("=> Loaded users")

	def delete_user(self, e=None, username=None):
		if username == self.page.current_session_username:
			utils.show_dialog(self, "Ошибка!", "Нельзя удалить данные пользователя, который используется вами в данный момент")
			return
		response = requests.delete(f"{self.page.ROOT_URL}/delete-user/{username}",  headers=self.page.special_request_headers)
		print(response)
		if response.status_code in (200, 204):
			print(f"=> Deleted user = {username}")
			utils.show_dialog(self, "Пользователь удален", "Данные таблицы обновлены")
			self.load_users()
	
	def on_exit(self, e=None):
		self.page.go('/items')