from wq.core.cli import main

if __name__ == '__main__':
    main()


# Examples (run from src dir)

# $ python wq
# Usage: wq [OPTIONS] COMMAND [ARGS]...
#
# QuantumLeap Work Queue.
#
# Options:
# --help  Show this message and exit.
#
# Commands:
# up  Start processing tasks on the queue.

# $ python wq up --help
# Usage: wq up [OPTIONS]
#
# Start processing tasks on the queue.
#
# Options:
# -w, --workers INTEGER  How many worker processes to service the queues.
# -b, --burst-mode       Process tasks until the queue is empty and then exit.
# --max-tasks INTEGER    Process the specified number of tasks and then exit.
# --help                 Show this message and exit.

# $ python wq up
# basically the same as running: `rq worker`

# $ python wq up -w 2
# multiple workers run tasks in parallel; experimental, only use for testing.
