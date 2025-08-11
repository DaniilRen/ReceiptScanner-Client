import flet as ft
import views
import os
import sys
import json
import urllib.parse


def main(page: ft.Page):
	# load app config
	with open(os.path.join(os.path.dirname(__file__), "client_app_config.json")) as file:
		config = json.load(file)
		page.ROOT_URL = config["ROOT_URL"] # root url for requests to API
		page.TIMER_RATE = config["TIMER_RATE"]
		page.THEME = config["THEME"]
		print(f"=> Set default params: theme={page.THEME}, timer rate={page.TIMER_RATE}, root url={page.ROOT_URL}")
		
		# check if app runs as executable
		page.executable = getattr(sys, 'frozen', False)
		# create temp storage: config STORAGE_PATH should be absolute path to storage
		if page.executable:
			storage_dir = os.path.realpath(config["STORAGE_PATH"])
		else:
			print("! Application runs in development mode")
			storage_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), 'assets'))
		os.makedirs(os.path.join(storage_dir, 'temp'), exist_ok=True)
		page.STORAGE_PATH = storage_dir
		print(f"=> Created storage dir: {storage_dir}")
		print("=> Config loaded")


	# setting app theme
	try:
		with open(os.path.join(os.path.dirname(__file__), "lib", "themes.json")) as file:
			page.theme = ft.Theme(color_scheme_seed=json.load(file)[page.THEME])
	except Exception as e:
		# default theme
		page.theme = ft.Theme(color_scheme_seed='#D4E9F7')
	page.theme_mode=ft.ThemeMode.LIGHT

	# need to fix icon
	page.window.prevent_close = True
	page.window.icon = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")

	page.vertical_alignment = ft.MainAxisAlignment.CENTER
	page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

	page.title = "ItemScanner"
	# needed for correct views work according to account rights 
	page.current_session_username = None 
	page.current_session_admin = None
	# needed for requests to api
	page.token = None
	page.request_headers = None
	# stroring loaded objects
	page.loaded_items = None
	page.filtered_items = None 
	page.categories = []

	def on_close(e: ft.ControlEvent):
		if e.data == "close":
			# Removing temp files
			print("=> Application is closing. Performing cleanup...")
			temp_dir = os.path.join(page.STORAGE_PATH, 'temp')
			count = 0
			start_count = len(os.listdir(temp_dir))
			for item_name in os.listdir(temp_dir):
				item_path = os.path.join(temp_dir, item_name)
				if os.path.isfile(item_path):
					os.remove(item_path)
					count += 1
			print(f"Removed {count} of {start_count} files")
			
			page.window.prevent_close = False
			page.window.on_event = None  
			page.update()
			page.window.close() 

	def parse_detailed_view_params():
		# parsing params from URL
		parsed = urllib.parse.urlparse(page.route)
		params = urllib.parse.parse_qs(parsed.query)
		_id = params.get("id", [""])[0]
		img = params.get("img", [""])[0]
		category = params.get("category", [""])[0]
		date = params.get("date", [""])[0]
		_sum = params.get("sum", [""])[0]

		# decoding route params 
		id_ = urllib.parse.unquote(_id)
		img_ = urllib.parse.unquote(img)
		category_ = urllib.parse.unquote(category)
		date_ = urllib.parse.unquote(date)
		sum_ = urllib.parse.unquote(_sum)
		return [id_, img_, category_, date_, sum_]


	def route_change(route):
		print(f"- {page.route}")
		page.views.clear()
		if page.route == '/login':
			page.views.append(views.LoginView(page))
		elif page.route == "/items":
			page.views.append(views.ItemsView(page))
		elif page.route == "/newitem":
			page.views.append(views.NewItemView(page))
		elif page.route == "/category":
			page.views.append(views.CategoryView(page))
		elif page.route == "/user":
			page.views.append(views.UserView(page))
		elif page.route.startswith("/detailedview"):
			page.views.append(views.DetailedView(page, *parse_detailed_view_params()))
		page.update()
			

	def view_pop(view):
		page.views.pop()
		top_view = page.views[-1]
		page.go(top_view.route)
	print("=> Views routing created")

	page.window.on_event = on_close

	page.on_route_change = route_change
	page.on_view_pop = view_pop
	page.go("/login")
	print("==> Ready to work")


ft.app(main)