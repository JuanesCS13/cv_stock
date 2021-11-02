import pytest
from inventario.models import Opciones


@pytest.mark.django_db
def test_crear_opciones():
    opciones = Opciones.objects.create(
        moneda = '$',
        valor_iva = 19,
        nombre_negocio = 'CV STOCK',
        mensaje_factura = 'Mensaje de prueba'
    )

    assert (opciones.moneda == '$'
            and opciones.valor_iva == 19
            and opciones.nombre_negocio == 'CV STOCK'
            and opciones.mensaje_factura == 'Mensaje de prueba'
            )