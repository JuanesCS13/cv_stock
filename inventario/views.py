'''modulos de django'''
#renderiza las vistas al usuario
from django.shortcuts import render
# para redirigir a otras paginas
from django.http import HttpResponseRedirect, HttpResponse,FileResponse
# clase para crear vistas basadas en sub-clases
from django.views import View
#autentificacion de usuario e inicio de sesion
from django.contrib.auth import authenticate, login, logout
#verifica si el usuario esta logeado
from django.contrib.auth.mixins import LoginRequiredMixin
#Mensajes de formulario
from django.contrib import messages
#Ejecuta un comando en la terminal externa
from django.core.management import call_command
#procesa archivos en .json
from django.core import serializers
#permite acceder de manera mas facil a los ficheros
from django.core.files.storage import FileSystemStorage
#formularios dinamicos
from django.forms import formset_factory
'''modulos personalizadas'''
#modelos
from .models import *
#el formulario de login
from .forms import *
#funciones personalizadas
from .funciones import *
#excepciones personalizadas
from .exceptions import ErrorConfiguracionGeneralNoDefinida


class Login(View):

    '''Ingresar a la vista por método GET'''
    def get(self,request):
        if request.user.is_authenticated == True:
            return HttpResponseRedirect('/inventario/panel')

        form = LoginFormulario()
        #Envia al usuario el formulario para que lo llene
        return render(request, 'inventario/login.html', {'form': form})

    
    '''Al enviar formulario en método post'''
    def post(self,request):
        # Crea una instancia del formulario y la llena con los datos:
        form = LoginFormulario(request.POST)
        # Revisa si es valido:
        if form.is_valid():
            usuario = form.cleaned_data['username']
            clave = form.cleaned_data['password']
            # Se verifica que el usuario y su clave validadas existan
            logeado = authenticate(request, username=usuario, password=clave)
            if logeado is not None:
                login(request,logeado)
                #login valido redirige a panel
                return HttpResponseRedirect('/inventario/panel')
            else:
                #login errado regresa al formulario
                return render(request, 'inventario/login.html', {'form': form})
        

class Panel(LoginRequiredMixin, View):
    #Las dos variables son la pagina a redirigir y el campo adicional, respectivamente
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request):
        from datetime import date
        contexto = {'usuario': request.user.username,
                    'id_usuario':request.user.id,
                   'nombre': request.user.first_name,
                   'apellido': request.user.last_name,
                   'correo': request.user.email,
                   'fecha':  date.today(),
                   'productosRegistrados' : Producto.numeroRegistrados(),
                   'productosVendidos' :  DetalleFactura.productosVendidos(),
                   'clientesRegistrados' : Cliente.numeroRegistrados(),
                   'usuariosRegistrados' : Usuario.numeroRegistrados(),
                   'facturasEmitidas' : Factura.numeroRegistrados(),
                   'ingresoTotal' : Factura.ingresoTotal(),
                   'ultimasVentas': DetalleFactura.ultimasVentas(),
                   'administradores': Usuario.numeroUsuarios('administrador'),
                   'usuarios': Usuario.numeroUsuarios('usuario')

        }
        return render(request, 'inventario/panel.html',contexto)


class Salir(LoginRequiredMixin, View):
    login_url = 'inventario/login'
    redirect_field_name = None

    def get(self, request):
        logout(request)
        return HttpResponseRedirect('/inventario/login')


