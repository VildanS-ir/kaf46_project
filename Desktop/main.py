import tkinter
import customtkinter
import sqlite3
from datetime import datetime
from tkinter import messagebox

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("green")


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Инициализация базы данных
        self.init_db()

        # Настройка окна
        self.title("Task Tracker")
        self.geometry(f"{900}x{650}")

        # Настройка сетки
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = customtkinter.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=(20, 20), pady=(20, 20), sticky="nsew")
        self.tabview.add("Внести задачу")
        self.tabview.add("Доска задач")
        self.tabview.add("Канбан-доска")

        # Конфигурация вкладок
        self.tabview.tab("Внести задачу").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Доска задач").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Канбан-доска").grid_columnconfigure((0, 1, 2), weight=1)

        # Вкладка "Внести задачу"
        self.create_input_tab()

        # Вкладка "Доска задач"
        self.create_task_board()

        # Вкладка "Канбан-доска"
        self.create_kanban_board()

        # Обновляем отображение задач при запуске
        self.update_task_display()
        self.update_kanban_board()

    def init_db(self):
        """Инициализация базы данных"""
        self.conn = sqlite3.connect('tasks.db')
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                deadline TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def create_input_tab(self):
        """Создание элементов вкладки для ввода задач"""
        # Поле для ввода задачи
        self.zad_entry = customtkinter.CTkEntry(self.tabview.tab("Внести задачу"), placeholder_text="Задача")
        self.zad_entry.grid(row=0, column=0, padx=20, pady=(10, 10), sticky="ew")

        # Выбор статуса
        self.status_var = tkinter.StringVar(value="Статус")
        self.optionmenu_1 = customtkinter.CTkOptionMenu(
            self.tabview.tab("Внести задачу"),
            dynamic_resizing=False,
            variable=self.status_var,
            values=["Запланирована", "В работе", "Сделана"]
        )
        self.optionmenu_1.grid(row=1, column=0, padx=20, pady=(20, 10))

        # Выбор приоритета
        self.priority_var = tkinter.StringVar(value="Приоритет")
        self.combobox_1 = customtkinter.CTkComboBox(
            self.tabview.tab("Внести задачу"),
            variable=self.priority_var,
            values=["Не очень важная", "Важная", "Очень важная"]
        )
        self.combobox_1.grid(row=2, column=0, padx=20, pady=(10, 10))

        # Ввод дедлайна
        self.date_entry = customtkinter.CTkEntry(self.tabview.tab("Внести задачу"),
                                                 placeholder_text="Дедлайн(ДД.ММ.ГГ)")
        self.date_entry.grid(row=3, column=0, padx=20, pady=(10, 10))

        # Кнопка добавления
        self.string_input_button = customtkinter.CTkButton(
            self.tabview.tab("Внести задачу"),
            text="Добавить",
            command=self.add_task
        )
        self.string_input_button.grid(row=4, column=0, padx=20, pady=(10, 10))

    def create_task_board(self):
        """Создание доски задач с фильтрами"""
        # Фрейм для фильтров
        self.filter_frame = customtkinter.CTkFrame(self.tabview.tab("Доска задач"))
        self.filter_frame.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")

        # Фильтр по приоритету
        self.priority_filter_var = tkinter.StringVar(value="Все приоритеты")
        self.priority_filter = customtkinter.CTkOptionMenu(
            self.filter_frame,
            variable=self.priority_filter_var,
            values=["Все приоритеты", "Не очень важная", "Важная", "Очень важная"],
            command=lambda _: self.update_task_display()
        )
        self.priority_filter.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="w")

        # Фильтр по дедлайну
        self.deadline_filter_var = tkinter.StringVar(value="Все сроки")
        self.deadline_filter = customtkinter.CTkOptionMenu(
            self.filter_frame,
            variable=self.deadline_filter_var,
            values=["Все сроки", "С дедлайном", "Без дедлайна", "Просроченные"],
            command=lambda _: self.update_task_display()
        )
        self.deadline_filter.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Кнопка сброса фильтров (теперь column=3)
        self.reset_filters_btn = customtkinter.CTkButton(
            self.filter_frame,
            text="Сбросить фильтры",
            command=self.reset_filters,
            width=120
        )
        self.reset_filters_btn.grid(row=0, column=3, padx=(5, 10), pady=5, sticky="e")

        # Фильтр сортировки по дате
        self.sort_filter_var = tkinter.StringVar(value="Сортировка")
        self.sort_filter = customtkinter.CTkOptionMenu(
            self.filter_frame,
            variable=self.sort_filter_var,
            values=["Сортировка", "По дате создания (новые)", "По дате создания (старые)", "По дедлайну (ближайшие)"],
            command=lambda _: self.update_task_display()
        )
        self.sort_filter.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Прокручиваемая область для задач
        self.tasks_scrollable = customtkinter.CTkScrollableFrame(self.tabview.tab("Доска задач"))
        self.tasks_scrollable.grid(row=1, column=0, padx=20, pady=(5, 20), sticky="nsew")

        # Метка для задач (будет обновляться)
        self.label_tab_2 = customtkinter.CTkLabel(self.tasks_scrollable, text="", justify="left")
        self.label_tab_2.pack(padx=10, pady=10, anchor="w")

    def create_kanban_board(self):
        """Создание канбан-доски с тремя колонками"""
        # Создаем фреймы для колонок
        self.column_planned = customtkinter.CTkFrame(self.tabview.tab("Канбан-доска"))
        self.column_planned.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.column_in_progress = customtkinter.CTkFrame(self.tabview.tab("Канбан-доска"))
        self.column_in_progress.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.column_done = customtkinter.CTkFrame(self.tabview.tab("Канбан-доска"))
        self.column_done.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        # Заголовки колонок
        customtkinter.CTkLabel(self.column_planned, text="Запланирована", font=("Arial", 14, "bold")).pack(pady=5)
        customtkinter.CTkLabel(self.column_in_progress, text="В работе", font=("Arial", 14, "bold")).pack(pady=5)
        customtkinter.CTkLabel(self.column_done, text="Сделана", font=("Arial", 14, "bold")).pack(pady=5)

        # Прокручиваемые области для задач
        self.planned_tasks = customtkinter.CTkScrollableFrame(self.column_planned, height=500)
        self.planned_tasks.pack(fill="both", expand=True, padx=5, pady=5)

        self.in_progress_tasks = customtkinter.CTkScrollableFrame(self.column_in_progress, height=500)
        self.in_progress_tasks.pack(fill="both", expand=True, padx=5, pady=5)

        self.done_tasks = customtkinter.CTkScrollableFrame(self.column_done, height=500)
        self.done_tasks.pack(fill="both", expand=True, padx=5, pady=5)

    def reset_filters(self):
        """Сброс всех фильтров"""
        self.priority_filter_var.set("Все приоритеты")
        self.deadline_filter_var.set("Все сроки")
        self.sort_filter_var.set("Сортировка")
        self.update_task_display()

    def add_task(self):
        """Добавление задачи в базу данных"""
        task = self.zad_entry.get()
        status = self.status_var.get()
        priority = self.priority_var.get()
        deadline = self.date_entry.get()

        if not task or status == "Статус" or priority == "Приоритет":
            messagebox.showerror("Ошибка", "Заполните все обязательные поля!")
            return

        if deadline:
            try:
                datetime.strptime(deadline, '%d.%m.%y')
            except ValueError:
                messagebox.showerror("Ошибка", "Неправильный формат даты! Используйте ДД.ММ.ГГ")
                return

        try:
            self.cursor.execute(
                "INSERT INTO tasks (task, status, priority, deadline) VALUES (?, ?, ?, ?)",
                (task, status, priority, deadline if deadline else None)
            )
            self.conn.commit()

            self.zad_entry.delete(0, 'end')
            self.status_var.set("Статус")
            self.priority_var.set("Приоритет")
            self.date_entry.delete(0, 'end')

            self.update_task_display()
            self.update_kanban_board()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить задачу: {str(e)}")

    def update_task_display(self, event=None):

        # """Обновление отображения задач на доске с учетом фильтров"""

        try:
            # Получаем текущие значения фильтров
            priority_filter = self.priority_filter_var.get()
            deadline_filter = self.deadline_filter_var.get()
            sort_filter = self.sort_filter_var.get()

            # Формируем базовый SQL запрос
            sql = "SELECT * FROM tasks"
            conditions = []

            # Добавляем условия фильтрации
            if priority_filter != "Все приоритеты":
                conditions.append(f"priority = '{priority_filter}'")

            if deadline_filter == "С дедлайном":
                conditions.append("deadline IS NOT NULL")
            elif deadline_filter == "Без дедлайна":
                conditions.append("deadline IS NULL")
            elif deadline_filter == "Просроченные":
                conditions.append("deadline IS NOT NULL")

            # Добавляем условия к запросу, если они есть
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

            # Добавляем сортировку в зависимости от выбранного фильтра
            if sort_filter == "По дате создания (новые)":
                sql += " ORDER BY created_at DESC"
            elif sort_filter == "По дате создания (старые)":
                sql += " ORDER BY created_at ASC"
            elif sort_filter == "По дедлайну (ближайшие)":
                sql += """ ORDER BY 
                    CASE WHEN deadline IS NULL THEN 1 ELSE 0 END, 
                    substr(deadline, 7, 2) || substr(deadline, 4, 2) || substr(deadline, 1, 2) ASC"""
            else:
                sql += " ORDER BY created_at DESC"  # Сортировка по умолчанию

            self.cursor.execute(sql)
            tasks = self.cursor.fetchall()

            # Фильтрация просроченных задач на стороне Python, если выбран соответствующий фильтр
            filtered_tasks = []
            current_date = datetime.now().date()

            for task in tasks:
                task_id, task_text, status, priority, deadline, created_at = task

                if deadline_filter == "Просроченные":
                    try:
                        deadline_date = datetime.strptime(deadline, '%d.%m.%y').date()
                        if deadline_date >= current_date:
                            continue  # Пропускаем непросроченные задачи
                    except ValueError:
                        continue  # Пропускаем задачи с некорректным форматом даты

                filtered_tasks.append(task)

            if not filtered_tasks:
                self.label_tab_2.configure(text="Нет задач, соответствующих фильтрам")
                return

            tasks_text = ""
            for task in filtered_tasks:
                task_id, task_text, status, priority, deadline, created_at = task
                deadline_str = f"Дедлайн: {deadline}" if deadline else "Без дедлайна"
                status_str = f"Статус: {status}"

                # Добавляем пометку "ПРОСРОЧЕНО" для просроченных задач
                if deadline and deadline_filter == "Просроченные":
                    try:
                        deadline_date = datetime.strptime(deadline, '%d.%m.%y').date()
                        if deadline_date < current_date:
                            deadline_str = f"Дедлайн: {deadline} (ПРОСРОЧЕНО)"
                    except ValueError:
                        pass

                tasks_text += f"{task_text}\n{status_str}, {priority}, {deadline_str}\n\n"

            self.label_tab_2.configure(text=tasks_text)

        except Exception as e:
            self.label_tab_2.configure(text=f"Ошибка загрузки задач: {str(e)}")

    def update_kanban_board(self):
        """Обновление канбан-доски"""
        # Очищаем все колонки
        for widget in self.planned_tasks.winfo_children():
            widget.destroy()
        for widget in self.in_progress_tasks.winfo_children():
            widget.destroy()
        for widget in self.done_tasks.winfo_children():
            widget.destroy()

        try:
            self.cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
            tasks = self.cursor.fetchall()

            if not tasks:
                return

            for task in tasks:
                task_id, task_text, status, priority, deadline, created_at = task
                deadline_str = f"\nДедлайн: {deadline}" if deadline else ""
                priority_str = f"\nПриоритет: {priority}"

                task_frame = customtkinter.CTkFrame(
                    self.planned_tasks if status == "Запланирована" else
                    self.in_progress_tasks if status == "В работе" else
                    self.done_tasks,
                    border_width=1,
                    corner_radius=5
                )
                task_frame.pack(fill="x", pady=5, padx=5)

                # Верхняя часть с текстом задачи
                text_frame = customtkinter.CTkFrame(task_frame, fg_color="transparent")
                text_frame.pack(fill="x", padx=5, pady=(5, 0))

                task_label = customtkinter.CTkLabel(
                    text_frame,
                    text=f"{task_text}{priority_str}{deadline_str}",
                    wraplength=200,
                    justify="left"
                )
                task_label.pack(side="left", padx=5, pady=5, anchor="w")

                # Нижняя часть с кнопками
                btn_frame = customtkinter.CTkFrame(task_frame, fg_color="transparent")
                btn_frame.pack(fill="x", padx=5, pady=(0, 5))

                # Кнопка удаления
                delete_btn = customtkinter.CTkButton(
                    btn_frame,
                    text="Удалить",
                    command=lambda t_id=task_id: self.delete_task(t_id),
                    width=80,
                    fg_color="#d9534f",
                    hover_color="#c9302c"
                )
                delete_btn.pack(side="right", padx=(5, 0))

                # Кнопка для изменения статуса (если задача не выполнена)
                if status != "Сделана":
                    new_status = "В работу" if status == "Запланирована" else "Сделана"
                    change_btn = customtkinter.CTkButton(
                        btn_frame,
                        text=f"{new_status}",
                        command=lambda t_id=task_id, s=status: self.change_task_status(t_id, s),
                        width=80
                    )
                    change_btn.pack(side="right", padx=(5, 0))

        except Exception as e:
            print(f"Ошибка обновления канбан-доски: {str(e)}")

    def change_task_status(self, task_id, current_status):
        """Изменение статуса задачи"""
        new_status = "В работе" if current_status == "Запланирована" else "Сделана"

        try:
            self.cursor.execute(
                "UPDATE tasks SET status = ? WHERE id = ?",
                (new_status, task_id))
            self.conn.commit()
            self.update_kanban_board()
            self.update_task_display()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось изменить статус: {str(e)}")

    def delete_task(self, task_id):
        """Удаление задачи из базы данных"""
        try:
            # Подтверждение удаления
            confirm = messagebox.askyesno(
                "Подтверждение",
                "Вы уверены, что хотите удалить эту задачу?"
            )

            if confirm:
                self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                self.conn.commit()
                self.update_kanban_board()
                self.update_task_display()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить задачу: {str(e)}")

    def __del__(self):
        """Закрываем соединение с БД при уничтожении объекта"""
        if hasattr(self, 'conn'):
            self.conn.close()


if __name__ == "__main__":
    app = App()
    app.mainloop()