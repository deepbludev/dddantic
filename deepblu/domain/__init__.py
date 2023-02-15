from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError, create_model

from deepblu.result import Result, monadic

TSchema = TypeVar("TSchema", bound="Schema")


class Schema(BaseModel):
    ...


class ValidationResult(Result[TSchema, ValidationError]):
    ...


TPrimitive = TypeVar("TPrimitive", bound="Primitive")
TPrimitiveValue = TypeVar(
    "TPrimitiveValue", int, float, bool, str, bytes, None, tuple[Any, ...]
)


class Primitive:
    """
    Mixin class for primitive types, in order to enhance custom Pydantic
    types with some general functionality.

    Primitive types are types that are not composed of other types. They are
    the most basic types in a programming language. In Python, the primitive
    types are: int, float, bool, str, bytes, None, and tuple.

    Primitive types are immutable. Once they are created, their attributes
    cannot be changed. This makes them safe to share between different parts
    of the application.

    Primitive types are
    * Compared by value, not by identity.
    * Serializable. They can be converted to a string
    * Comparable. They can be compared using the == and !=
    * Hashable. They can be used as keys in a dictionary.
    * Immutable. Once they are created, their attributes cannot be changed.
    This makes them safe to share between different parts of the application.

    """

    @classmethod
    def parse(cls: type[TPrimitive], value: TPrimitiveValue) -> TPrimitiveValue:
        """
        Parses a value in order to check if it is valid without the need of
        adding it as a field in a Schema/BaseModel.
        """
        create_model("Validator", v=(cls, ...))(v=value)
        return value

    @classmethod
    def monadic_parse(
        cls: type[TPrimitive], value: TPrimitiveValue
    ) -> Result[TPrimitiveValue, ValidationError]:
        """
        Parses a value in order to check if it is valid without the need of
        adding it as a field in a Schema/BaseModel.
        """
        return monadic(cls.parse)(value)

    @classmethod
    def is_valid(cls, value: Any) -> bool:
        """Parses a value and returns True if it is valid, False otherwise."""
        return cls.monadic_parse(value).is_ok


TValueObject = TypeVar("TValueObject", bound="ValueObject")


class ValueObject(Schema):
    """
    Mixin class for value objects, in order to enhance custom Pydantic types
    with some general functionality.

    Value objects are immutable objects that represent a value, whether it's a
    monetary amount, a date range, a location on a map, or a person's name.
    In DDD, value objects are usually small objects that do not have an
    identity. They are defined by the attributes that they hold, not by a
    thread of continuity and identity.

    Value objects are compared by their attributes, not by identity.
    Two value objects are equal if they have the same attributes, regardless
    of whether they are the same object in memory.

    Value objects are immutable. Once they are created, their attributes cannot
    be changed. This makes them safe to share between different parts of the
    application.

    Value objects are serializable. They can be converted to a primitive type
    that can be stored in a database or sent over the network.

    Value objects are comparable. They can be compared to other value objects
    to check if they are equal or not.

    Value objects are hashable. They can be used as keys in dictionaries or
    elements in sets.

    Value objects are self-validating. They can validate their own invariants.
    This makes them easier to test.

    Value objects are small. They should not have much more behavior other than
    getters and setters for their attributes, except for specific cases, such as
    encrypting passwords or formatting dates.

    """

    class Config:
        allow_mutation = False

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.dict().items())))

    def clone(self: TValueObject) -> TValueObject:
        return self.copy()

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.dict() == other.dict()
