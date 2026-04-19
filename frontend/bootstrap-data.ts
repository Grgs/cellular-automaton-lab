import type {
    AppBootstrapData,
    BootstrappedAperiodicFamilyDefinition,
    BootstrappedFrontendDefaults,
    BootstrappedTopologyDefinition,
} from "./types/domain.js";
import type { PeriodicFaceTilingDescriptor } from "./types/rendering.js";

function cloneBootstrapData(payload: AppBootstrapData): AppBootstrapData {
    return {
        app_defaults: structuredClone(payload.app_defaults),
        topology_catalog: payload.topology_catalog.map((entry) => ({ ...entry })),
        periodic_face_tilings: payload.periodic_face_tilings.map((entry) => ({ ...entry })),
        aperiodic_families: payload.aperiodic_families.map((entry) => ({
            ...entry,
            implementation_status: entry.implementation_status,
            promotion_blocker: entry.promotion_blocker,
            public_cell_kinds: [...entry.public_cell_kinds],
        })),
        server_meta: { ...payload.server_meta },
        snapshot_version: Number(payload.snapshot_version),
    };
}

function requireObject(value: unknown, context: string): Record<string, unknown> {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        throw new Error(`${context} is invalid.`);
    }
    return value as Record<string, unknown>;
}

function normalizeBootstrapData(payload: unknown): AppBootstrapData {
    const root = requireObject(payload, "Bootstrap payload");
    const defaults = root.app_defaults as BootstrappedFrontendDefaults | undefined;
    const topologies = root.topology_catalog as ReadonlyArray<BootstrappedTopologyDefinition> | undefined;
    const periodicFaceTilings = root.periodic_face_tilings as ReadonlyArray<PeriodicFaceTilingDescriptor> | undefined;
    const aperiodicFamilies = root.aperiodic_families as ReadonlyArray<BootstrappedAperiodicFamilyDefinition> | undefined;
    const serverMeta = root.server_meta as { app_name?: string } | undefined;
    const snapshotVersion = Number(root.snapshot_version);
    if (
        !defaults
        || !Array.isArray(topologies)
        || !Array.isArray(periodicFaceTilings)
        || !Array.isArray(aperiodicFamilies)
        || !serverMeta?.app_name
    ) {
        throw new Error("Bootstrap payload is invalid.");
    }
    if (!Number.isFinite(snapshotVersion)) {
        throw new Error("Bootstrap payload snapshot version is invalid.");
    }
    return cloneBootstrapData({
        app_defaults: defaults,
        topology_catalog: topologies,
        periodic_face_tilings: periodicFaceTilings,
        aperiodic_families: aperiodicFamilies,
        server_meta: { app_name: String(serverMeta.app_name) },
        snapshot_version: snapshotVersion,
    });
}

export function installBootstrapData(payload: AppBootstrapData): AppBootstrapData {
    const normalized = cloneBootstrapData(payload);
    window.APP_DEFAULTS = structuredClone(normalized.app_defaults);
    window.APP_TOPOLOGIES = normalized.topology_catalog;
    window.APP_PERIODIC_FACE_TILINGS = normalized.periodic_face_tilings;
    window.APP_APERIODIC_FAMILIES = normalized.aperiodic_families;
    return normalized;
}

export function bootstrapDataFromWindow(): AppBootstrapData {
    return installBootstrapData({
        app_defaults: window.APP_DEFAULTS,
        topology_catalog: window.APP_TOPOLOGIES,
        periodic_face_tilings: window.APP_PERIODIC_FACE_TILINGS,
        aperiodic_families: window.APP_APERIODIC_FAMILIES,
        server_meta: { app_name: "cellular-automaton-lab" },
        snapshot_version: 5,
    });
}

export async function fetchBootstrapData(url: string): Promise<AppBootstrapData> {
    const response = await fetch(url, {
        headers: { "Content-Type": "application/json" },
    });
    if (!response.ok) {
        throw new Error(`Bootstrap request failed: ${response.status}`);
    }
    return normalizeBootstrapData(await response.json());
}
