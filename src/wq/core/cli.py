"""
CLI for the QuantumLeap work queue.
"""
import click

from wq.core.rts import start


@click.group()
def main():
    """QuantumLeap Work Queue."""
    pass


@main.command()
@click.option('--workers', '-w', type=int, default=None,
              help='How many worker processes to service the queues.')
@click.option('--burst-mode', '-b', is_flag=True, default=False,
              help='Process tasks until the queue is empty and then exit.')
@click.option('--max-tasks', type=int, default=None,
              help='Process the specified number of tasks and then exit.')
@click.option('--collect-telemetry-in', type=str, default=None,
              help='Turn on telemetry and collect task durations in the ' +
              'specified path. Directories in the given path will be ' +
              'created as needed.')
def up(workers, burst_mode, max_tasks, collect_telemetry_in):
    """Start processing tasks on the queue."""
    start(pool_size=workers, burst_mode=burst_mode, max_tasks=max_tasks,
          monitoring_dir=collect_telemetry_in)
