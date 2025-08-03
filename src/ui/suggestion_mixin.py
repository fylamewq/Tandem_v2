import tkinter as tk

class SuggestionMixin:
    def bind_suggestion_events(self, entry, field_type, row, table_type):
        entry.bind("<KeyRelease>", lambda e: self._show_suggestions_safely(entry, field_type, row, table_type, e))
        entry.bind("<Escape>", lambda e: self.hide_suggestions())
        entry.bind("<Down>", lambda e: self._suggestion_entry_down(entry, field_type, row, table_type))
        entry.bind("<Return>", lambda e: self._on_suggestion_select(entry, field_type, row, table_type))

    def _suggestion_entry_down(self, entry, field_type, row, table_type):
        if getattr(self, "suggestion_listbox", None):
            self.suggestion_listbox.focus_set()
            self.suggestion_listbox.selection_clear(0, tk.END)
            self.suggestion_listbox.selection_set(0)
            self.suggestion_listbox.activate(0)
            self.suggestion_listbox.see(0)
            return "break"

    def _show_suggestions_safely(self, entry, field_type, row, table_type, event):
        if getattr(self, "_suppress_suggestions", False) and event.keysym == "Return":
            self._suppress_suggestions = False
            return
        self.show_suggestions(entry, field_type, row, table_type)

    def show_suggestions(self, entry, field_type, row, table_type):
        text = entry.get().lower().strip()
        suggestions = self.get_suggestions_for_field(field_type, text)
        self.hide_suggestions()
        if not suggestions:
            return

        self.suggestion_toplevel = tk.Toplevel(self.root)
        self.suggestion_toplevel.overrideredirect(True)
        self.suggestion_toplevel.lift()
        self.suggestion_toplevel.attributes("-topmost", True)
        self.suggestion_toplevel.transient(self.root)

        self.suggestion_listbox = tk.Listbox(self.suggestion_toplevel)
        self.suggestion_listbox.pack(fill=tk.BOTH, expand=True)
        for s in suggestions:
            self.suggestion_listbox.insert(tk.END, s)
        self.suggestion_listbox.selection_set(0)
        self.suggestion_listbox.activate(0)

        entry_x = entry.winfo_rootx()
        entry_y = entry.winfo_rooty() + entry.winfo_height()
        entry_width = entry.winfo_width()
        self.suggestion_toplevel.geometry(f"{entry_width}x150+{entry_x}+{entry_y}")

        # --- Контекстное меню
        self.suggestion_listbox.bind("<Button-3>", lambda event: self._show_entry_context_menu(event, entry))
        self.suggestion_listbox.bind("<Button-2>", lambda event: self._show_entry_context_menu(event, entry))
        self.suggestion_toplevel.bind("<Button-3>", lambda event: self._show_entry_context_menu(event, entry))
        self.suggestion_toplevel.bind("<Button-2>", lambda event: self._show_entry_context_menu(event, entry))

        # --- SCROLL REDIRECT
        def redirect_scroll(event, direction=None):
            canvas = getattr(self, "act_canvas", None)
            if canvas is not None:
                # Windows/Mac
                if hasattr(event, "delta") and event.delta != 0:
                    if event.delta > 0:
                        canvas.yview_scroll(-1, "units")
                    else:
                        canvas.yview_scroll(1, "units")
                # Linux: Button-4/5
                elif getattr(event, "num", None) == 4:
                    canvas.yview_scroll(-1, "units")
                elif getattr(event, "num", None) == 5:
                    canvas.yview_scroll(1, "units")
                return "break"

        self.suggestion_listbox.bind("<MouseWheel>", redirect_scroll)
        self.suggestion_listbox.bind("<Button-4>", lambda e: redirect_scroll(e, -1))
        self.suggestion_listbox.bind("<Button-5>", lambda e: redirect_scroll(e, 1))

        self.suggestion_listbox.bind("<Return>", lambda e: self._on_suggestion_select(entry, field_type, row, table_type))
        self.suggestion_listbox.bind("<Escape>", lambda e: self.hide_suggestions())
        self.suggestion_listbox.bind("<ButtonRelease-1>", lambda e: self._on_suggestion_select(entry, field_type, row, table_type))
        self.suggestion_listbox.bind("<Up>", lambda e: self._move_suggestion_selection(-1))
        self.suggestion_listbox.bind("<Down>", lambda e: self._move_suggestion_selection(1))
        self.suggestion_listbox.bind("<FocusOut>", lambda e: self.hide_suggestions())

        self.root.bind("<Unmap>", self._on_root_unmap)
        self.root.bind("<Map>", self._on_root_map)

    def _show_entry_context_menu(self, event, entry):
        self.hide_suggestions()
        if hasattr(entry, "context_menu"):
            try:
                entry.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                if hasattr(entry.context_menu, 'grab_release'):
                    entry.context_menu.grab_release()

    def _on_root_unmap(self, event):
        self.hide_suggestions()

    def _on_root_map(self, event):
        pass

    def _focus_suggestion_listbox(self):
        if getattr(self, "suggestion_listbox", None):
            self.suggestion_listbox.focus_set()

    def hide_suggestions(self, event=None):
        if getattr(self, "suggestion_toplevel", None):
            try:
                self.suggestion_toplevel.destroy()
            except Exception:
                pass
            self.suggestion_toplevel = None
            self.suggestion_listbox = None
        if hasattr(self.root, 'event_generate'):
            self.root.event_generate("<<SuggestionClosed>>")

    def _on_suggestion_select(self, entry, field_type, row, table_type):
        if self.suggestion_listbox is None:
            return
        cur = self.suggestion_listbox.curselection()
        if cur:
            value = self.suggestion_listbox.get(cur[0])
            entry.delete(0, tk.END)
            entry.insert(0, value)
            self.fill_row_by_suggestion(entry, field_type, value, row, table_type)
        self.hide_suggestions()
        entry.focus_set()
        self._suppress_suggestions = True

    def _move_suggestion_selection(self, direction):
        if getattr(self, "suggestion_listbox", None):
            cur = self.suggestion_listbox.curselection()
            if cur:
                idx = cur[0] + direction
            else:
                idx = 0
            count = self.suggestion_listbox.size()
            idx = max(0, min(idx, count - 1))
            self.suggestion_listbox.selection_clear(0, tk.END)
            self.suggestion_listbox.selection_set(idx)
            self.suggestion_listbox.activate(idx)
            self.suggestion_listbox.see(idx)
            return "break"

    def fill_row_by_suggestion(self, entry, field_type, value, row, table_type):
        if table_type == "vehicle_works":
            items = self.get_works()
            entries = self.work_entries
            fill_map = {"unit": 1, "price": 3}
        elif table_type == "vehicle_materials":
            items = self.get_materials()
            entries = self.parts_entries
            fill_map = {"unit": 1, "price": 3}
        else:
            return
        if not (0 <= row < len(entries)):
            return
        for item in items:
            if item["name"] == value:
                for key, idx in fill_map.items():
                    if len(entries[row]) > idx:
                        entries[row][idx].delete(0, tk.END)
                        entries[row][idx].insert(0, item.get(key, ""))
                break