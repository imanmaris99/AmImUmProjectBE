from decimal import Decimal

from app.dtos import cart_dtos


def get_cart_total(cart_items) -> cart_dtos.CartProductTotalDto:
    active_items = [item for item in cart_items if item.is_active]
    all_promo_active_prices = sum(Decimal(item.total_promo or 0) for item in active_items)
    all_item_active_prices = sum(Decimal(item.total_price_no_discount or 0) for item in active_items)
    total_all_active_prices = all_item_active_prices - all_promo_active_prices
    
    return cart_dtos.CartProductTotalDto(
        all_promo_active_prices=all_promo_active_prices,
        all_item_active_prices=all_item_active_prices,
        total_all_active_prices=total_all_active_prices
    )