import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import sys
import os
import traceback

# Add debug logging
def debug_log(message):
    print(f"DEBUG: {message}", file=sys.stderr)
    sys.stderr.flush()

try:
    debug_log("Starting imports...")
    from tempsms import (fetch_countries, fetch_numbers, fetch_sms, 
                        fetch_authkey, decrypt_key, copy_clipboard)
    debug_log("Imports successful")
except Exception as e:
    debug_log(f"Import error: {str(e)}")
    debug_log(f"Traceback: {traceback.format_exc()}")
    messagebox.showerror("Error", f"Failed to import required modules: {str(e)}")
    sys.exit(1)

class TempSMSApp:
    def __init__(self, root):
        try:
            debug_log("Initializing application...")
            self.root = root
            self.root.title("Temp SMS Receiver")
            self.root.geometry("900x600")
            
            # Configure style
            style = ttk.Style()
            style.theme_use('clam')  # Use a modern looking theme
            
            # Create main container
            main_frame = ttk.Frame(root, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            root.columnconfigure(0, weight=1)
            root.rowconfigure(0, weight=1)
            
            # Top section - Country Selection
            top_frame = ttk.Frame(main_frame)
            top_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
            
            ttk.Label(top_frame, text="Select Country:").pack(side=tk.LEFT, padx=(0, 5))
            self.country_combo = ttk.Combobox(top_frame, width=40, state="readonly")
            self.country_combo.pack(side=tk.LEFT, padx=(0, 5))
            
            refresh_countries_btn = ttk.Button(top_frame, text="Refresh Countries", command=self.load_countries)
            refresh_countries_btn.pack(side=tk.LEFT)
            
            # Middle section - Numbers and Messages
            # Numbers List
            numbers_frame = ttk.LabelFrame(main_frame, text="Available Numbers", padding="5")
            numbers_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
            main_frame.columnconfigure(0, weight=1)
            
            numbers_toolbar = ttk.Frame(numbers_frame)
            numbers_toolbar.pack(fill=tk.X, pady=(0, 5))
            
            refresh_numbers_btn = ttk.Button(numbers_toolbar, text="Refresh Numbers", command=self.load_numbers)
            refresh_numbers_btn.pack(side=tk.LEFT)
            
            self.numbers_list = tk.Listbox(numbers_frame, width=30)
            self.numbers_list.pack(fill=tk.BOTH, expand=True)
            numbers_scrollbar = ttk.Scrollbar(numbers_frame, orient=tk.VERTICAL, command=self.numbers_list.yview)
            numbers_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.numbers_list.configure(yscrollcommand=numbers_scrollbar.set)
            
            # Messages Area
            messages_frame = ttk.LabelFrame(main_frame, text="SMS Messages", padding="5")
            messages_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
            main_frame.columnconfigure(1, weight=2)
            
            self.messages_area = scrolledtext.ScrolledText(messages_frame, wrap=tk.WORD)
            self.messages_area.pack(fill=tk.BOTH, expand=True)
            
            # Bottom section - Status and Actions
            bottom_frame = ttk.Frame(main_frame)
            bottom_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
            
            self.status_var = tk.StringVar(value="Ready")
            status_label = ttk.Label(bottom_frame, textvariable=self.status_var)
            status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            copy_btn = ttk.Button(bottom_frame, text="Copy Number", command=self.copy_selected_number)
            copy_btn.pack(side=tk.RIGHT)
            
            # Bind events
            self.country_combo.bind('<<ComboboxSelected>>', lambda e: self.load_numbers())
            self.numbers_list.bind('<<ListboxSelect>>', lambda e: self.on_number_selected())
            
            # Configure grid weights for resizing
            main_frame.rowconfigure(1, weight=1)
            
            debug_log("GUI initialization complete")
            # Initial load
            self.load_countries()
            
        except Exception as e:
            debug_log(f"Initialization error: {str(e)}")
            debug_log(f"Traceback: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Failed to initialize application: {str(e)}")
            
    def run_async(self, func, callback, *args, **kwargs):
        def thread_func():
            try:
                debug_log(f"Running async function: {func.__name__}")
                result = func(*args, **kwargs)
                self.root.after(0, callback, result)
            except Exception as e:
                debug_log(f"Async function error: {str(e)}")
                debug_log(f"Traceback: {traceback.format_exc()}")
                self.root.after(0, self.show_error, str(e))
        
        threading.Thread(target=thread_func, daemon=True).start()
        
    def show_error(self, message):
        debug_log(f"Error: {message}")
        self.status_var.set("Error occurred")
        messagebox.showerror("Error", message)
        
    def load_countries(self):
        try:
            debug_log("Loading countries...")
            self.status_var.set("Loading countries...")
            self.country_combo.set('')
            self.country_combo['values'] = []
            
            def on_complete(countries):
                try:
                    country_list = [f"{c['country_code']} - {c['Country_Name']}" for c in countries]
                    self.country_combo['values'] = country_list
                    if country_list:
                        self.country_combo.set(country_list[0])
                        self.load_numbers()
                    self.status_var.set("Countries loaded")
                    debug_log("Countries loaded successfully")
                except Exception as e:
                    debug_log(f"Error processing countries: {str(e)}")
                    self.show_error(f"Error processing countries: {str(e)}")
            
            self.run_async(fetch_countries, on_complete)
        except Exception as e:
            debug_log(f"Error in load_countries: {str(e)}")
            self.show_error(f"Failed to load countries: {str(e)}")
        
    def load_numbers(self):
        try:
            if not self.country_combo.get():
                return
                
            debug_log("Loading numbers...")
            self.status_var.set("Loading numbers...")
            self.numbers_list.delete(0, tk.END)
            country = self.country_combo.get().split(' - ')[1]
            
            def on_complete(data):
                try:
                    numbers = data.get("Available_numbers", [])
                    for number in numbers:
                        number_display = (number.get("E.164") or 
                                    number.get("number") or 
                                    number.get("phone_number", "Unknown"))
                        self.numbers_list.insert(tk.END, number_display)
                    self.status_var.set("Numbers loaded")
                    debug_log("Numbers loaded successfully")
                except Exception as e:
                    debug_log(f"Error processing numbers: {str(e)}")
                    self.show_error(f"Error processing numbers: {str(e)}")
            
            self.run_async(fetch_numbers, on_complete, country, 1)
        except Exception as e:
            debug_log(f"Error in load_numbers: {str(e)}")
            self.show_error(f"Failed to load numbers: {str(e)}")
        
    def on_number_selected(self):
        try:
            selection = self.numbers_list.curselection()
            if not selection:
                return
                
            debug_log("Loading messages...")
            number = self.numbers_list.get(selection[0])
            self.status_var.set("Loading messages...")
            self.messages_area.delete(1.0, tk.END)
            
            def on_complete(messages):
                try:
                    self.messages_area.delete(1.0, tk.END)
                    for msg in messages:
                        self.messages_area.insert(tk.END, 
                            f"From: {msg['FromNumber']}\n"
                            f"Time: {msg['message_time']}\n"
                            f"Message: {msg['Messagebody']}\n"
                            f"{'-' * 50}\n"
                        )
                    self.status_var.set("Messages loaded")
                    debug_log("Messages loaded successfully")
                except Exception as e:
                    debug_log(f"Error processing messages: {str(e)}")
                    self.show_error(f"Error processing messages: {str(e)}")
            
            self.run_async(fetch_sms, on_complete, number)
        except Exception as e:
            debug_log(f"Error in on_number_selected: {str(e)}")
            self.show_error(f"Failed to load messages: {str(e)}")
        
    def copy_selected_number(self):
        try:
            selection = self.numbers_list.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a number first")
                return
                
            number = self.numbers_list.get(selection[0])
            result = copy_clipboard(number)
            if result[0]:
                self.status_var.set("Number copied to clipboard")
                debug_log("Number copied successfully")
            else:
                debug_log(f"Copy error: {result[1]}")
                messagebox.showwarning("Warning", result[1])
        except Exception as e:
            debug_log(f"Error in copy_selected_number: {str(e)}")
            self.show_error(f"Failed to copy number: {str(e)}")

if __name__ == "__main__":
    try:
        debug_log("Starting application...")
        root = tk.Tk()
        app = TempSMSApp(root)
        debug_log("Application initialized, starting mainloop")
        root.mainloop()
    except Exception as e:
        debug_log(f"Fatal error: {str(e)}")
        debug_log(f"Traceback: {traceback.format_exc()}")
        messagebox.showerror("Fatal Error", f"Application failed to start: {str(e)}") 