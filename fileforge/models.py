"""Generate typed model declarations from a representative JSON object."""
from __future__ import annotations

import keyword
import json
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FieldSchema:
    json_name: str
    python_name: str
    type_name: str
    optional: bool
    nullable: bool


@dataclass
class ObjectSchema:
    name: str
    path: tuple[str, ...]
    fields: list[FieldSchema] = field(default_factory=list)


def _pascal(value: str) -> str:
    parts = re.findall(r"[A-Za-z0-9]+", value)
    result = "".join(part[:1].upper() + part[1:] for part in parts)
    if not result:
        result = "Generated"
    if result[0].isdigit():
        result = "Model" + result
    return result


def _singular(value: str) -> str:
    lower = value.lower()
    if lower.endswith("ies") and len(value) > 3:
        return value[:-3] + "y"
    if lower.endswith(("sses", "shes", "ches", "xes", "zes")):
        return value[:-2]
    if lower.endswith("s") and not lower.endswith(("ss", "us", "is")):
        return value[:-1]
    return value


def _identifier(value: str) -> str:
    name = re.sub(r"\W", "_", value, flags=re.UNICODE)
    if not name:
        name = "field"
    if name[0].isdigit():
        name = "field_" + name
    if keyword.iskeyword(name):
        name += "_"
    return name


class _ModelBuilder:
    def __init__(self, root_name: str):
        self.root_name = _pascal(root_name)
        self.schemas: dict[tuple[str, ...], ObjectSchema] = {}
        self.used_names: dict[str, tuple[str, ...]] = {}

    def _claim_name(self, proposed: str, path: tuple[str, ...]) -> str:
        base = _pascal(proposed)
        name = base
        if name in self.used_names and self.used_names[name] != path:
            parent = _pascal(path[-2]) if len(path) > 1 else "Nested"
            name = parent + base
        suffix = 2
        candidate = name
        while candidate in self.used_names and self.used_names[candidate] != path:
            candidate = f"{name}{suffix}"
            suffix += 1
        self.used_names[candidate] = path
        return candidate

    def build(self, value: dict[str, Any]) -> list[ObjectSchema]:
        self._build_object(("$",), self.root_name, [value])
        return list(self.schemas.values())

    def _build_object(
        self,
        path: tuple[str, ...],
        proposed_name: str,
        objects: list[dict[str, Any]],
    ) -> str:
        if path in self.schemas:
            return self.schemas[path].name

        class_name = self._claim_name(proposed_name, path)
        schema = ObjectSchema(class_name, path)
        self.schemas[path] = schema

        keys: list[str] = []
        for obj in objects:
            for key in obj:
                if key not in keys:
                    keys.append(key)

        pending: list[FieldSchema] = []
        used_field_names: set[str] = set()
        for key in keys:
            values = [obj[key] for obj in objects if key in obj]
            optional = len(values) < len(objects)
            nullable = any(value is None for value in values)
            non_null = [value for value in values if value is not None]
            type_name = self._infer_values(
                non_null,
                path + (key,),
                class_name,
                key,
            )
            if nullable:
                type_name = self._union([type_name, "None"])

            python_name = _identifier(key)
            base_name = python_name
            suffix = 2
            while python_name in used_field_names:
                python_name = f"{base_name}_{suffix}"
                suffix += 1
            used_field_names.add(python_name)

            pending.append(
                FieldSchema(
                    json_name=key,
                    python_name=python_name,
                    type_name=type_name,
                    optional=optional,
                    nullable=nullable,
                )
            )

        # Dataclass fields with defaults must follow required fields.
        schema.fields = sorted(pending, key=lambda item: item.optional)
        return class_name

    @staticmethod
    def _union(types: list[str]) -> str:
        unique = list(dict.fromkeys(types))
        if not unique:
            return "Any"
        if "float" in unique and "int" in unique:
            unique.remove("int")
        if len(unique) == 1:
            return unique[0]
        return " | ".join(unique)

    def _infer_values(
        self,
        values: list[Any],
        path: tuple[str, ...],
        parent_name: str,
        field_name: str,
    ) -> str:
        if not values:
            return "Any"

        inferred: list[str] = []
        object_values = [value for value in values if isinstance(value, dict)]
        if object_values:
            inferred.append(
                self._build_object(path, _pascal(field_name), object_values)
            )

        list_values = [value for value in values if isinstance(value, list)]
        if list_values:
            all_items = [item for group in list_values for item in group]
            object_items = [item for item in all_items if isinstance(item, dict)]
            item_types: list[str] = []

            if object_items:
                item_types.append(
                    self._build_object(
                        path + ("[]",),
                        _pascal(_singular(field_name)),
                        object_items,
                    )
                )

            for item in all_items:
                if not isinstance(item, dict):
                    item_types.append(
                        self._infer_value(
                            item, path + ("[]",), parent_name, field_name
                        )
                    )

            element_type = self._union(item_types) if item_types else "Any"
            inferred.append(f"list[{element_type}]")

        for value in values:
            if not isinstance(value, (dict, list)):
                inferred.append(
                    self._infer_value(value, path, parent_name, field_name)
                )

        return self._union(inferred)

    def _infer_value(
        self,
        value: Any,
        path: tuple[str, ...],
        parent_name: str,
        field_name: str,
    ) -> str:
        if value is None:
            return "None"
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        if isinstance(value, str):
            return "str"
        if isinstance(value, dict):
            proposed = _pascal(field_name)
            return self._build_object(path, proposed, [value])
        if isinstance(value, list):
            if not value:
                return "list[Any]"
            object_values = [item for item in value if isinstance(item, dict)]
            if object_values:
                item_name = _pascal(_singular(field_name))
                item_path = path + ("[]",)
                object_type = self._build_object(
                    item_path,
                    item_name,
                    object_values,
                )
                other_types = [
                    self._infer_value(item, item_path, parent_name, field_name)
                    for item in value
                    if not isinstance(item, dict)
                ]
                item_type = self._union([object_type] + other_types)
            else:
                item_types = [
                    self._infer_value(item, path + ("[]",), parent_name, field_name)
                    for item in value
                ]
                item_type = self._union(item_types)
            return f"list[{item_type}]"
        return "Any"


