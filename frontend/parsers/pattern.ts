import {
    describeTopologySpec,
    getTopologyDefinition,
} from "../topology-catalog.js";
import { isPlainObject } from "../runtime-validation.js";
import type { ParsedPattern, TopologySpec } from "../types/domain.js";

const PATTERN_FORMAT = "cellular-automaton-lab-pattern";
const PATTERN_VERSION = 5;

export class PatternValidationError extends Error {}

interface PatternPayloadCandidate {
    format?: unknown;
    version?: unknown;
    topology_spec?: unknown;
    rule?: unknown;
    cells_by_id?: unknown;
}

function ensurePatternObject(value: unknown): PatternPayloadCandidate {
    if (!isPlainObject(value)) {
        throw new PatternValidationError("Pattern file must contain a JSON object.");
    }
    return value;
}

function parsePositiveInteger(value: unknown, fieldName: string): number {
    const parsed = Number(value);
    if (!Number.isInteger(parsed) || parsed <= 0) {
        throw new PatternValidationError(`Pattern field '${fieldName}' must be a positive integer.`);
    }
    return parsed;
}

function parseNonNegativeInteger(value: unknown, fieldName: string): number {
    const parsed = Number(value);
    if (!Number.isInteger(parsed) || parsed < 0) {
        throw new PatternValidationError(`Pattern field '${fieldName}' must be a non-negative integer.`);
    }
    return parsed;
}

function parseRuleName(value: unknown): string {
    if (typeof value !== "string" || value.trim() === "") {
        throw new PatternValidationError("Pattern field 'rule' must be a non-empty string.");
    }
    return value.trim();
}

function parseTopologySpec(value: unknown): TopologySpec {
    if (!isPlainObject(value)) {
        throw new PatternValidationError("Pattern field 'topology_spec' must be an object.");
    }
    const normalized = describeTopologySpec(value);
    if (!getTopologyDefinition(normalized.tiling_family)) {
        throw new PatternValidationError("Pattern field 'topology_spec.tiling_family' is unsupported.");
    }
    return normalized;
}

function parseCellsById(cellsById: unknown): Record<string, number> {
    if (!isPlainObject(cellsById)) {
        throw new PatternValidationError("Pattern field 'cells_by_id' must be an object.");
    }

    const normalizedCellsById: Record<string, number> = {};
    Object.entries(cellsById).forEach(([id, rawState]) => {
        const normalizedId = typeof id === "string" ? id.trim() : "";
        if (!normalizedId) {
            throw new PatternValidationError("Pattern field 'cells_by_id' must only contain non-empty string keys.");
        }
        const state = Number(rawState);
        if (!Number.isInteger(state)) {
            throw new PatternValidationError(`Pattern cell '${normalizedId}' must include an integer state.`);
        }
        if (state !== 0) {
            normalizedCellsById[normalizedId] = state;
        }
    });
    return normalizedCellsById;
}

export function parsePatternText(text: string): ParsedPattern {
    let parsed: unknown;
    try {
        parsed = JSON.parse(text);
    } catch {
        throw new PatternValidationError("Pattern file must contain valid JSON.");
    }

    const pattern = ensurePatternObject(parsed);
    if (pattern.format !== PATTERN_FORMAT) {
        throw new PatternValidationError("Pattern file format is not supported.");
    }
    if (Number(pattern.version) !== PATTERN_VERSION) {
        throw new PatternValidationError("Pattern file version is not supported.");
    }

    const topologySpec = parseTopologySpec(pattern.topology_spec);
    const normalizedPattern: ParsedPattern = {
        format: PATTERN_FORMAT,
        version: PATTERN_VERSION,
        topologySpec: {
            ...topologySpec,
            width: parsePositiveInteger(topologySpec.width, "topology_spec.width"),
            height: parsePositiveInteger(topologySpec.height, "topology_spec.height"),
            patch_depth: parseNonNegativeInteger(topologySpec.patch_depth, "topology_spec.patch_depth"),
        },
        rule: parseRuleName(pattern.rule),
        cellsById: parseCellsById(pattern.cells_by_id),
        patchDepth: 0,
        width: 0,
        height: 0,
    };
    normalizedPattern.patchDepth = normalizedPattern.topologySpec.patch_depth;
    normalizedPattern.width = normalizedPattern.topologySpec.width;
    normalizedPattern.height = normalizedPattern.topologySpec.height;
    return normalizedPattern;
}
