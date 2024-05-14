from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id_, nombre, correo_electronico, contrasena, admin):
        self.id = id_
        self.nombre = nombre
        self.correo_electronico = correo_electronico
        self.contrasena = contrasena
        self.admin = admin