def _render_python(schemas: list[ObjectSchema], style: str) -> str:
    lines: list[str] = ["from __future__ import annotations", ""]
    if style == "dataclass":
        lines += ["from dataclasses import dataclass", "from typing import Any", ""]
    else:
        lines += ["from pydantic import BaseModel, Field", "from typing import Any", ""]

    for schema in reversed(schemas):
        if style == "dataclass":
            lines.append("@dataclass")
        lines.append(f"class {schema.name}({'' if style == 'dataclass' else 'BaseModel'}):" if style != "dataclass" else f"class {schema.name}:")
        if not schema.fields:
            lines.append("    pass")
        for item in schema.fields:
            annotation = item.type_name
            default = ""
            if item.optional:
                annotation = f"{annotation} | None"
                default = " = None"
            alias_needed = item.python_name != item.json_name
            if style == "pydantic" and alias_needed:
                alias = repr(item.json_name)
                default = f" = Field(default=None, alias={alias})" if item.optional else f" = Field(alias={alias})"
            elif style == "pydantic" and item.optional:
                default = " = None"
            comment = ""
            if style == "dataclass" and alias_needed:
                comment = f"  # Khóa JSON: {item.json_name!r}"
            lines.append(
                f"    {item.python_name}: {annotation}{default}{comment}"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _to_typescript_type(type_name: str) -> str:
    replacements = {
        "str": "string",
        "int": "number",
        "float": "number",
        "bool": "boolean",
        "None": "null",
        "Any": "unknown",
    }
    if type_name.startswith("list[") and type_name.endswith("]"):
        inner = type_name[5:-1]
        if " | " in inner:
            inner = f"({ _to_typescript_type(inner) })"
        else:
            inner = _to_typescript_type(inner)
        return f"Array<{inner}>"
    return " | ".join(replacements.get(part, part) for part in type_name.split(" | "))


def _render_typescript(schemas: list[ObjectSchema]) -> str:
    lines: list[str] = []
    for schema in reversed(schemas):
        lines.append(f"export interface {schema.name} {{")
        if not schema.fields:
            lines.append("}")
            lines.append("")
            continue
        for item in schema.fields:
            property_name = (
                item.json_name
                if re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", item.json_name)
                else json.dumps(item.json_name, ensure_ascii=False)
            )
            optional = "?" if item.optional else ""
            type_name = _to_typescript_type(item.type_name)
            if item.nullable and "null" not in type_name.split(" | "):
                type_name += " | null"
            lines.append(f"  {property_name}{optional}: {type_name};")
        lines.append("}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"



def _language_field_name(value: str, target: str) -> str:
    name = _identifier(value)
    if target in {"java", "kotlin"}:
        parts = name.split("_")
        name = parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])
    if target == "kotlin" and name in {"class", "object", "when", "is", "in", "fun", "val", "var"}:
        name += "_"
    return name


