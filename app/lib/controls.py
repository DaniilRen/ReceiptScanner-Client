import flet as ft
from typing import Callable


""" Clickable Datacell with on_tap handler function """
def ClickableDatacell(text: str, on_tap: Callable) -> ft.DataCell:
	# Создаём DataCell с текстом и обработчиком on_tap
	cell = ft.DataCell(
		ft.Text(
			text,
			weight=ft.FontWeight.BOLD,
			style="textDecoration: underline; color: blue; cursor: pointer"
		),
		on_tap=on_tap
	)
	return cell
