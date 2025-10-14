import argparse
import glob
import importlib
import inspect
import os
from types import ModuleType
from typing import TextIO, Any

import pyobs.vfs


def find_python_modules(pkg: type[Any], ignore_init: bool = True) -> list[ModuleType]:
    path = os.path.dirname(pkg.__file__)
    basename = pkg.__name__
    modules: list[ModuleType] = []
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in [f for f in filenames if f.endswith(".py")]:
            # ignore inits?
            if filename == "__init__.py" and ignore_init:
                continue

            # build module name
            mod = basename
            if dirpath != path:
                mod += "." + os.path.basename(dirpath)
            mod += "." + filename[:-3]

            # ignore module
            if filename[:-3] == "module":
                continue

            # append
            modules.append(importlib.import_module(mod))

    # finished
    return modules


def find_submodules(mod: ModuleType) -> list[ModuleType]:
    if mod.__file__ is None:
        return []
    path = os.path.dirname(mod.__file__)
    content = [os.path.basename(c) for c in sorted(glob.glob(os.path.join(path, "*"))) if os.path.isdir(c)]
    names = [c for c in content if c[0] not in [".", "_"]]
    return [importlib.import_module(mod.__name__ + "." + n) for n in names]


def find_classes_in_modules(modules: ModuleType | list[ModuleType]) -> list[type[Any]]:
    # make it a list
    if not isinstance(modules, list):
        modules = [modules]

    # init
    classes = []

    # loop modules
    for mod in modules:
        # no __all__?
        if not hasattr(mod, "__all__"):
            print("No __all__ found in %s." % mod.__file__)
            continue

        # loop all elements in __all__
        for o in mod.__all__:
            # get element
            tmp = getattr(mod, o)

            # we only want subclasses of Module
            if inspect.isclass(tmp):
                classes.append(tmp)

    # finished
    return classes


def write_class_rst(filename: str, cls: type[Any], **kwargs: Any) -> None:
    with open(filename, "w") as rst:
        write_class(rst, cls, **kwargs)


def write_class(
    rst: TextIO,
    cls: type[Any],
    title: bool = True,
    members: bool = False,
    inheritance: bool = False,
    undoc_members: bool = False,
    private: bool = False,
    header_level: int = 1,
    autotype: str = "autoclass",
    class_doc_from: str | None = None,
) -> None:
    name, module = cls.__name__, cls.__module__
    if title:
        write_title(rst, name, header_level)
    rst.write(".. %s:: %s.%s\n" % (autotype, module, name))
    if members:
        rst.write("   :members:\n")
    if inheritance:
        rst.write("   :show-inheritance:\n")
    if undoc_members:
        rst.write("   :undoc-members:\n")
    if private:
        rst.write("   :private-members:\n")
    if class_doc_from is not None:
        rst.write(f"   :class-doc-from: {class_doc_from}\n")
    rst.write("\n")


def write_title(rst: TextIO, title: str, header_level: int) -> None:
    rst.write("%s\n" % title)
    c = ["=", "-", "^", '"'][header_level]
    rst.write(c * len(title) + "\n\n")


def write_module_rst(filename: str, mod: ModuleType | list[ModuleType], header_level: int = 1, **kwargs: Any) -> None:
    # create path
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

    # make list
    if not isinstance(mod, list):
        mod = [mod]

    # write all mods
    first = True
    with open(filename, "w") as rst:
        for m in mod:
            write_module(rst, m, header_level=header_level, **kwargs)

            # increase header level
            if first:
                header_level += 1
            first = False


def write_module(
    rst: TextIO,
    mod: ModuleType,
    title: str | None = None,
    members: bool = False,
    imported: bool = False,
    header_level: int = 1,
    undoc_members: bool = False,
    ignore_classes: list[str] | None = None,
    classes: bool = False,
    class_kwargs: dict[str, Any] | None = None,
    **kwargs: Any,
) -> None:

    # does module have a title?
    if hasattr(mod, "__title__") and title is None:
        title = "%s (%s)" % (mod.__title__, mod.__name__)
    if title:
        write_title(rst, title, header_level)

    # automodule
    rst.write(".. automodule:: %s\n\n" % mod.__name__)

    # classes?
    if classes:
        class_kwargs = {} if class_kwargs is None else class_kwargs
        if "header_level" not in class_kwargs:
            class_kwargs["header_level"] = header_level + 1
        write_module_classes(rst, mod, ignore_classes=ignore_classes, **class_kwargs)


