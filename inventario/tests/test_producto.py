import pytest
from inventario.models import Producto


@pytest.mark.django_db
def test_crear_producto():
    producto = Producto.objects.create(
        precio='12000',
        disponible=6,
        categoria='1',
        tiene_iva=True
    )

    assert (producto.precio == '12000' and producto.disponible == 6 and producto.categoria == '1'
            and producto.tiene_iva == True)
