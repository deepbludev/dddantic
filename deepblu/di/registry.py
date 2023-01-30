from typing import Any, Callable, TypeVar, cast

TProviderValue = TypeVar("TProviderValue")
Provider = Callable[..., TProviderValue]
AnyProvider = Provider[Any]
Binding = tuple[Provider[TProviderValue], Provider[TProviderValue]]
AnyBinding = tuple[AnyProvider, AnyProvider]


class ProviderRegistry:
    """Provider registry for dependency injection.

    Used only as a singleton instance called `registry`, exported by the `di` module.

    ```py title="Example:"
    from deepblu.di import registry

    registry.bind(Interface, Implementation)
    registry[OtherInterface] = OtherImplementation

    isinstance(registry[Interface], Implementation) # True
    isinstance(registry.get(OtherInterface), OtherImplementation) # True

    registry.bindings
    # {Interface: Implementation, OtherInterface: OtherImplementation}

    ```
    """

    __slots__ = "__bindings__"
    __bindings__: dict[AnyProvider, AnyProvider]

    def __init__(self) -> None:
        self.__bindings__ = {}

    def bind(
        self, interface: Provider[TProviderValue], impl: Provider[TProviderValue]
    ) -> "ProviderRegistry":
        """Bind an interface to an implementation."""
        self.__bindings__[interface] = impl
        return self

    def __setitem__(
        self, interface: Provider[TProviderValue], impl: Provider[TProviderValue]
    ) -> "ProviderRegistry":
        """Bind an interface to an implementation."""
        return self.bind(interface, impl)

    def get(self, interface: Provider[TProviderValue]) -> TProviderValue:
        """Get the implementation instance for an interface."""
        return cast(TProviderValue, self.__bindings__[interface]())

    def __getitem__(self, interface: Provider[TProviderValue]) -> TProviderValue:
        """Get the implementation instance for an interface.""" ""
        return self.get(interface)

    @property
    def bindings(self) -> dict[AnyProvider, AnyProvider]:
        """Get current bindings"""
        return self.__bindings__
