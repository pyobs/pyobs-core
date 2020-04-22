from .pyobs import init_cli, parse_cli, run


def main():
    from pyobs.application import GuiApplication

    # init argument parsing and parse it
    parser = init_cli()
    args = parse_cli(parser)

    # run app
    run(app_class=GuiApplication, **args)


if __name__ == '__main__':
    main()
