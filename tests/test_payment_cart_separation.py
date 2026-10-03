import inspect


def test_payment_create_transaction_does_not_delete_cart_rows():
    from app.services.payment_services.create_transaction import create_transaction

    source = inspect.getsource(create_transaction)

    assert "CartProductModel" not in source
    assert ".delete()" not in source
    assert "cart:" not in source
    assert "carts:" not in source
