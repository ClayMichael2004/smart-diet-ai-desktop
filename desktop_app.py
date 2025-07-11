import tkinter as tk
from tkinter import ttk, messagebox
from smart_diet_ai.core import SmartDietRecommender

import sys
import os

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path=sys._MEIPASS #Pyinstaller stores temp path here
    except Exception:
        base_path=os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SmartDietApp:
    def __init__(self, root):
        self.root=root
        self.root.title("Smart Diet AI - food recommender")
        self.root.iconbitmap(resource_path("assets/favicon.ico"))
        self.root.geometry("1000x650")
        self.root.configure(bg="#f4f7f9")

        self.recommender=SmartDietRecommender()
        self.create_widgets()

    def create_widgets(self):
        style=ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#f4f7f9", font=("Segoe UI", 10))
        style.configure("TButton")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", rowheight=25)


        #input frame
        input_frame=ttk.LabelFrame(self.root, text="Search Food" )
        input_frame.pack(fill="x", padx=15, pady=10)

        ttk.Label(input_frame, text="Enter food name:").grid(row=0, column=0, padx=5, pady=5, sticky="W")
        self.food_entry=ttk.Entry(input_frame, width=40)
        self.food_entry.grid(row=0, column=1, padx=5, pady=5)

        search_btn=ttk.Button(input_frame, text="Search", command=self.load_food_data)
        search_btn.grid(row=0, column=2, padx=5, pady=5)

        #filterFrame
        filter_frame=ttk.LabelFrame(self.root, text="Recommendation options")
        filter_frame.pack(fill="x", padx=15, pady=5)

        ttk.Label(filter_frame, text="Goal:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.goal_var=tk.StringVar()
        self.goal_dropdown=ttk.Combobox(filter_frame, textvariable=self.goal_var, state="readonly", width=20)
        self.goal_dropdown['values']=list(self.recommender.GOAL_PROFILES.keys())
        self.goal_dropdown.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(filter_frame, text="Allergies (comma seperated):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.allergy_entry=ttk.Entry(filter_frame, width=40)
        self.allergy_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Button(filter_frame, text="Recommend", command=self.recommend_by_goal).grid(row=0, column=4, padx=5)
        ttk.Button(filter_frame, text="find similar", command=self.find_similar).grid(row=0, column=5, padx=5)
        ttk.Button(filter_frame, text="same cluster", command=self.find_cluster).grid(row=0, column=6, padx=5)

        #results frame
        self.result_frame=ttk.LabelFrame(self.root, text="Results")
        self.result_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.tree=ttk.Treeview(self.result_frame, columns=("desc", "brand", "category", "calories", "protein"), show="headings")
        self.tree.heading("desc", text="Description")
        self.tree.heading("brand", text="Brand")
        self.tree.heading("category", text="Category")
        self.tree.heading("calories", text="Calories")
        self.tree.heading("protein", text="Protein")

        self.tree.column("desc", width=250)
        self.tree.column("brand", width=150)
        self.tree.column("category", width=120)
        self.tree.column("calories", width=100)
        self.tree.column("protein", width=100)

        vsb=ttk.Scrollbar(self.result_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        self.tree.pack(fill="both", expand=True)

    def clear_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

    def populate_table(self, data):
        self.clear_table()
        for _, row in data.iterrows():
            self.tree.insert("", "end", values=(
                row.get("description", ""),
                row.get("brand", ""),
                row.get("category", ""),
                row.get("calories", ""),
                row.get("protein", "")
            ))

    def load_food_data(self):
        query=self.food_entry.get().strip()
        if not query:
            messagebox.showwarning("Input required", "Please enter a food name!")
            return
        
        loaded=self.recommender.load_data(query)
        if not loaded:
            messagebox.showerror("No results", f"No data found for '{query}'. Try another keyword")
        else:
            self.recommender.train_models()

            try:
                import os
                os.makedirs("data", exist_ok=True)
                self.recommender.data.to_csv("data/backup_foods.cvs", index=False)
            except Exception as e:
                print("failed to save backup!!", e)
            messagebox.showinfo("Data ready", f"Data loaded successfully for '{query}'. Now choose an action.")
    def recommend_by_goal(self):
        goal=self.goal_var.get()
        allergies=[a.strip() for a in self.allergy_entry.get().split(',') if a.strip()]
        results=self.recommender.filter_by_goal(goal, allergies)
        if results.empty:
            messagebox.showinfo("No matches", "No food matches found for this goal and allergy combination.")
        else:
            self.populate_table(results)

    def find_similar(self):
        query=self.food_entry.get().strip()
        results=self.recommender.find_similar(query)
        if results.empty:
            messagebox.showinfo("No matches", "Could not find similar foods")
        else:
            self.populate_table(results)

    def find_cluster(self):
        query=self.food_entry.get().strip()
        results=self.recommender.get_cluster_foods(query)
        if results.empty:
            messagebox.showinfo("No cluster", "No foods found in the same nutrient cluster")
        else:
            self.populate_table(results)

if __name__=="__main__":
    root=tk.Tk()
    root.iconbitmap(default=resource_path("assets/favicon.ico"))
    app=SmartDietApp(root)
    root.mainloop()