def write_module_classes(rst: TextIO, mod: ModuleType, ignore_classes: list[str] | None = None, **kwargs: Any) -> None:
    for _, c in inspect.getmembers(mod, lambda x: inspect.isclass(x) and x.__module__ == mod.__name__):
        if ignore_classes and c.__name__ in ignore_classes:
            continue
        write_class(rst, c, **kwargs)


def create_rst_overview(
    filename: str, title: str, package: ModuleType, base_class: type[Any] | None = None, **kwargs: Any
) -> None:
    # get all classes
    classes = sorted(list(filter(lambda m: inspect.isclass(m[1]), inspect.getmembers(package))))

    # open file
    with open(filename, "w") as rst:
        # header
        rst.write(title + "\n")
        rst.write("=" * len(title) + "\n\n")

        # write Interface
        if base_class:
            write_class(rst, base_class, title=False, **kwargs)

        # loop events
        for name, cls in classes:
            # no pyobs class?
            if not cls.__module__.startswith("pyobs"):
                continue

            # skip base class
            if base_class and name == base_class.__name__:
                continue

            # add it
            write_class(rst, cls, **kwargs)


def write_index_file(
    path: str, title: str | None = None, header_level: int = 1, module: ModuleType | None = None, **kwargs: Any
) -> None:
    with open(os.path.join(path, "index.rst"), "w") as rst:
        # write title
        if title:
            write_title(rst, title, header_level)

        # module?
        if module:
            write_module(rst, module, **kwargs)

        # write TOC
        write_index(rst, path, **kwargs)


def write_index(
    rst: TextIO, path: str, topics: list[str] | None = None, index_header: str = "Contents", **kwargs: Any
) -> None:
    # TOC
    rst.write(".. toctree::\n")
    rst.write("   :maxdepth: 2\n")
    rst.write(f"   :caption: {index_header}:\n\n")

    # topics or files?
    if topics:
        for t in topics:
            rst.write("   %s\n" % t)
    else:
        # loop all files
        for f in sorted(glob.glob(os.path.join(path, "*.rst"))):
            filename = os.path.basename(f)
            if filename == "index.rst":
                continue
            rst.write("   %s\n" % filename[:-4])


def create_utils_rst() -> None:
    import pyobs.utils.focusseries
    import pyobs.utils.simulation
    import pyobs.utils.skyflats
    import pyobs.utils.enums
    import pyobs.utils.time
    import pyobs.utils.archive
    import pyobs.utils.fits
    import pyobs.utils.exceptions
    import pyobs.utils.parallel
    import pyobs.utils.skyflats.pointing
    import pyobs.utils.skyflats.priorities

    # clean up
    os.system("rm -rf source/api/utils/*")

    # write
    write_module_rst(
        "source/api/utils/enums.rst",
        pyobs.utils.enums,
        classes=True,
        class_kwargs=dict(members=True, undoc_members=True),
    )
    write_module_rst("source/api/utils/time.rst", pyobs.utils.time, classes=True)
    write_module_rst("source/api/utils/archive.rst", pyobs.utils.archive, classes=True)
    write_module_rst("source/api/utils/fits.rst", pyobs.utils.fits, classes=True)
    write_module_rst(
        "source/api/utils/exceptions.rst",
        pyobs.utils.exceptions,
        classes=True,
        class_kwargs=dict(members=True, undoc_members=True, autotype="autoexception"),
    )
    write_module_rst("source/api/utils/focusseries.rst", pyobs.utils.focusseries, classes=True)
    write_module_rst("source/api/utils/simulation.rst", pyobs.utils.simulation, classes=True)
    write_module_rst(
        "source/api/utils/skyflats.rst",
        [pyobs.utils.skyflats, pyobs.utils.skyflats.pointing, pyobs.utils.skyflats.priorities],
        classes=True,
    )
    write_module_rst(
        "source/api/utils/parallel.rst",
        pyobs.utils.parallel,
        classes=True,
        class_kwargs=dict(members=True, undoc_members=True),
    )

    # write index file
    write_index_file("source/api/utils/", title="Utilities (pyobs.utils)", header_level=1)


