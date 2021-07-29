from pathlib import Path
import subprocess


DEFAULT_DOCKER_COMPOSE_FILE_NAME = 'docker-compose.yml'


def sh(cmd_line: [str]):
    subprocess.run(cmd_line, check=True)


def dir_from_file_path(pathname: str) -> Path:
    file = Path(pathname)
    return file.parent


def default_docker_file_in_same_dir(pathname: str) -> Path:
    base_dir = dir_from_file_path(pathname)
    return base_dir / DEFAULT_DOCKER_COMPOSE_FILE_NAME


class DockerCompose:

    def __init__(self, test_script_path: str):
        self._base_dir = dir_from_file_path(test_script_path)
        self._docker_file = default_docker_file_in_same_dir(test_script_path)

    def run_cmd(self, *xs):
        compose = ['docker-compose', '-f', str(self._docker_file)]
        cmd = compose + [x for x in xs]
        sh(cmd)

    def build_images(self):
        self.run_cmd('build')

    def start(self):
        self.run_cmd('up', '-d')

    def stop(self):
        self.run_cmd('down', '-v')

    def start_service(self, name: str):
        self.run_cmd('start', name)

    def stop_service(self, name: str):
        self.run_cmd('stop', name)

    def pause_service(self, name: str):
        self.run_cmd('pause', name)

    def unpause_service(self, name: str):
        self.run_cmd('unpause', name)
