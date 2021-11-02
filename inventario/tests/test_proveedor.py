import pytest
from inventario.models import Proveedor


@pytest.mark.django_db
def test_crear_proveedor():
    proveedor = Proveedor.objects.create(
        cedula = '00112233',
        nacimiento = '2021-01-01',
    )

    assert (proveedor.cedula == '00112233'
            and proveedor.nacimiento == '2021-01-01'
            )