class Perfil(LoginRequiredMixin, View):
    login_url = 'inventario/login'
    redirect_field_name = None

    '''Acceder y validar que el usuario pueda modificar al otro usuario el cual es obtenido por la variable p'''
    def get(self, request, modo, p):
        if modo == 'editar':
            perf = Usuario.objects.get(id=p)
            editandoSuperAdmin = False

            if p == 1:
                if request.user.nivel != 2:
                    messages.error(request, 'No puede editar el perfil del administrador por no tener los permisos suficientes')
                    return HttpResponseRedirect('/inventario/perfil/ver/%s' % p)
                editandoSuperAdmin = True
            else:
                if request.user.is_superuser != True: 
                    messages.error(request, 'No puede cambiar el perfil por no tener los permisos suficientes')
                    return HttpResponseRedirect('/inventario/perfil/ver/%s' % p) 

                else:
                    if perf.is_superuser == True:
                        if request.user.nivel == 2:
                            pass

                        elif perf.id != request.user.id:
                            messages.error(request, 'No puedes cambiar el perfil de un usuario de tu mismo nivel')

                            return HttpResponseRedirect('/inventario/perfil/ver/%s' % p) 

            if editandoSuperAdmin:
                form = UsuarioFormulario()
                form.fields['level'].disabled = True
            else:
                form = UsuarioFormulario()

            form['username'].field.widget.attrs['value']  = perf.username
            form['first_name'].field.widget.attrs['value']  = perf.first_name
            form['last_name'].field.widget.attrs['value']  = perf.last_name
            form['email'].field.widget.attrs['value']  = perf.email
            form['level'].field.widget.attrs['value']  = perf.nivel

            contexto = {'form':form,'modo':request.session.get('perfilProcesado'),'editar':'perfil',
            'nombreUsuario':perf.username}

            contexto = complementarContexto(contexto,request.user)
            return render(request,'inventario/perfil/perfil.html', contexto)


        elif modo == 'clave':  
            perf = Usuario.objects.get(id=p)
            if p == 1:
                if request.user.nivel != 2:
                   
                    messages.error(request, 'No puede cambiar la clave del administrador por no tener los permisos suficientes')
                    return HttpResponseRedirect('/inventario/perfil/ver/%s' % p)  
            else:
                if request.user.is_superuser != True: 
                    messages.error(request, 'No puede cambiar la clave de este perfil por no tener los permisos suficientes')
                    return HttpResponseRedirect('/inventario/perfil/ver/%s' % p) 

                else:
                    if perf.is_superuser == True:
                        if request.user.nivel == 2:
                            pass

                        elif perf.id != request.user.id:
                            messages.error(request, 'No puedes cambiar la clave de un usuario de tu mismo nivel')
                            return HttpResponseRedirect('/inventario/perfil/ver/%s' % p) 


            form = ClaveFormulario(request.POST)
            contexto = { 'form':form, 'modo':request.session.get('perfilProcesado'),
            'editar':'clave','nombreUsuario':perf.username }            

            contexto = complementarContexto(contexto,request.user)
            return render(request, 'inventario/perfil/perfil.html', contexto)

        elif modo == 'ver':
            perf = Usuario.objects.get(id=p)
            contexto = { 'perfil':perf }      
            contexto = complementarContexto(contexto,request.user)
          
            return render(request,'inventario/perfil/verPerfil.html', contexto)



    def post(self,request,modo,p):
        if modo ==  'editar':
            form = UsuarioFormulario(request.POST)

            if form.is_valid():
                perf = Usuario.objects.get(id=p)
                if p != 1:
                    level = form.cleaned_data['level']        
                    perf.nivel = level
                    perf.is_superuser = level

                username = form.cleaned_data['username']
                first_name = form.cleaned_data['first_name']
                last_name = form.cleaned_data['last_name']
                email = form.cleaned_data['email']

                perf.username = username
                perf.first_name = first_name
                perf.last_name = last_name
                perf.email = email

                perf.save()
                
                form = UsuarioFormulario()
                messages.success(request, 'Actualizado exitosamente el perfil de ID %s.' % p)
                request.session['perfilProcesado'] = True           
                return HttpResponseRedirect("/inventario/perfil/ver/%s" % perf.id)
            else:
                #De lo contrario lanzara el mismo formulario
                return render(request, 'inventario/perfil/perfil.html', {'form': form})

        elif modo == 'clave':
            form = ClaveFormulario(request.POST)

            if form.is_valid():
                error = 0
                clave_nueva = form.cleaned_data['clave_nueva']
                repetir_clave = form.cleaned_data['repetir_clave']

                #================CONFIRMAR CLAVE ACTUAL PARA CAMBIO==================
                #clave = form.cleaned_data['clave']
                #correcto = authenticate(username=request.user.username , password=clave)

                #if correcto is not None:
                    #if clave_nueva == clave:
                        #error = 1
                        #messages.error(request,"La nueva contraseña es igual a la anterior") 

                usuario = Usuario.objects.get(id=p) 

                if repetir_clave != clave_nueva:
                    error = 1
                    messages.error(request,"Las contraseñas no coinciden")

                if(error == 0):
                    messages.success(request, 'Contraseña actualizada satisfactoriamente')
                    usuario.set_password(clave_nueva)
                    usuario.save()
                    return HttpResponseRedirect("/inventario/login")
                else:
                    return HttpResponseRedirect("/inventario/perfil/clave/%s" % p)


'''Vista para eliminar usuarios, productos, clientes o proveedores'''
class Eliminar(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request, modo, p):
        if modo == 'producto':
            prod = Producto.objects.get(id=p)
            prod.delete()
            messages.success(request, f"Producto de ID {p} borrado exitosamente.")
            return HttpResponseRedirect("/inventario/listarProductos")         
           
        elif modo == 'cliente':
            cliente = Cliente.objects.get(id=p)
            cliente.delete()
            messages.success(request, f"Cliente de ID {p} borrado exitosamente.")
            return HttpResponseRedirect("/inventario/listarClientes")            


        elif modo == 'proveedor':
            proveedor = Proveedor.objects.get(id=p)
            proveedor.delete()
            messages.success(request, f"Proveedor de ID {p} borrado exitosamente.")
            return HttpResponseRedirect("/inventario/listarProveedores")

        elif modo == 'usuario':
            if not request.user.is_superuser:
                messages.error(request, 'No tienes permisos suficientes para borrar usuarios')  
                return HttpResponseRedirect('/inventario/listarUsuarios')
            elif p == 1:
                messages.error(request, 'No puedes eliminar al super-administrador.')
                return HttpResponseRedirect('/inventario/listarUsuarios')  
            elif request.user.id == p:
                messages.error(request, 'No puedes eliminar tu propio usuario.')
                return HttpResponseRedirect('/inventario/listarUsuarios')                 
            else:
                usuario = Usuario.objects.get(id=p)
                usuario.delete()
                messages.success(request, f"Usuario de ID {p} borrado exitosamente.")
                return HttpResponseRedirect("/inventario/listarUsuarios")        


class ListarProductos(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request):
        productos = Producto.objects.all()
        contexto = {'tabla':productos}
        contexto = complementarContexto(contexto,request.user)  
        return render(request, 'inventario/producto/listarProductos.html',contexto)


