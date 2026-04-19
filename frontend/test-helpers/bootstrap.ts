import bootstrapFixtureData from "../test-fixtures/bootstrap-data.json";
import type {
    AppBootstrapData,
    BootstrappedAperiodicFamilyDefinition,
    BootstrappedTopologyDefinition,
} from "../types/domain.js";

function cloneBootstrapFixture(): AppBootstrapData {
    return structuredClone(bootstrapFixtureData as AppBootstrapData);
}

export function getFixtureTopologyDefinition(tilingFamily: string): BootstrappedTopologyDefinition {
    const definition = cloneBootstrapFixture().topology_catalog.find(
        (entry) => entry.tiling_family === tilingFamily,
    );
    if (!definition) {
        throw new Error(`Missing bootstrap topology fixture for "${tilingFamily}".`);
    }
    return definition;
}

export function getFixtureAperiodicFamilyDefinition(
    tilingFamily: string,
): BootstrappedAperiodicFamilyDefinition {
    const definition = cloneBootstrapFixture().aperiodic_families.find(
        (entry) => entry.tiling_family === tilingFamily,
    );
    if (!definition) {
        throw new Error(`Missing bootstrap aperiodic fixture for "${tilingFamily}".`);
    }
    return definition;
}

export function installFrontendGlobals(): void {
    const payload = cloneBootstrapFixture();
    window.APP_DEFAULTS = payload.app_defaults;
    window.APP_TOPOLOGIES = payload.topology_catalog;
    window.APP_PERIODIC_FACE_TILINGS = payload.periodic_face_tilings;
    window.APP_APERIODIC_FAMILIES = payload.aperiodic_families;
    window.__appReady = true;
}
