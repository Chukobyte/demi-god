import time
from typing import Coroutine, Callable, Optional, List

from crescent_api import World


class Awaitable:
    class State:
        SUSPENDED = 0
        FINISHED = 1

    def __init__(self, state: int):
        self.state = state

    def __await__(self):
        yield self


class Task:
    def __init__(self, coroutine: Coroutine):
        self.coroutine = coroutine
        self.on_close_subscribers = []
        self.valid = True
        self.current_task: "Task" = self
        self.parent_task: Optional["Task"] = None

    def __await__(self):
        yield self

    def resume(self) -> None:
        if self.valid:
            try:
                task_return_value = self.current_task.coroutine.send(None)
                if issubclass(type(task_return_value), Awaitable):
                    if task_return_value.state == Awaitable.State.FINISHED:
                        raise StopIteration
                elif issubclass(type(task_return_value), Task):
                    # Swap subtask in place
                    task_return_value.parent_task = self.current_task
                    self.current_task = task_return_value
            except StopIteration:
                if self.current_task.parent_task:
                    self.current_task = self.current_task.parent_task
                    self.resume()
                else:
                    self.valid = False

    def close(self) -> None:
        if self.valid:
            try:
                while self.current_task:
                    self.current_task.coroutine.close()
                    self.current_task.valid = False
                    self.current_task = self.current_task.parent_task
            except ValueError:
                pass


class TaskManager:
    def __init__(self, tasks: Optional[List[Task]] = None):
        if not tasks:
            tasks = []
        self.tasks: List[Task] = tasks

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        try:
            self.tasks.remove(task)
        except ValueError as e:
            pass

    def update(self) -> None:
        for task in self.tasks[:]:
            task.resume()
            if not task.valid:
                self.remove_task(task)

    def kill_tasks(self) -> None:
        for task in self.tasks[:]:
            if task.valid:
                task.close()
        self.tasks.clear()

    def get_task_amount(self) -> int:
        return len(self.tasks)

    def has_tasks(self) -> bool:
        return len(self.tasks) > 0


def co_suspend() -> Awaitable:
    return Awaitable(Awaitable.State.SUSPENDED)


def co_return() -> Awaitable:
    return Awaitable(Awaitable.State.FINISHED)


async def co_wait_until(predicate: [Callable, Coroutine]):
    async def co_wait_until_internal(_predicate: [Callable, Coroutine]):
        if isinstance(_predicate, Callable):
            while not _predicate():
                await co_suspend()
        elif isinstance(_predicate, Coroutine):
            try:
                while _predicate.send(None).state == Awaitable.State.SUSPENDED:
                    await co_suspend()
            except StopIteration:
                pass
        else:
            raise Exception(
                f"Didn't pass in a Callable or Coroutine into co_wait_until! predicate = {str(_predicate)}"
            )

    await Task(co_wait_until_internal(predicate))


# TODO: Get current time from engine function to allow for time dilation changes
async def co_wait_seconds(
    seconds: float, time_func: Callable = None, ignore_time_dilation=False
):
    async def co_wait_seconds_internal(
        _seconds: float, _time_func: Callable = None, _ignore_time_dilation=False
    ):
        if not _time_func:
            _time_func = time.time
        start_time = _time_func()
        while True:
            current_time = _time_func()
            if not _ignore_time_dilation:
                current_time *= World.get_time_dilation()
            delta = current_time - start_time
            if delta >= _seconds:
                break
            await co_suspend()

    await Task(co_wait_seconds_internal(seconds, time_func, ignore_time_dilation))


# Coroutine example
# async def example_coroutine_task():
#     # We should wrap things in try catch
#     try:
#         while True:
#             await co_suspend()
#     # Called if coroutine is cancelled externally
#     except GeneratorExit:
#         pass
#     # Clean up stuff
#     finally:
#         pass
