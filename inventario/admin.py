from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .forms import LoginFormulario
from .models import Cliente, Pedido, Producto, Proveedor, Usuario

class UsuarioAdmin(UserAdmin):
    add_form = LoginFormulario
    #form = CustomUserChangeForm
    model = Usuario
    list_display = ['email', 'username',]

admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Producto)
admin.site.register(Proveedor)
admin.site.register(Pedido)
admin.site.register(Cliente)