def _simple_type(type_name: str) -> tuple[str, bool]:
    parts = type_name.split(" | ")
    nullable = "None" in parts
    parts = [part for part in parts if part != "None"]
    base = parts[0] if parts else "Any"
    if len(parts) > 1:
        base = "float" if set(parts) <= {"int", "float"} else "Any"
    return base, nullable


def _java_type(type_name: str) -> str:
    base, _ = _simple_type(type_name)
    if base.startswith("list[") and base.endswith("]"):
        return f"List<{_java_type(base[5:-1])}>"
    return {"str": "String", "int": "Long", "float": "Double", "bool": "Boolean", "Any": "Object"}.get(base, base)


def _kotlin_type(type_name: str) -> tuple[str, bool]:
    base, nullable = _simple_type(type_name)
    if base.startswith("list[") and base.endswith("]"):
        inner, inner_nullable = _kotlin_type(base[5:-1])
        rendered = f"List<{inner}{'?' if inner_nullable else ''}>"
    else:
        rendered = {"str": "String", "int": "Long", "float": "Double", "bool": "Boolean", "Any": "Any"}.get(base, base)
    return rendered, nullable


def _render_java(schemas: list[ObjectSchema]) -> str:
    lines = ["import java.util.List;", ""]
    for schema in reversed(schemas):
        lines.append(f"class {schema.name} {{")
        if not schema.fields:
            lines.append("    // No fields")
        for item in schema.fields:
            field_name = _language_field_name(item.json_name, "java")
            lines.append(f"    public {_java_type(item.type_name)} {field_name};")
        lines.extend(["}", ""])
    return "\n".join(lines).rstrip() + "\n"


def _render_kotlin(schemas: list[ObjectSchema]) -> str:
    lines = []
    for schema in reversed(schemas):
        fields = []
        for item in schema.fields:
            field_name = _language_field_name(item.json_name, "kotlin")
            type_name, nullable = _kotlin_type(item.type_name)
            if nullable or item.optional:
                type_name += "?"
            default = " = null" if item.optional else ""
            fields.append(f"    val {field_name}: {type_name}{default}")
        if not fields:
            lines.append(f"data class {schema.name}()")
        else:
            lines.extend([f"data class {schema.name}(", ",\n".join(fields), ")"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _c_identifier(value: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if not name or name[0].isdigit():
        name = "field_" + name
    return name


def _c_type(type_name: str) -> tuple[str, bool, bool]:
    base, nullable = _simple_type(type_name)
    is_array = base.startswith("list[") and base.endswith("]")
    if is_array:
        base, inner_nullable = _simple_type(base[5:-1])
        nullable = nullable or inner_nullable
    mapped = {"str": "char *", "int": "int64_t", "float": "double", "bool": "bool", "Any": "void *"}.get(base, base)
    return mapped, nullable, is_array


def _render_c(schemas: list[ObjectSchema]) -> str:
    lines = ["#include <stdbool.h>", "#include <stddef.h>", "#include <stdint.h>", ""]
    for schema in reversed(schemas):
        lines.append(f"typedef struct {schema.name} {{")
        if not schema.fields:
            lines.append("    /* No fields */")
        for item in schema.fields:
            ctype, _nullable, is_array = _c_type(item.type_name)
            field_name = _c_identifier(item.json_name)
            if is_array:
                pointer = "*" if ctype.endswith("*") else " *"
                lines.extend([f"    {ctype}{pointer} {field_name};", f"    size_t {field_name}_count;"])
            elif item.optional and not ctype.endswith("*"):
                lines.append(f"    {ctype} *{field_name}; /* optional */")
            elif ctype.endswith("*"):
                lines.append(f"    {ctype}{field_name};")
            else:
                lines.append(f"    {ctype} {field_name};")
        lines.extend([f"}} {schema.name};", ""])
    return "\n".join(lines).rstrip() + "\n"

def generate_models(
    data: Any,
    class_name: str = "RootModel",
    target: str = "dataclass",
) -> str:
    """Generate dataclass, Pydantic v2, or TypeScript declarations from JSON."""
    if not isinstance(data, dict):
        # Preserve array/scalar roots by wrapping them in a named root field.
        data = {"root": data}

    if target not in {"dataclass", "pydantic", "typescript", "java", "kotlin", "c"}:
        raise ValueError(f"Kiểu model không được hỗ trợ: {target}")

    builder = _ModelBuilder(class_name or "RootModel")
    schemas = builder.build(data)

    if target == "typescript":
        return _render_typescript(schemas)
    if target == "java":
        return _render_java(schemas)
    if target == "kotlin":
        return _render_kotlin(schemas)
    if target == "c":
        return _render_c(schemas)
    return _render_python(schemas, target)
