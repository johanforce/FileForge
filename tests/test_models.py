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
        compile(code, "<generated-model>", "exec")

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

    def test_generates_java_classes(self):
        code = generate_models(SAMPLE, "Customer", "java")
        self.assertIn("class Customer {", code)
        self.assertIn("class Profile {", code)
        self.assertIn("List<Order> orders;", code)
        self.assertIn("String optionalKey;", code)
        self.assertIn("import java.util.List;", code)

    def test_generates_kotlin_data_classes(self):
        code = generate_models(SAMPLE, "Customer", "kotlin")
        self.assertIn("data class Customer(", code)
        self.assertIn("data class Profile(", code)
        self.assertIn("val nickname: Any?", code)
        self.assertIn("val note: String? = null", code)
        self.assertIn("List<Order>", code)

    def test_generates_c_structs(self):
        code = generate_models(SAMPLE, "Customer", "c")
        self.assertIn("#include <stdint.h>", code)
        self.assertIn("typedef struct Customer", code)
        self.assertIn("Order *orders;", code)
        self.assertIn("size_t orders_count;", code)
        self.assertIn("char *name;", code)

    def test_merges_nested_objects_from_array_samples(self):
        data = {
            "items": [
                {"meta": {"id": 1}},
                {"meta": {"name": "second"}},
            ]
        }
        code = generate_models(data, "RootModel", "dataclass")
        self.assertIn("id: int | None = None", code)
        self.assertIn("name: str | None = None", code)

    def test_wraps_array_root_in_root_field(self):
        code = generate_models([{"id": 1}, {"id": 2}], "RootModel", "dataclass")
        self.assertIn("root: list[Root]", code)
        self.assertIn("class Root:", code)


if __name__ == "__main__":
    unittest.main()
