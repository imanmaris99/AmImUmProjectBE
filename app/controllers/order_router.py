from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session
from typing import List, Annotated

from app.services import order_services
from app.dtos import order_dtos

from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service


router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)

# @router.post(
#         "/create", 
#         response_model=order_dtos.OrderInfoResponseDto,
#         status_code=status.HTTP_201_CREATED,
#         responses={
#         status.HTTP_201_CREATED: {
#             "description": "Pesanan berhasil dibuat",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "status_code": 201,
#                         "message": "Your order has been saved",
#                         "data": {
#                             "id": "string",
#                             "status": "processing",
#                             "total_price": 200000,
#                             "shipment_id": 12345,
#                             "delivery_type": "delivery",
#                             "notes": "Please deliver in the morning",
#                             "created_at": "2024-11-23T11:47:19.027Z"
#                         }
#                     }
#                 }
#             }
#         },
#         status.HTTP_400_BAD_REQUEST: {
#             "description": "Data yang dikirim tidak valid",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "status_code": 400,
#                         "error": "Bad Request",
#                         "message": "Invalid order data."
#                     }
#                 }
#             }
#         },
#         status.HTTP_401_UNAUTHORIZED: {
#             "description": "Pengguna belum diotorisasi",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "status_code": 401,
#                         "error": "Unauthorized",
#                         "message": "You need to log in to perform this action."
#                     }
#                 }
#             }
#         },
#         status.HTTP_500_INTERNAL_SERVER_ERROR: {
#             "description": "Kesalahan server saat membuat pesanan",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "status_code": 500,
#                         "error": "Internal Server Error",
#                         "message": "Unexpected error occurred while creating the order."
#                     }
#                 }
#             }
#         }
#     },
#     summary="Create a new order"
#     )
# def create_order(
#     order_dto: order_dtos.OrderCreateDTO,
#     jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
#     db: Session = Depends(get_db)
# ):
#     """
#     # Membuat Pesanan Baru #

#     Endpoint ini digunakan untuk membuat pesanan baru oleh pengguna yang telah diautentikasi.
    
#     **Parameter:**
#     - **order_dto** (OrderCreateDTO): Data pesanan yang berisi tipe pengiriman, catatan, dan shipment ID.
#     - **jwt_token** (TokenPayLoad): Payload JWT dari token pengguna.
#     - **db** (Session): Koneksi database aktif.

#     **Return:**
#     - **201 Created**: Jika pesanan berhasil dibuat.
#     - **400 Bad Request**: Jika data pesanan tidak valid.
#     - **401 Unauthorized**: Jika pengguna belum login.
#     - **500 Internal Server Error**: Jika terjadi kesalahan server.

#     """
#     # Memanggil service untuk menambahkan item ke dalam cart
#     result = order_services.create_order(
#         db, 
#         order_dto, 
#         jwt_token.id
#     )

#     if result.error:
#         raise result.error

#     return result.unwrap()


