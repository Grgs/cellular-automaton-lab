import type { PersistedSimulationSnapshotV5 } from "../types/domain.js";
import type { SimulationStatePersistence } from "../types/controller.js";

const DATABASE_NAME = "cellular-automaton-lab-standalone";
const OBJECT_STORE_NAME = "runtime";
const SNAPSHOT_KEY = "snapshot-v5";
const LOCAL_STORAGE_KEY = "cellular-automaton-lab-standalone-state-v5";

function openDatabase(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
        const request = window.indexedDB.open(DATABASE_NAME, 1);
        request.onupgradeneeded = () => {
            const database = request.result;
            if (!database.objectStoreNames.contains(OBJECT_STORE_NAME)) {
                database.createObjectStore(OBJECT_STORE_NAME);
            }
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error ?? new Error("Failed to open IndexedDB."));
    });
}

function transactionDone(transaction: IDBTransaction): Promise<void> {
    return new Promise((resolve, reject) => {
        transaction.oncomplete = () => resolve();
        transaction.onerror = () => reject(transaction.error ?? new Error("IndexedDB transaction failed."));
        transaction.onabort = () => reject(transaction.error ?? new Error("IndexedDB transaction aborted."));
    });
}

async function createIndexedDbPersistence(): Promise<SimulationStatePersistence> {
    const database = await openDatabase();
    return {
        async load() {
            const transaction = database.transaction(OBJECT_STORE_NAME, "readonly");
            const store = transaction.objectStore(OBJECT_STORE_NAME);
            const request = store.get(SNAPSHOT_KEY);
            const value = await new Promise<PersistedSimulationSnapshotV5 | null>((resolve, reject) => {
                request.onsuccess = () => resolve((request.result as PersistedSimulationSnapshotV5 | undefined) ?? null);
                request.onerror = () => reject(request.error ?? new Error("IndexedDB read failed."));
            });
            await transactionDone(transaction);
            return value;
        },
        async save(snapshot) {
            const transaction = database.transaction(OBJECT_STORE_NAME, "readwrite");
            transaction.objectStore(OBJECT_STORE_NAME).put(snapshot, SNAPSHOT_KEY);
            await transactionDone(transaction);
        },
    };
}

function createLocalStoragePersistence(): SimulationStatePersistence {
    return {
        async load() {
            const raw = window.localStorage.getItem(LOCAL_STORAGE_KEY);
            if (!raw) {
                return null;
            }
            return JSON.parse(raw) as PersistedSimulationSnapshotV5;
        },
        async save(snapshot) {
            window.localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(snapshot));
        },
    };
}

export async function createSimulationStatePersistence(): Promise<SimulationStatePersistence> {
    if (typeof window.indexedDB !== "undefined") {
        try {
            return await createIndexedDbPersistence();
        } catch (error) {
            console.warn("Falling back to localStorage persistence for standalone runtime.", error);
        }
    }
    return createLocalStoragePersistence();
}
