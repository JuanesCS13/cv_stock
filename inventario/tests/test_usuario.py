import pytest
from inventario.models import Usuario


@pytest.mark.django_db
def test_crear_usuario():
    user = Usuario.objects.create_user(
        username='prueba1',
        email='prueba1@example.com',
        password='password12345'
    )

    assert user.username == 'prueba1'

@pytest.mark.django_db
def test_crear_superusuario():
    user = Usuario.objects.create_superuser(
        username='prueba1',
        email='prueba1@example.com',
        password='password12345'
    )

    assert user.is_superuser