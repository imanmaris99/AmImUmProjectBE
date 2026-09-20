from pydantic import ValidationError

from app.dtos.courier_dtos import CourierCreateDto, CourierDataWeightUpdateDTO


def test_courier_create_accepts_jnt():
    dto = CourierCreateDto(courier_name="jnt", weight=1000)

    assert dto.courier_name == "jnt"
    assert dto.weight == 1000


def test_courier_weight_update_accepts_jnt():
    dto = CourierDataWeightUpdateDTO(courier_name="jnt", weight=1000)

    assert dto.courier_name == "jnt"


def test_courier_create_rejects_unknown_courier():
    try:
        CourierCreateDto(courier_name="ninja", weight=1000)
    except ValidationError:
        return

    raise AssertionError("unknown courier should be rejected")