@router.post(
    "/checkout",
    response_model=order_dtos.OrderInfoResponseDto,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Checkout berhasil dan order baru dibuat dari cart aktif.",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 201,
                        "message": "Your order has been created successfully.",
                        "data": {
                            "id": "c4b35d76-6e8d-4f4f-92d4-8d7d6a71f1d2",
                            "status": "pending",
                            "total_price": 67000,
                            "shipment_id": "5ed9d28a-6377-4f09-8d3c-8dbe49f628bf",
                            "delivery_type": "delivery",
                            "notes": None,
                            "created_at": "2026-04-21T20:25:31.120000+00:00"
                        }
                    }
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Cart aktif tidak ditemukan atau input checkout tidak valid.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status_code": 404,
                            "error": "Not Found",
                            "message": "Active cart items for user user-1 not found."
                        }
                    }
                }
            }
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "User belum login atau token tidak valid.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authenticated"
                    }
                }
            }
        },
        status.HTTP_409_CONFLICT: {
            "description": "Terjadi konflik saat akses database.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status_code": 409,
                            "error": "Conflict",
                            "message": "Database error: <detail konflik database>"
                        }
                    }
                }
            }
        }
    },
    summary="Initiate checkout"
)
def initiate_checkout(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    result = order_services.checkout(db, jwt_token.id)

    if result.error:
        raise result.error

    payload = result.data
    if isinstance(payload, dict):
        return JSONResponse(status_code=payload.get("status_code", 200), content=payload)
    
    return JSONResponse(status_code=200, content=payload)


@router.get(
    "/my-orders",
    response_model=order_dtos.GetOrderInfoResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Informasi pesanan berhasil diambil.",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Information about your order successfully retrieved",
                        "data": [
                            {
                                "id": "string",
                                "status": "string",
                                "total_price": 0,
                                "shipment_id": "string",
                                "delivery_type": "delivery",
                                "notes": "string",
                                "customer_name": "string",
                                "created_at": "2024-11-23T12:13:44.312Z",
                                "shipping_cost": 0,
                                "order_item_lists": [
                                    {
                                        "id": 0,
                                        "product_name": "string",
                                        "variant_product": "string",
                                        "variant_discount": 0,
                                        "quantity": 0,
                                        "price_per_item": 0,
                                        "total_price": 0,
                                        "created_at": "2024-11-23T12:13:44.312Z"
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Pengguna tidak memiliki akses karena token tidak valid atau tidak ada.",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 401,
                        "error": "Unauthorized",
                        "message": "Token tidak valid atau sudah kedaluwarsa."
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Data order tidak ditemukan untuk pengguna ini",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Tidak ada data order yang ditemukan untuk pengguna ini."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server saat mengambil pesanan.",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat mengambil informasi pesanan."
                    }
                }
            }
        }
    },
    summary="Get all orders by account login"
)
async def get_my_order(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    """
    # Get My Orders
    Endpoint ini mengambil semua pesanan milik akun yang sedang login.

    **Parameter:**
    - **jwt_token**: Payload dari JWT yang mengandung ID pengguna.
    - **db**: Koneksi database dari dependency.

    **Responses:**
    - **200 OK**: Informasi pesanan berhasil diambil.
    - **401 Unauthorized**: Token tidak valid atau pengguna tidak memiliki akses.
    - **404 Not Found**: Tidak ada data order yang ditemukan untuk pengguna ini.
    - **500 Internal Server Error**: Kesalahan server saat mengambil data pesanan.

    """
    result = order_services.my_order(db, jwt_token.id)

    if result.error:
        raise result.error
    
    return result.unwrap()

@router.get(
    "/detail/{order_id}",
    response_model=order_dtos.GetOrderDetailResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Detail order berhasil diambil.",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Order details accessed successfully",
                        "data": {
                            "id": "c4b35d76-6e8d-4f4f-92d4-8d7d6a71f1d2",
                            "status": "pending",
                            "total_price": 67000,
                            "delivery_type": "delivery",
                            "notes": "Tolong kirim sore hari",
                            "customer_name": "M Aris",
                            "created_at": "2026-04-21T20:25:31.120000+00:00",
                            "shipping_cost": 17000,
                            "my_shipping": {
                                "id": "5ed9d28a-6377-4f09-8d3c-8dbe49f628bf",
                                "my_address": {
                                    "id": 12,
                                    "name": "M Aris",
                                    "phone": "08123456789",
                                    "address": "Jl. Contoh No. 10, Jakarta",
                                    "created_at": "2026-04-20T09:00:00+00:00"
                                },
                                "my_courier": {
                                    "id": 4,
                                    "courier_name": "JNE",
                                    "weight": 1000,
                                    "service_type": "REG",
                                    "cost": 17000,
                                    "estimated_delivery": "2-3 hari",
                                    "created_at": "2026-04-20T09:05:00+00:00"
                                },
                                "created_at": "2026-04-20T09:10:00+00:00"
                            },
                            "order_item_lists": [
                                {
                                    "id": 1,
                                    "product_name": "Jahe Merah Instan",
                                    "variant_product": "Box 10 Sachet",
                                    "variant_discount": 10,
                                    "quantity": 2,
                                    "price_per_item": 25000,
                                    "total_price": 45000,
                                    "created_at": "2026-04-21T20:25:31.120000+00:00"
                                }
                            ]
                        }
                    }
                }
            }
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "User belum login atau token tidak valid.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authenticated"
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Order tidak ditemukan.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status_code": 404,
                            "error": "Not Found",
                            "message": "Order with ID order-x for user ID user-1 not found."
                        }
                    }
                }
            }
        },
        status.HTTP_409_CONFLICT: {
            "description": "Terjadi konflik saat akses database.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status_code": 409,
                            "error": "Conflict",
                            "message": "Database error: <detail konflik database>"
                        }
                    }
                }
            }
        }
    },
    summary="Get order detail"
)
def get_order_detail(
    order_id: str, 
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    
    # Panggil service detail_order
    result= order_services.detail_order(
        db=db,
        order_id=order_id,
        user_id=jwt_token.id
    )

    if result.error:
        # Tangani error jika terjadi
        raise result.error
    
    # Kembalikan data response jika berhasil
    return result.data


@router.put(
    "/complete-details/{order_id}", 
    response_model=order_dtos.OrderInfoResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Detail order berhasil diperbarui.",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Your order has been updated successfully.",
                        "data": {
                            "id": "c4b35d76-6e8d-4f4f-92d4-8d7d6a71f1d2",
                            "status": "pending",
                            "total_price": 67000,
                            "shipment_id": "5ed9d28a-6377-4f09-8d3c-8dbe49f628bf",
                            "delivery_type": "delivery",
                            "notes": "Tolong kirim sore hari",
                            "created_at": "2026-04-21T20:25:31.120000+00:00"
                        }
                    }
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Shipment tidak valid atau request body tidak sesuai.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid or inactive shipment. Please ensure shipment_id is valid."
                    }
                }
            }
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "User belum login atau token tidak valid.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authenticated"
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Order tidak ditemukan.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status_code": 404,
                            "error": "Not Found",
                            "message": "Your order with ID order-x was not found."
                        }
                    }
                }
            }
        },
        status.HTTP_409_CONFLICT: {
            "description": "Terjadi konflik saat akses database.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status_code": 409,
                            "error": "Conflict",
                            "message": "Database error: <detail konflik database>"
                        }
                    }
                }
            }
        }
    },
    summary="Update order details"
)
def update_order_details(
        order_updated: order_dtos.OrderIdCompleteDataDTO,
        order_dto: order_dtos.OrderCreateDTO,
        jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)
):
    result = order_services.edit_order(
        db, 
        order_updated=order_updated, 
        order_dto=order_dto, 
        user_id=jwt_token.id
    )

    if result.error:
        raise result.error
    
    return result.unwrap()