import pytest
from inventario.models import Cliente, Factura, Opciones


@pytest.mark.django_db
def test_crear_factura():
    cliente = Cliente.objects.create(
        cedula='11223344',
        nacimiento='2001-01-01'
    )
    opciones = Opciones.objects.create(
        moneda = '$',
        valor_iva = 19,
        nombre_negocio = 'CV STOCK',
        mensaje_factura = 'Mensaje prueba'
    )
    factura = Factura.objects.create(
        cliente=cliente,
        fecha='2021-10-01',
        sub_monto = 12500.23,
        monto_general = 12500.23,
        iva = opciones
    )

    assert (factura.cliente == cliente)