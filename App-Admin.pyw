import tkinter as tk
from tkinter import messagebox, Toplevel, Label, Entry, Button, Radiobutton
import requests

API_BASE_URL = "http://localhost:5000"

class LoginWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Login")
        self.master.geometry("250x150")

        tk.Label(self.master, text="Nom d'utilisateur:").grid(row=0, column=0, padx=10, pady=10)
        self.username = tk.Entry(self.master)
        self.username.grid(row=0, column=1)

        tk.Label(self.master, text="Mot de passe:").grid(row=1, column=0, padx=10, pady=10)
        self.password = tk.Entry(self.master, show="*")
        self.password.grid(row=1, column=1)

        self.login_button = tk.Button(self.master, text="Login", command=self.login)
        self.login_button.grid(row=2, column=0, columnspan=2, pady=10)

    def login(self):
        # Authentification de l'utilisateur
        data = {"nom": self.username.get(), "mot_de_passe": self.password.get()}
        try:
            response = requests.post(f"{API_BASE_URL}/login", json=data)
            if response.ok:
                response_data = response.json()
                user_info = response_data.get("user", {})
                # Vérifiez si l'utilisateur est un administrateur en utilisant id_roles
                if user_info.get("id_roles") == 3:
                    self.master.destroy()  # Fermer la fenêtre de login
                    main_app_window = tk.Tk()  # Créer la fenêtre principale de l'application
                    app = ProfileApp(main_app_window, response_data['access_token'])  # Lancer l'application principale avec le token
                    main_app_window.mainloop()
                else:
                    messagebox.showerror("Erreur", "Accès refusé. Vous n'êtes pas administrateur.")
            else:
                messagebox.showerror("Erreur", "Nom d'utilisateur ou mot de passe incorrect.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue: {e}")

class ProfileApp:
    def __init__(self, master, token):
        self.master = master
        self.token = token  # Stocker le JWT pour l'utiliser dans les requêtes suivantes
        self.master.title("Gestion de Profils")
        self.setup_ui()
        self.fetch_users()

    def setup_ui(self):
        tk.Button(self.master, text="Créer un profil", command=lambda: self.open_profile_window("Créer")).grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        tk.Button(self.master, text="Actualiser", command=self.fetch_users).grid(row=0, column=1, sticky="ew", padx=10, pady=5)

        self.results_listbox = tk.Listbox(self.master, width=50, height=20)
        self.results_listbox.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.results_listbox.bind('<<ListboxSelect>>', self.on_select)

        self.edit_button = tk.Button(self.master, text="Modifier", state="disabled", command=self.edit_profile)
        self.delete_button = tk.Button(self.master, text="Supprimer", state="disabled", command=self.delete_profile)
        self.edit_button.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        self.delete_button.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

    def fetch_users(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = requests.get(f"{API_BASE_URL}/get_users", headers=headers)
            if response.ok:
                users = response.json()
                sorted_users = sorted(users, key=lambda user: user['id'])
                self.results_listbox.delete(0, tk.END)
                for user in sorted_users:
                    role = self.map_role(user["id_roles"])
                    self.results_listbox.insert(tk.END, f"{user['id']} - {user['nom']} ({role})")
            else:
                messagebox.showerror("Erreur", "Impossible de récupérer les utilisateurs.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue: {e}")

    def map_role(self, id_roles):
        roles = {1: "Demandeur", 2: "Prestataire", 3: "Administrateur"}
        return roles.get(id_roles, "Inconnu")

    def on_select(self, event=None):
        if self.results_listbox.curselection():
            self.edit_button["state"] = "normal"
            self.delete_button["state"] = "normal"
        else:
            self.edit_button["state"] = "disabled"
            self.delete_button["state"] = "disabled"

    def open_profile_window(self, action, user_data=None):
        window = Toplevel(self.master)
        window.title(f"{action} un profil")
        window.geometry("300x200")

        fields = ["nom", "code_parainage"]
        if action == "Créer":
            fields.append("mot_de_passe")
        entries = {}

        for index, field in enumerate(fields, start=1):
            Label(window, text=field.capitalize() + ":").grid(row=index, column=0, padx=30)
            entry = Entry(window, show="*") if field == "mot_de_passe" else Entry(window)
            entry.grid(row=index, column=1)
            entries[field] = entry
            if user_data:
                entry.insert(0, user_data.get(field, ""))

        role_var = tk.IntVar()
        role_var.set(user_data.get("id_roles", 1) if user_data else 1)

        roles_frame = tk.LabelFrame(window, text="Rôle")
        roles_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=5)
        for role_id, role_label in [(1, "Demandeur"), (2, "Prestataire"), (3, "Administrateur")]:
            Radiobutton(roles_frame, text=role_label, variable=role_var, value=role_id).pack(anchor="w")

        Button(window, text=action, command=lambda: self.create_profile(entries, action, window, user_data.get("id") if user_data else None, role_var.get())).grid(row=len(fields)+2, column=0, columnspan=2)

    def edit_profile(self):
        selected = self.results_listbox.curselection()
        if selected:
            selected_text = self.results_listbox.get(selected[0])
            selected_id = selected_text.split(" - ")[0]
            headers = {"Authorization": f"Bearer {self.token}"}
            try:
                response = requests.get(f"{API_BASE_URL}/get_user/{selected_id}", headers=headers)
                if response.ok:
                    user_data = response.json()
                    self.open_profile_window("Modifier", user_data)
                else:
                    messagebox.showerror("Erreur", "Impossible de récupérer les détails de l'utilisateur.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Une erreur est survenue: {e}")

    def create_profile(self, entries, action, window, user_id=None, id_roles=None):
        profile_data = {field: entry.get() for field, entry in entries.items()}
        profile_data["id_roles"] = id_roles
        headers = {"Authorization": f"Bearer {self.token}"}
        endpoint = f"{API_BASE_URL}/create_user" if action == "Créer" else f"{API_BASE_URL}/update_user/{user_id}"
        method = requests.post if action == "Créer" else requests.put
        response = method(endpoint, json=profile_data, headers=headers)
    
        if response.ok:
            messagebox.showinfo("Succès", f"Profil {action.lower()} avec succès.")
            window.destroy()
            self.fetch_users()
        else:
            messagebox.showerror("Erreur", f"L'opération de {action.lower()} a échoué.")

    def delete_profile(self):
        selected = self.results_listbox.curselection()
        if selected:
            selected_text = self.results_listbox.get(selected[0])
            selected_id = selected_text.split(" - ")[0]
            headers = {"Authorization": f"Bearer {self.token}"}
            if messagebox.askyesno("Supprimer", "Voulez-vous vraiment supprimer ce profil?"):
                try:
                    response = requests.delete(f"{API_BASE_URL}/delete_user/{selected_id}", headers=headers)
                    if response.ok:
                        messagebox.showinfo("Succès", "Profil supprimé avec succès.")
                        self.fetch_users()
                    else:
                        messagebox.showerror("Erreur", "La suppression a échoué.")
                except Exception as e:
                    messagebox.showerror("Erreur", f"Une erreur est survenue: {e}")

if __name__ == "__main__":
    login_window_root = tk.Tk()
    login_app = LoginWindow(login_window_root)
    login_window_root.mainloop()