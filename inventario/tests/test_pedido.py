import pytest
from inventario.models import Opciones, Pedido, Proveedor


@pytest.mark.django_db
def test_crear_pedido():
    proveedor = Proveedor.objects.create(
        cedula = '112233',
        nacimiento = '2021-01-01'
    )
    opciones = Opciones.objects.create(
        moneda = '$',
        valor_iva = 19,
        nombre_negocio = 'CV STOCK',
        mensaje_factura = 'Mensaje de prueba'
    )
    pedido = Pedido.objects.create(
        proveedor = proveedor,
        fecha = '2021-10-01',
        sub_monto = 15000.52,
        monto_general = 15000.52,
        iva = opciones,
    )

    assert (
        pedido.proveedor == proveedor,
        pedido.fecha == '2021-10-01',
        pedido.sub_monto == 15000.52,
        pedido.monto_general == 15000.52,
        pedido.iva == opciones,
    )