def create_modules_rst() -> None:
    # clean up
    os.system("rm -rf source/modules/*")

    # first do pyobs.modules, since that's the more complicated case
    import pyobs.modules

    for module in find_submodules(pyobs.modules):
        # module
        write_module_rst(
            "source/modules/%s.rst" % module.__name__,
            module,
            classes=True,
            class_kwargs=dict(members=True, inheritance=True),
        )
    write_index_file("source/modules/", title="Core modules (pyobs.modules)", relative_title=False)

    # add to git
    os.system("git add source/modules/")


def create_image_processors_rst() -> None:
    import pyobs.images.processors

    # clean up
    os.system("rm -rf source/api/image_processors/*")

    # first do pyobs.modules, since that's the more complicated case
    for module in find_submodules(pyobs.images.processors):
        # module
        write_module_rst(
            "source/api/image_processors/%s.rst" % module.__name__,
            module,
            classes=True,
            class_kwargs=dict(members=True, undoc_members=True, class_doc_from="class"),
        )
    write_index_file(
        "source/api/image_processors/",
        title="Image processors",
        relative_title=False,
        module=pyobs.images.processors,
        index_header="List of image processors",
    )

    # add to git
    os.system("git add source/api/image_processors/")


if __name__ == "__main__":
    import pyobs.events
    import pyobs.interfaces
    import pyobs.images

    # command line parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", help="Re-create all", action="store_true")
    parser.add_argument("--events", help="Re-create source/api/events.rst", action="store_true")
    parser.add_argument("--interfaces", help="Re-create source/api/interfaces.rst", action="store_true")
    parser.add_argument("--utils", help="Re-create source/api/utils/*", action="store_true")
    parser.add_argument("--modules", help="Re-create source/api/modules/*", action="store_true")
    parser.add_argument("--images", help="Re-create source/api/images.rst", action="store_true")
    parser.add_argument("--vfs", help="Re-create source/api/vfs.rst", action="store_true")
    parser.add_argument("--mixins", help="Re-create source/api/mixins.rst", action="store_true")
    args = parser.parse_args()

    # run it
    if args.all or args.events:
        with open("source/api/events.rst", "w") as rst:
            write_module(rst, pyobs.events, title=None, classes=True)

    if args.all or args.interfaces:
        with open("source/api/interfaces.rst", "w") as rst:
            write_module(
                rst,
                pyobs.interfaces,
                header_level=1,
                classes=True,
                ignore_classes=["Interface"],
                class_kwargs=dict(members=True, inheritance=True, undoc_members=True),
            )

    if args.all or args.utils:
        create_utils_rst()

    if args.all or args.modules:
        create_modules_rst()

    if args.all or args.images:
        with open("source/api/images.rst", "w") as rst:
            write_module(rst, pyobs.images, header_level=1)
            write_class(rst, pyobs.images.Image, header_level=2)

        create_image_processors_rst()

    if args.all or args.vfs:
        with open("source/api/vfs.rst", "w") as rst:
            write_module(rst, pyobs.vfs, header_level=1)
            write_class(rst, pyobs.vfs.VirtualFileSystem, header_level=2)
            write_title(rst, "File Access Classes", 2)
            write_module_classes(rst, pyobs.vfs, ignore_classes=["VirtualFileSystem"], header_level=3)

    if args.all or args.mixins:
        with open("source/api/mixins.rst", "w") as rst:
            import pyobs.mixins

            write_module(rst, pyobs.mixins, header_level=1, classes=True, class_kwargs=dict(members=True, private=True))
