import pytest
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.urls import reverse
from model_bakery import baker


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db, client, django_user_model):
    data = {
        'username': 'test-user',
        'email': 'test-user@mail.com',
        'password': 'Test-Password123'
    }
    user = django_user_model.objects.create_user(**data)
    client.force_login(user)

    return user


@pytest.fixture
def token(db, client, user):
    Token.objects.create(user=user)
    token = Token.objects.get(user=user)

    return token


@pytest.fixture
def auth_client(db, client, user, token):
    client.force_authenticate(user=user, token=token)

    return client


@pytest.fixture
def shop_factory(user_partner):
    def factory(**kwargs):
        return baker.make('Shop', user=user_partner, **kwargs)

    return factory


@pytest.fixture
def order_factory():
    def factory(**kwargs):
        return baker.make('Order', **kwargs)

    return factory


@pytest.fixture
def product_info_factory():
    def factory(**kwargs):
        category = baker.make('Category', **kwargs)
        product = baker.make('Product', category_id=category.id, **kwargs)
        shop = baker.make('Shop', **kwargs)
        return baker.make('ProductInfo', product_id=product.id, shop_id=shop.id, **kwargs)

    return factory


@pytest.fixture
def user_partner(db, client, django_user_model):
    data = {
        "email": "test_partner@mail.com",
        "password": "!QAZzaq1",
        "type": "shop",
    }
    user_partner = django_user_model.objects.create_user(
        email=data['email'],
        password=data['password'],
        type=data['type']
    )
    client.force_login(user_partner)

    return user_partner


@pytest.fixture
def partner_token(db, client, user_partner):
    Token.objects.create(user=user_partner)
    partner_token = Token.objects.get(user=user_partner)

    return partner_token


@pytest.fixture
def auth_partner(db, client, user_partner, partner_token):
    client.force_authenticate(user=user_partner, token=partner_token)

    return client


@pytest.mark.django_db
def test_get_basket(user, auth_client, order_factory):
    order_factory(make_m2m=True, user=user)
    url = reverse('basket')
    resp = auth_client.get(url)
    assert resp.status_code == 200


@pytest.mark.django_db
def test_add_items_to_basket(user, auth_client, order_factory, product_info_factory):
    created_item = product_info_factory(make_m2m=True)
    order_factory(make_m2m=True, user=user)
    url = reverse('basket')
    resp = auth_client.post(
        url,
        {'items': f'[{{"product_info": {created_item.id}, "quantity": "1"}}]'}
    )

    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json['Status'] is True


@pytest.mark.django_db
def test_partner_get_status(auth_partner, shop_factory):
    shop = shop_factory(make_m2m=True)
    url = reverse('partner-state')
    resp = auth_partner.get(url)
    resp_json = resp.json()

    assert resp.status_code == 200
    assert resp_json['id'] == shop.id
    assert resp_json['state'] == shop.state


@pytest.mark.django_db
def test_partner_update_status(auth_partner, shop_factory):
    shop_factory(make_m2m=True)
    url = reverse('partner-state')
    resp = auth_partner.post(url, {'state': 'on'})
    resp_json = resp.json()
    print(resp_json)
    assert resp.status_code == 200
    assert resp_json['Status'] is True
