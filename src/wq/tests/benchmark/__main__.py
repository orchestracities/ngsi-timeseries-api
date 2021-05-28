import click

from wq.tests.benchmark.driver import TestScript


@click.command()
@click.option('--no-docker', is_flag=True, default=False,
              help="Don't start docker compose services.")
def main(no_docker):
    TestScript().main(with_docker=not no_docker)


if __name__ == "__main__":
    main()
