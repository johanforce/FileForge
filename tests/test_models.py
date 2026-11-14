import unittest

from fileforge.models import generate_models


SAMPLE = {
    "id": 10,
    "name": "An",
    "active": True,
    "profile": {"city": "Hà Nội", "nickname": None},
    "orders": [
        {"order_id": 1, "total": 12.5},
        {"order_id": 2, "total": 20, "note": "mới"},
    ],
    "optional-key": "value",
}


class ModelGenerationTests(unittest.TestCase):
    def test_generates_nested_dataclasses_and_optional_fields(self):
        code = generate_models(SAMPLE, "Customer", "dataclass")
        self.assertIn("class Customer:", code)
        self.assertIn("class Profile:", code)
        self.assertIn("class Order:", code)
        self.assertIn("orders: list[Order]", code)
        self.assertIn("note: str | None = None", code)
        self.assertIn("optional_key: str", code)

    def test_generates_pydantic_models(self):
        code = generate_models(SAMPLE, "Customer", "pydantic")
        self.assertIn("from pydantic import BaseModel, Field", code)
        self.assertIn("class Customer(BaseModel):", code)
        self.assertIn("Field(alias='optional-key')", code)

    def test_generates_typescript_interfaces(self):
        code = generate_models(SAMPLE, "Customer", "typescript")
        self.assertIn("export interface Customer", code)
        self.assertIn("export interface Order", code)
        self.assertIn('"optional-key": string;', code)
        self.assertIn("orders: Array<Order>;", code)

    def test_wraps_array_root_in_root_field(self):
        code = generate_models([{"id": 1}, {"id": 2}], "Root", "dataclass")
        self.assertIn("root: list[Root]", code)
        self.assertIn("class Root:", code)


if __name__ == "__main__":
    unittest.main()