class AgregarProducto(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def post(self, request):
        form = ProductoFormulario(request.POST)
        if form.is_valid():
            descripcion = form.cleaned_data['descripcion']
            precio = form.cleaned_data['precio']
            categoria = form.cleaned_data['categoria']
            tiene_iva = form.cleaned_data['tiene_iva']
            disponible = 0

            prod = Producto(descripcion=descripcion,precio=precio,categoria=categoria,tiene_iva=tiene_iva,disponible=disponible)
            prod.save()
            
            form = ProductoFormulario()
            messages.success(request, 'Ingresado exitosamente bajo la ID %s.' % prod.id)
            request.session['productoProcesado'] = 'agregado'
            return HttpResponseRedirect("/inventario/agregarProducto")
        else:
            #De lo contrario lanzara el mismo formulario
            return render(request, 'inventario/producto/agregarProducto.html', {'form': form})

    # Si se llega por GET crearemos un formulario en blanco
    def get(self,request):
        form = ProductoFormulario()
        #Envia al usuario el formulario para que lo llene
        contexto = {'form':form , 'modo':request.session.get('productoProcesado')}   
        contexto = complementarContexto(contexto,request.user)  
        return render(request, 'inventario/producto/agregarProducto.html', contexto)
        

class ImportarProductos(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def post(self,request):
        form = ImportarProductosFormulario(request.POST)
        if form.is_valid():
            request.session['productosImportados'] = True
            return HttpResponseRedirect("/inventario/importarProductos")

    def get(self,request):
        form = ImportarProductosFormulario()

        if request.session.get('productosImportados') == True:
            importado = request.session.get('productoImportados')
            contexto = { 'form':form,'productosImportados': importado  }
            request.session['productosImportados'] = False

        else:
            contexto = {'form':form}
            contexto = complementarContexto(contexto,request.user) 
        return render(request, 'inventario/producto/importarProductos.html',contexto)        


class ExportarProductos(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def post(self,request):
        form = ExportarProductosFormulario(request.POST)
        if form.is_valid():
            request.session['productosExportados'] = True

            #Se obtienen las entradas de producto en formato JSON
            data = serializers.serialize("json", Producto.objects.all())
            fs = FileSystemStorage('inventario/tmp/')

            #Se utiliza la variable fs para acceder a la carpeta con mas facilidad
            with fs.open("productos.json", "w") as out:
                out.write(data)
                out.close()  

            with fs.open("productos.json", "r") as out:                 
                response = HttpResponse(out.read(), content_type="application/force-download")
                response['Content-Disposition'] = 'attachment; filename="productos.json"'
                out.close() 
            #------------------------------------------------------------
            return response

    def get(self,request):
        form = ExportarProductosFormulario()

        if request.session.get('productosExportados') == True:
            exportado = request.session.get('productoExportados')
            contexto = { 'form':form,'productosExportados': exportado  }
            request.session['productosExportados'] = False

        else:
            contexto = {'form':form}
            contexto = complementarContexto(contexto,request.user) 
        return render(request, 'inventario/producto/exportarProductos.html',contexto)
        

class EditarProducto(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def post(self,request,p):
        # Crea una instancia del formulario y la llena con los datos:
        form = ProductoFormulario(request.POST)
        # Revisa si es valido:
        if form.is_valid():
            # Procesa y asigna los datos con form.cleaned_data como se requiere
            descripcion = form.cleaned_data['descripcion']
            precio = form.cleaned_data['precio']
            categoria = form.cleaned_data['categoria']
            tiene_iva = form.cleaned_data['tiene_iva']

            prod = Producto.objects.get(id=p)
            prod.descripcion = descripcion
            prod.precio = precio
            prod.categoria = categoria
            prod.tiene_iva = tiene_iva
            prod.save()
            form = ProductoFormulario(instance=prod)
            messages.success(request, 'Actualizado exitosamente el producto de ID %s.' % p)
            request.session['productoProcesado'] = 'editado'            
            return HttpResponseRedirect("/inventario/editarProducto/%s" % prod.id)
        else:
            #De lo contrario lanzara el mismo formulario
            return render(request, 'inventario/producto/agregarProducto.html', {'form': form})

    def get(self, request,p): 
        prod = Producto.objects.get(id=p)
        form = ProductoFormulario(instance=prod)
        #Envia al usuario el formulario para que lo llene
        contexto = {'form':form , 'modo':request.session.get('productoProcesado'),'editar':True}    
        contexto = complementarContexto(contexto,request.user) 
        return render(request, 'inventario/producto/agregarProducto.html', contexto)
        

class ListarClientes(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request):
        from django.db import models
        #Saca una lista de todos los clientes de la BDD
        clientes = Cliente.objects.all()                
        contexto = {'tabla': clientes}
        contexto = complementarContexto(contexto,request.user)         

        return render(request, 'inventario/cliente/listarClientes.html',contexto)


class AgregarCliente(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def post(self, request):
        # Crea una instancia del formulario y la llena con los datos:
        form = ClienteFormulario(request.POST)
        # Revisa si es valido:

        if form.is_valid():
            # Procesa y asigna los datos con form.cleaned_data como se requiere

            cedula = form.cleaned_data['cedula']
            nombre = form.cleaned_data['nombre']
            apellido = form.cleaned_data['apellido']
            direccion = form.cleaned_data['direccion']
            nacimiento = form.cleaned_data['nacimiento']
            telefono = form.cleaned_data['telefono']
            correo = form.cleaned_data['correo']
            telefono2 = form.cleaned_data['telefono2']
            correo2 = form.cleaned_data['correo2']

            cliente = Cliente(cedula=cedula,nombre=nombre,apellido=apellido,
                direccion=direccion,nacimiento=nacimiento,telefono=telefono,
                correo=correo,telefono2=telefono2,correo2=correo2)
            cliente.save()
            form = ClienteFormulario()

            messages.success(request, 'Ingresado exitosamente bajo la ID %s.' % cliente.id)
            request.session['clienteProcesado'] = 'agregado'
            return HttpResponseRedirect("/inventario/agregarCliente")
        else:
            #De lo contrario lanzara el mismo formulario
            return render(request, 'inventario/cliente/agregarCliente.html', {'form': form})        

    def get(self,request):
        form = ClienteFormulario()
        #Envia al usuario el formulario para que lo llene
        contexto = {'form':form , 'modo':request.session.get('clienteProcesado')} 
        contexto = complementarContexto(contexto,request.user)         
        return render(request, 'inventario/cliente/agregarCliente.html', contexto)
        

class ImportarClientes(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def post(self,request):
        form = ImportarClientesFormulario(request.POST)
        if form.is_valid():
            request.session['clientesImportados'] = True
            return HttpResponseRedirect("/inventario/importarClientes")

    def get(self,request):
        form = ImportarClientesFormulario()

        if request.session.get('clientesImportados') == True:
            importado = request.session.get('clientesImportados')
            contexto = { 'form':form,'clientesImportados': importado  }
            request.session['clientesImportados'] = False

        else:
            contexto = {'form':form}
            contexto = complementarContexto(contexto,request.user)             
        return render(request, 'inventario/cliente/importarClientes.html',contexto)
        

class ExportarClientes(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def post(self,request):
        form = ExportarClientesFormulario(request.POST)
        if form.is_valid():
            request.session['clientesExportados'] = True

            #Se obtienen las entradas de producto en formato JSON
            data = serializers.serialize("json", Cliente.objects.all())
            fs = FileSystemStorage('inventario/tmp/')

            #Se utiliza la variable fs para acceder a la carpeta con mas facilidad
            with fs.open("clientes.json", "w") as out:
                out.write(data)
                out.close()  

            with fs.open("clientes.json", "r") as out:                 
                response = HttpResponse(out.read(), content_type="application/force-download")
                response['Content-Disposition'] = 'attachment; filename="clientes.json"'
                out.close() 
            #------------------------------------------------------------
            return response

    def get(self,request):
        form = ExportarClientesFormulario()

        if request.session.get('clientesExportados') == True:
            exportado = request.session.get('clientesExportados')
            contexto = { 'form':form,'clientesExportados': exportado  }
            request.session['clientesExportados'] = False

        else:
            contexto = {'form':form}
            contexto = complementarContexto(contexto,request.user) 
        return render(request, 'inventario/cliente/exportarClientes.html',contexto)
        

class EditarCliente(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def post(self,request,p):
        # Crea una instancia del formulario y la llena con los datos:
        cliente = Cliente.objects.get(id=p)
        form = ClienteFormulario(request.POST, instance=cliente)
        # Revisa si es valido:
    
        if form.is_valid():           
            # Procesa y asigna los datos con form.cleaned_data como se requiere
            cedula = form.cleaned_data['cedula']
            nombre = form.cleaned_data['nombre']
            apellido = form.cleaned_data['apellido']
            direccion = form.cleaned_data['direccion']
            nacimiento = form.cleaned_data['nacimiento']
            telefono = form.cleaned_data['telefono']
            correo = form.cleaned_data['correo']
            telefono2 = form.cleaned_data['telefono2']
            correo2 = form.cleaned_data['correo2']

            cliente.cedula = cedula
            cliente.nombre = nombre
            cliente.apellido = apellido
            cliente.direccion = direccion
            cliente.nacimiento = nacimiento
            cliente.telefono = telefono
            cliente.correo = correo
            cliente.telefono2 = telefono2
            cliente.correo2 = correo2
            cliente.save()
            form = ClienteFormulario(instance=cliente)

            messages.success(request, 'Actualizado exitosamente el cliente de ID %s.' % p)
            request.session['clienteProcesado'] = 'editado'            
            return HttpResponseRedirect("/inventario/editarCliente/%s" % cliente.id)
        else:
            #De lo contrario lanzara el mismo formulario
            return render(request, 'inventario/cliente/agregarCliente.html', {'form': form})

    def get(self, request,p): 
        cliente = Cliente.objects.get(id=p)
        form = ClienteFormulario(instance=cliente)
        #Envia al usuario el formulario para que lo llene
        contexto = {'form':form , 'modo':request.session.get('clienteProcesado'),'editar':True} 
        contexto = complementarContexto(contexto,request.user)     
        return render(request, 'inventario/cliente/agregarCliente.html', contexto)
        

class EmitirFactura(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def post(self, request):
        # Crea una instancia del formulario y la llena con los datos:
        cedulas = Cliente.cedulasRegistradas()
        form = EmitirFacturaFormulario(request.POST,cedulas=cedulas)
        # Revisa si es valido:
        if form.is_valid():
            # Procesa y asigna los datos con form.cleaned_data como se requiere
            request.session['form_details'] = form.cleaned_data['productos']
            request.session['id_client'] = form.cleaned_data['cliente']
            return HttpResponseRedirect("detallesDeFactura")
        else:
            #De lo contrario lanzara el mismo formulario
            return render(request, 'inventario/factura/emitirFactura.html', {'form': form})

    def get(self, request):
        cedulas = Cliente.cedulasRegistradas()   
        form = EmitirFacturaFormulario(cedulas=cedulas)
        contexto = {'form':form, 'deshabilitar_entrada': ''}
        if len(cedulas) == 0:
            contexto['deshabilitar_entrada'] = 'disabled'
        contexto = complementarContexto(contexto,request.user) 
        return render(request, 'inventario/factura/emitirFactura.html', contexto)
        

class DetallesFactura(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request):
        cedula = request.session.get('id_client')
        productos = request.session.get('form_details')
        FacturaFormulario = formset_factory(DetallesFacturaFormulario, extra=productos)
        formset = FacturaFormulario()
        contexto = {'formset':formset}
        contexto = complementarContexto(contexto,request.user) 

        return render(request, 'inventario/factura/detallesFactura.html', contexto)        

    def post(self, request):
        cedula = request.session.get('id_client')
        productos = request.session.get('form_details')

        FacturaFormulario = formset_factory(DetallesFacturaFormulario, extra=productos)

        inicial = {
        'descripcion':'',
        'cantidad': 0,
        'subtotal':0,
        }

        data = {
    'form-TOTAL_FORMS': productos,
    'form-INITIAL_FORMS':0,
    'form-MAX_NUM_FORMS': '',
                }

        formset = FacturaFormulario(request.POST,data)


        if formset.is_valid():

            id_producto = []
            cantidad = []
            subtotal = []
            total_general = []
            sub_monto = 0
            monto_general = 0

            for form in formset:
                desc = form.cleaned_data['descripcion'].descripcion
                cant = form.cleaned_data['cantidad']
                sub = form.cleaned_data['valor_subtotal']
                id_producto.append(obtenerIdProducto(desc)) #funcion opcional
                cantidad.append(cant)
                subtotal.append(sub)

            #Ingresa la factura
            #--Saca el sub-monto
            for index in subtotal:
                sub_monto += index

            #--Saca el monto general
            for index,element in enumerate(subtotal):
                if productoTieneIva(id_producto[index]):
                    nuevoPrecio = sacarIva(element)   
                    monto_general += nuevoPrecio
                    total_general.append(nuevoPrecio)                     
                else:                   
                    monto_general += element
                    total_general.append(element)        

            from datetime import date

            cliente = Cliente.objects.get(cedula=cedula)
            iva = ivaActual('objeto')
            factura = Factura(cliente=cliente,fecha=date.today(),sub_monto=sub_monto,monto_general=monto_general,iva=iva)

            factura.save()
            id_factura = factura

            for indice,elemento in enumerate(id_producto):
                objetoProducto = obtenerProducto(elemento)
                cantidadDetalle = cantidad[indice]
                subDetalle = subtotal[indice]
                totalDetalle = total_general[indice]

                detalleFactura = DetalleFactura(id_factura=id_factura,id_producto=objetoProducto,cantidad=cantidadDetalle
                    ,sub_total=subDetalle,total=totalDetalle)

                objetoProducto.disponible -= cantidadDetalle
                objetoProducto.save()

                detalleFactura.save()  

            messages.success(request, 'Factura de ID %s insertada exitosamente.' % id_factura.id)
            return HttpResponseRedirect("/inventario/emitirFactura")    
    
    
class ListarFacturas(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request):
        #Lista de productos de la BDD
        facturas = Factura.objects.all()
        #Crea el paginador
                               
        contexto = {'tabla': facturas}
        contexto = complementarContexto(contexto,request.user) 

        return render(request, 'inventario/factura/listarFacturas.html', contexto)        


class VerFactura(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request, p):
        factura = Factura.objects.get(id=p)
        detalles = DetalleFactura.objects.filter(id_factura_id=p)
        contexto = {'factura':factura, 'detalles':detalles}
        contexto = complementarContexto(contexto,request.user)     
        return render(request, 'inventario/factura/verFactura.html', contexto)
        

class GenerarFactura(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request, p):
        import csv

        factura = Factura.objects.get(id=p)
        detalles = DetalleFactura.objects.filter(id_factura_id=p) 

        nombre_factura = "factura_%s.csv" % (factura.id)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="%s"' % nombre_factura
        writer = csv.writer(response)

        writer.writerow(['Producto', 'Cantidad', 'Sub-total', 'Total',
         'Porcentaje IVA utilizado: %s' % (factura.iva.valor_iva)])

        for producto in detalles:            
            writer.writerow([producto.id_producto.descripcion,producto.cantidad,producto.sub_total,producto.total])

        writer.writerow(['Total general:','','', factura.monto_general])

        return response


class GenerarFacturaPDF(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request, p):
        import io
        from reportlab.pdfgen import canvas
        import datetime

        factura = Factura.objects.get(id=p)
        general = Opciones.objects.get(id=1)
        detalles = DetalleFactura.objects.filter(id_factura_id=p)          

        data = {
             'fecha': factura.fecha, 
             'monto_general': factura.monto_general,
            'nombre_cliente': factura.cliente.nombre + " " + factura.cliente.apellido,
            'cedula_cliente': factura.cliente.cedula,
            'id_reporte': factura.id,
            'iva': factura.iva.valor_iva,
            'detalles': detalles,
            'modo': 'factura',
            'general':general
        }

        nombre_factura = "factura_%s.pdf" % (factura.id)

        pdf = render_to_pdf('inventario/PDF/prueba.html', data)
        response = HttpResponse(pdf,content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="%s"' % nombre_factura

        return response  


class ListarProveedores(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request):
        from django.db import models
        #Saca una lista de todos los clientes de la BDD
        proveedores = Proveedor.objects.all()                
        contexto = {'tabla': proveedores}
        contexto = complementarContexto(contexto,request.user)         

        return render(request, 'inventario/proveedor/listarProveedores.html',contexto) 
        

class AgregarProveedor(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def post(self, request):
        form = ProveedorFormulario(request.POST)

        if form.is_valid():
            
            cedula = form.cleaned_data['cedula']
            nombre = form.cleaned_data['nombre']
            apellido = form.cleaned_data['apellido']
            direccion = form.cleaned_data['direccion']
            nacimiento = form.cleaned_data['nacimiento']
            telefono = form.cleaned_data['telefono']
            correo = form.cleaned_data['correo']
            telefono2 = form.cleaned_data['telefono2']
            correo2 = form.cleaned_data['correo2']

            proveedor = Proveedor(cedula=cedula,nombre=nombre,apellido=apellido,
                direccion=direccion,nacimiento=nacimiento,telefono=telefono,
                correo=correo,telefono2=telefono2,correo2=correo2)
            proveedor.save()
            form = ProveedorFormulario()

            messages.success(request, 'Ingresado exitosamente bajo la ID %s.' % proveedor.id)
            request.session['proveedorProcesado'] = 'agregado'
            return HttpResponseRedirect("/inventario/agregarProveedor")
        else:
            #De lo contrario lanzara el mismo formulario
            return render(request, 'inventario/proveedor/agregarProveedor.html', {'form': form})        

    def get(self,request):
        form = ProveedorFormulario()
        #Envia al usuario el formulario para que lo llene
        contexto = {'form':form , 'modo':request.session.get('proveedorProcesado')} 
        contexto = complementarContexto(contexto,request.user)         
        return render(request, 'inventario/proveedor/agregarProveedor.html', contexto)
        

class ImportarProveedores(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def post(self,request):
        form = ImportarClientesFormulario(request.POST)
        if form.is_valid():
            request.session['clientesImportados'] = True
            return HttpResponseRedirect("/inventario/importarClientes")

    def get(self,request):
        form = ImportarClientesFormulario()

        if request.session.get('clientesImportados') == True:
            importado = request.session.get('clientesImportados')
            contexto = { 'form':form,'clientesImportados': importado  }
            request.session['clientesImportados'] = False

        else:
            contexto = {'form':form}
            contexto = complementarContexto(contexto,request.user)             
        return render(request, 'inventario/importarClientes.html',contexto)
        

class ExportarProveedores(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def post(self,request):
        form = ExportarClientesFormulario(request.POST)
        if form.is_valid():
            request.session['clientesExportados'] = True


            #Se obtienen las entradas de producto en formato JSON
            data = serializers.serialize("json", Cliente.objects.all())
            fs = FileSystemStorage('inventario/tmp/')

            #Se utiliza la variable fs para acceder a la carpeta con mas facilidad
            with fs.open("clientes.json", "w") as out:
                out.write(data)
                out.close()  

            with fs.open("clientes.json", "r") as out:                 
                response = HttpResponse(out.read(), content_type="application/force-download")
                response['Content-Disposition'] = 'attachment; filename="clientes.json"'
                out.close() 
            #------------------------------------------------------------
            return response

    def get(self,request):
        form = ExportarClientesFormulario()

        if request.session.get('clientesExportados') == True:
            exportado = request.session.get('clientesExportados')
            contexto = { 'form':form,'clientesExportados': exportado  }
            request.session['clientesExportados'] = False

        else:
            contexto = {'form':form}
            contexto = complementarContexto(contexto,request.user) 
        return render(request, 'inventario/exportarClientes.html',contexto)
        

class EditarProveedor(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def post(self,request,p):
        # Crea una instancia del formulario y la llena con los datos:
        proveedor = Proveedor.objects.get(id=p)
        form = ProveedorFormulario(request.POST, instance=proveedor)
        # Revisa si es valido:
      
        if form.is_valid():           
            # Procesa y asigna los datos con form.cleaned_data como se requiere
            cedula = form.cleaned_data['cedula']
            nombre = form.cleaned_data['nombre']
            apellido = form.cleaned_data['apellido']
            direccion = form.cleaned_data['direccion']
            nacimiento = form.cleaned_data['nacimiento']
            telefono = form.cleaned_data['telefono']
            correo = form.cleaned_data['correo']
            telefono2 = form.cleaned_data['telefono2']
            correo2 = form.cleaned_data['correo2']

            proveedor.cedula = cedula
            proveedor.nombre = nombre
            proveedor.apellido = apellido
            proveedor.direccion = direccion
            proveedor.nacimiento = nacimiento
            proveedor.telefono = telefono
            proveedor.correo = correo
            proveedor.telefono2 = telefono2
            proveedor.correo2 = correo2
            proveedor.save()
            form = ProveedorFormulario(instance=proveedor)

            messages.success(request, 'Actualizado exitosamente el proveedor de ID %s.' % p)
            request.session['proveedorProcesado'] = 'editado'            
            return HttpResponseRedirect("/inventario/editarProveedor/%s" % proveedor.id)
        else:
            #De lo contrario lanzara el mismo formulario
            return render(request, 'inventario/proveedor/agregarProveedor.html', {'form': form})

    def get(self, request,p): 
        proveedor = Proveedor.objects.get(id=p)
        form = ProveedorFormulario(instance=proveedor)
        #Envia al usuario el formulario para que lo llene
        contexto = {'form':form , 'modo':request.session.get('proveedorProcesado'),'editar':True} 
        contexto = complementarContexto(contexto,request.user)     
        return render(request, 'inventario/proveedor/agregarProveedor.html', contexto)  


class AgregarPedido(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request):
        cedulas = Proveedor.cedulasRegistradas()
        form = EmitirPedidoFormulario(cedulas=cedulas)
        contexto = {'form':form, 'deshabilitar_entrada': ''}
        if len(cedulas) == 0:
            contexto['deshabilitar_entrada'] = 'disabled'
        contexto = complementarContexto(contexto,request.user) 
        return render(request, 'inventario/pedido/emitirPedido.html', contexto)

    def post(self, request):
        # Crea una instancia del formulario y la llena con los datos:
        cedulas = Proveedor.cedulasRegistradas()
        form = EmitirPedidoFormulario(request.POST,cedulas=cedulas)
        # Revisa si es valido:
        if form.is_valid():
            # Procesa y asigna los datos con form.cleaned_data como se requiere
            request.session['form_details'] = form.cleaned_data['productos']
            request.session['id_proveedor'] = form.cleaned_data['proveedor']
            return HttpResponseRedirect("detallesPedido")
        else:
            #De lo contrario lanzara el mismo formulario
            return render(request, 'inventario/pedido/emitirPedido.html', {'form': form})


class ListarPedidos(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request):
        from django.db import models
        #Saca una lista de todos los clientes de la BDD
        pedidos = Pedido.objects.all()                
        contexto = {'tabla': pedidos}
        contexto = complementarContexto(contexto,request.user)         

        return render(request, 'inventario/pedido/listarPedidos.html',contexto) 


class DetallesPedido(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request):
        cedula = request.session.get('id_proveedor')
        productos = request.session.get('form_details')
        PedidoFormulario = formset_factory(DetallesPedidoFormulario, extra=productos)
        formset = PedidoFormulario()
        contexto = {'formset':formset}
        contexto = complementarContexto(contexto,request.user) 

        return render(request, 'inventario/pedido/detallesPedido.html', contexto)        

    def post(self, request):
        cedula = request.session.get('id_proveedor')
        productos = request.session.get('form_details')

        PedidoFormulario = formset_factory(DetallesPedidoFormulario, extra=productos)

        inicial = {
        'descripcion':'',
        'cantidad': 0,
        'subtotal':0,
        }

        data = {
    'form-TOTAL_FORMS': productos,
    'form-INITIAL_FORMS':0,
    'form-MAX_NUM_FORMS': '',
                }

        formset = PedidoFormulario(request.POST,data)

 
        if formset.is_valid():

            id_producto = []
            cantidad = []
            subtotal = []
            total_general = []
            sub_monto = 0
            monto_general = 0

            for form in formset:
                desc = form.cleaned_data['descripcion'].descripcion
                cant = form.cleaned_data['cantidad']
                sub = form.cleaned_data['valor_subtotal']
       
                id_producto.append(obtenerIdProducto(desc)) #esta funcion, a estas alturas, es innecesaria porque ya tienes la id
                cantidad.append(cant)
                subtotal.append(sub)        

            #Ingresa la factura
            #--Saca el sub-monto
            for index in subtotal:
                sub_monto += index

            #--Saca el monto general
            try:
                for index,element in enumerate(subtotal):
                    if productoTieneIva(id_producto[index]):
                        nuevoPrecio = sacarIva(element)
                        monto_general += nuevoPrecio
                        total_general.append(nuevoPrecio)                     
                    else:                   
                        monto_general += element
                        total_general.append(element) 
            except ErrorConfiguracionGeneralNoDefinida as c:
                messages.error(request, c.message)
                return HttpResponseRedirect("/inventario/detallesPedido")

            from datetime import date

            proveedor = Proveedor.objects.get(cedula=cedula)
            iva = ivaActual('objeto')
            presente = False
            pedido = Pedido(proveedor=proveedor,fecha=date.today(),sub_monto=sub_monto,monto_general=monto_general,iva=iva,
                presente=presente)

            pedido.save()
            id_pedido = pedido

            for indice,elemento in enumerate(id_producto):
                objetoProducto = obtenerProducto(elemento)
                cantidadDetalle = cantidad[indice]
                subDetalle = subtotal[indice]
                totalDetalle = total_general[indice]

                detallePedido = DetallePedido(id_pedido=id_pedido,id_producto=objetoProducto,cantidad=cantidadDetalle
                    ,sub_total=subDetalle,total=totalDetalle)
                detallePedido.save()  


            messages.success(request, 'Pedido de ID %s insertado exitosamente.' % id_pedido.id)
            return HttpResponseRedirect("/inventario/agregarPedido")     
    
    
class VerPedido(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request, p):
        pedido = Pedido.objects.get(id=p)
        detalles = DetallePedido.objects.filter(id_pedido_id=p)
        recibido = Pedido.recibido(p)
        contexto = {'pedido':pedido, 'detalles':detalles,'recibido': recibido}
        contexto = complementarContexto(contexto,request.user)     
        return render(request, 'inventario/pedido/verPedido.html', contexto)
        

class ValidarPedido(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request, p):
        pedido = Pedido.objects.get(id=p)
        detalles = DetallePedido.objects.filter(id_pedido_id=p)

        #Agrega los productos del pedido
        for elemento in detalles:
            elemento.id_producto.disponible += elemento.cantidad
            elemento.id_producto.save()

        pedido.presente = True
        pedido.save()
        messages.success(request, 'Pedido de ID %s verificado exitosamente.' % pedido.id)     
        return HttpResponseRedirect("/inventario/verPedido/%s" % p) 
        

class GenerarPedido(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request, p):
        import csv

        pedido = Pedido.objects.get(id=p)
        detalles = DetallePedido.objects.filter(id_pedido_id=p) 

        nombre_pedido = "pedido_%s.csv" % (pedido.id)

        response = HttpResponse(content_type='text/csv')

        response['Content-Disposition'] = 'attachment; filename="%s"' % nombre_pedido
        writer = csv.writer(response)

        writer.writerow(['Producto', 'Cantidad', 'Sub-total', 'Total',
         'Porcentaje IVA utilizado: %s' % (pedido.iva.valor_iva)])

        for producto in detalles:            
            writer.writerow([producto.id_producto.descripcion,producto.cantidad,producto.sub_total,producto.total])

        writer.writerow(['Total general:','','', pedido.monto_general])

        return response
        

class GenerarPedidoPDF(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request, p):

        pedido = Pedido.objects.get(id=p)
        general = Opciones.objects.get(id=1)
        detalles = DetallePedido.objects.filter(id_pedido_id=p)


        data = {
             'fecha': pedido.fecha, 
             'monto_general': pedido.monto_general,
            'nombre_proveedor': pedido.proveedor.nombre + " " + pedido.proveedor.apellido,
            'cedula_proveedor': pedido.proveedor.cedula,
            'id_reporte': pedido.id,
            'iva': pedido.iva.valor_iva,
            'detalles': detalles,
            'modo' : 'pedido',
            'general': general
        }

        nombre_pedido = "pedido_%s.pdf" % (pedido.id)

        pdf = render_to_pdf('inventario/PDF/prueba.html', data)
        response = HttpResponse(pdf,content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="%s"' % nombre_pedido

        return response
        

class CrearUsuario(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None    

    def get(self, request):
        if request.user.is_superuser:
            form = NuevoUsuarioFormulario()
            #Envia al usuario el formulario para que lo llene
            contexto = {'form':form , 'modo':request.session.get('usuarioCreado')}   
            contexto = complementarContexto(contexto,request.user)  
            return render(request, 'inventario/usuario/crearUsuario.html', contexto)
        else:
            messages.error(request, 'No tiene los permisos para crear un usuario nuevo')
            return HttpResponseRedirect('/inventario/panel')

    def post(self, request):
        form = NuevoUsuarioFormulario(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            rep_password = form.cleaned_data['rep_password']
            level = form.cleaned_data['level']

            error = 0

            if password == rep_password:
                pass

            else:
                error = 1
                messages.error(request, 'La clave y su repeticion tienen que coincidir')

            if usuarioExiste(Usuario,'username',username) is False:
                pass

            else:
                error = 1
                messages.error(request, "El nombre de usuario '%s' ya existe. eliga otro!" % username)


            if usuarioExiste(Usuario,'email',email) is False:
                pass

            else:
                error = 1
                messages.error(request, "El correo '%s' ya existe. eliga otro!" % email)                    

            if(error == 0):
                if level == '0':
                    nuevoUsuario = Usuario.objects.create_user(username=username,password=password,email=email)
                    nivel = 0
                elif level == '1':
                    nuevoUsuario = Usuario.objects.create_superuser(username=username,password=password,email=email)
                    nivel = 1

                nuevoUsuario.first_name = first_name
                nuevoUsuario.last_name = last_name
                nuevoUsuario.nivel = nivel
                nuevoUsuario.save()

                messages.success(request, 'Usuario creado exitosamente')
                return HttpResponseRedirect('/inventario/crearUsuario')

            else:
                return HttpResponseRedirect('/inventario/crearUsuario')


class ListarUsuarios(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None    

    def get(self, request):
        usuarios = Usuario.objects.all()
        #Envia al usuario el formulario para que lo llene
        contexto = {'tabla':usuarios}   
        contexto = complementarContexto(contexto,request.user)  
        return render(request, 'inventario/usuario/listarUsuarios.html', contexto)

    def post(self, request):
        pass   


class ImportarBDD(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request):
        if request.user.is_superuser == False:
            messages.error(request, 'Solo los administradores pueden importar una nueva base de datos')  
            return HttpResponseRedirect('/inventario/panel')

        form = ImportarBDDFormulario()
        contexto = { 'form': form }
        contexto = complementarContexto(contexto, request.user)
        return render(request, 'inventario/BDD/importar.html', contexto)

    def post(self, request):
        form = ImportarBDDFormulario(request.POST, request.FILES)

        if form.is_valid():
            ruta = 'inventario/archivos/BDD/inventario_respaldo.xml'
            manejarArchivo(request.FILES['archivo'],ruta)

            try:
                call_command('loaddata', ruta, verbosity=0)
                messages.success(request, 'Base de datos subida exitosamente')
                return HttpResponseRedirect('/inventario/importarBDD')
            except Exception:
                messages.error(request, 'El archivo esta corrupto')
                return HttpResponseRedirect('/inventario/importarBDD')


class DescargarBDD(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request):
        #Se obtiene la carpeta donde se va a guardar y despues se crea el respaldo ahi
        fs = FileSystemStorage('inventario/archivos/tmp/')
        with fs.open('inventario_respaldo.xml','w') as output:
            call_command('dumpdata','inventario',indent=4,stdout=output,format='xml', 
                exclude=['contenttypes', 'auth.permission'])

            output.close()

        #Descargar
        with fs.open('inventario_respaldo.xml','r') as output:
            response = HttpResponse(output.read(), content_type="application/force-download")
            response['Content-Disposition'] = 'attachment; filename="inventario_respaldo.xml"'

            #Cierra el archivo
            output.close()

            #Borra el archivo
            ruta = 'inventario/archivos/tmp/inventario_respaldo.xml'
            call_command('erasefile',ruta)

            #Regresa el archivo a descargar
            return response



class ConfiguracionGeneral(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request):
        try:
            conf = Opciones.objects.get(id=1)
            form = OpcionesFormulario()
            
            #Envia al usuario el formulario para que lo llene

            form['moneda'].field.widget.attrs['value']  = conf.moneda
            form['valor_iva'].field.widget.attrs['value']  = conf.valor_iva
            form['mensaje_factura'].field.widget.attrs['value']  = conf.mensaje_factura
            form['nombre_negocio'].field.widget.attrs['value']  = conf.nombre_negocio

            contexto = {'form':form}    
            contexto = complementarContexto(contexto,request.user) 
            return render(request, 'inventario/opciones/configuracion.html', contexto)
        except:
            form = OpcionesFormulario()
            contexto = {'form':form}    
            contexto = complementarContexto(contexto,request.user) 
            return render(request, 'inventario/opciones/configuracion.html', contexto)
            

    def post(self,request):
        # Crea una instancia del formulario y la llena con los datos:
        form = OpcionesFormulario(request.POST,request.FILES)
        # Revisa si es valido:

        if form.is_valid():
            # Procesa y asigna los datos con form.cleaned_data como se requiere
            moneda = form.cleaned_data['moneda']
            valor_iva = form.cleaned_data['valor_iva']
            mensaje_factura = form.cleaned_data['mensaje_factura']
            nombre_negocio = form.cleaned_data['nombre_negocio']
            imagen = request.FILES.get('imagen',False)

            #Si se subio un logo se sobreescribira en la carpeta ubicada
            #--en la siguiente ruta
            if imagen:
                manejarArchivo(imagen,'inventario/static/inventario/assets/logo/logo2.png')

            try:
                conf = Opciones.objects.get(id=1)
            except:
                conf = Opciones()
            finally:
                conf.moneda = moneda
                conf.valor_iva = valor_iva
                conf.mensaje_factura = mensaje_factura
                conf.nombre_negocio = nombre_negocio
                conf.save()


            messages.success(request, 'Configuracion actualizada exitosamente!')          
            return HttpResponseRedirect("/inventario/configuracionGeneral")
        else:
            form = OpcionesFormulario()
            #De lo contrario lanzara el mismo formulario
            return render(request, 'inventario/opciones/configuracion.html', {'form': form})

