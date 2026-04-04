import type { MutationRunner, MutationRunnerOptions } from "./types/controller.js";

async function executeTask<T>(
    task: () => Promise<T>,
    { onError, onRecover }: MutationRunnerOptions = {},
): Promise<T> {
    try {
        return await task();
    } catch (error) {
        onError?.(error);
        if (typeof onRecover === "function") {
            await onRecover(error);
        }
        throw error;
    }
}

export function createMutationRunner(): MutationRunner {
    let mutationQueue: Promise<void> = Promise.resolve();

    function run<T>(task: () => Promise<T>, options: MutationRunnerOptions = {}): Promise<T> {
        const scheduled = mutationQueue.then(
            () => executeTask(task, options),
            () => executeTask(task, options),
        );
        mutationQueue = scheduled.then(
            () => undefined,
            () => undefined,
        );
        return scheduled;
    }

    function dispose(): void {
        mutationQueue = Promise.resolve();
    }

    return {
        run,
        dispose,
    };
}
