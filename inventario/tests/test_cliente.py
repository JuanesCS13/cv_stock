import pytest
from inventario.models import Cliente


@pytest.mark.django_db
def test_crear_cliente():
    cliente = Cliente.objects.create(
        cedula='11223344',
        nacimiento='2001-01-01'
    )

    assert (cliente.cedula == '11223344' and cliente.nacimiento == '2001-01-01')