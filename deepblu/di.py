import inspect
from abc import ABC
from functools import wraps
from typing import Any, Callable, TypeVar, cast

TProviderValue = TypeVar("TProviderValue")
Provider = Callable[..., TProviderValue]
AnyProvider = Provider[Any]
Binding = tuple[Provider[TProviderValue], Provider[TProviderValue]]
AnyBinding = tuple[AnyProvider, AnyProvider]


class ProviderRegistry:
    """
    Provider registry for dependency injection.
    Used only as a singleton instance called `registry`, exported by the `di` module.

    """

    __slots__ = ("__bindings__", "__instances__")
    __bindings__: dict[AnyProvider, AnyProvider]
    __instances__: dict[AnyProvider, Any]

    def __init__(self) -> None:
        self.__bindings__ = {}
        self.__instances__ = {}

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
        try:
            instance = self.__instances__[interface]
        except KeyError:
            instance = self.__bindings__[interface]()
        self.__instances__[interface] = instance
        return cast(TProviderValue, instance)

    def __getitem__(self, interface: Provider[TProviderValue]) -> TProviderValue:
        """Get the implementation instance for an interface.""" ""
        return self.get(interface)

    @property
    def bindings(self) -> dict[AnyProvider, AnyProvider]:
        """Get current bindings"""
        return self.__bindings__


# Provider registry instance for dependency injection.
registry = ProviderRegistry()


def bind(interface: Provider[TProviderValue], impl: Provider[TProviderValue]) -> None:
    """Binds an interface to an implementation."""
    registry[interface] = impl


def add(provider: Provider[TProviderValue]) -> None:
    """Add a provider to the registry."""
    bind(provider, provider)


def bind_all(*providers: AnyBinding | AnyProvider) -> None:
    """Bind multiple interfaces to implementations.

    Args:
        providers: A list of Binding tuples of the
        form ```(interface, implementation)```.

    ```py title="Example:" linenums="1"
    di.bind_all(
        (DummyInterface, DummyImpl), (OtherDummyInterface, dummy_factory)
    )
    ```
    """
    for provider in providers:
        if isinstance(provider, tuple):
            interface, impl = provider
        else:
            interface, impl = provider, provider
        bind(interface, impl)


def get(interface: Provider[TProviderValue]) -> TProviderValue:
    """Get the implementation instance for an interface."""
    return registry[interface]


def provide_many(interface: AnyProvider, impls: list[AnyProvider]) -> AnyBinding:
    """Get a list of providers for a list of interfaces."""
    return (interface, lambda: [provider() for provider in impls])


def inject(func: Provider[TProviderValue]) -> Callable[..., TProviderValue]:
    """Decorator to inject dependencies into a function or `__init__` method."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> TProviderValue:
        annotations = inspect.getfullargspec(func).annotations
        for name, provider in annotations.items():
            if provider in registry.bindings and name not in kwargs:
                kwargs[name] = registry[provider]
        return func(*args, **kwargs)

    return wrapper


def injectable(cls: Provider[TProviderValue]) -> Provider[TProviderValue]:
    """Inject dependencies into a class `__init__`."""
    cls.__init__ = inject(cls.__init__)  # type: ignore
    return cls


ProviderList = list[AnyBinding | AnyProvider]


class Module(ABC):
    """
    A module is a collection of providers and imported submodules.

    It is used to organize the providers in a hierarchical way, and to
    provide a way to bind providers to the dependency injection container.

    A module can be imported by other modules, and its providers will be
    bound to the container when the module is imported, if the module class
    is decorated with the `module` decorator.
    """

    _imports: list[type["Module"]]
    _providers: ProviderList

    def get(self, interface: Provider[TProviderValue]) -> TProviderValue:
        """
        Returns an instance of the given interface.

        It is used to avoid the need to import the di container when using
        module-based dependency injection.
        """

        return get(interface)


def module(
    imports: list[type[Module]] | None = None,
    providers: ProviderList | None = None,
) -> Callable[[type[Module]], type[Module]]:
    """
    Decorator that binds the given providers and submodules to the module.

    The providers are bound to the di container when the module is imported.
    The submodules are imported when the module is imported, binding their own
    providers to the di container.

    This is useful to organize the providers in a hierarchical way.

    """

    def wrapper(cls: type[Module]) -> type[Module]:
        cls._imports = imports or []
        cls._providers = providers or []

        bind_all(*cls._providers)
        return cls

    return wrapper
