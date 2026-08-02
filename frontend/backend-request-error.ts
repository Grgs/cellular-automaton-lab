export interface BackendErrorDetails {
    status?: number;
    code?: string;
    limit?: number;
    estimatedCells?: number;
    actualCells?: number;
}

/** Structured public error shared by HTTP and standalone worker adapters. */
export class BackendRequestError extends Error {
    readonly status: number | undefined;
    readonly code: string | undefined;
    readonly limit: number | undefined;
    readonly estimatedCells: number | undefined;
    readonly actualCells: number | undefined;

    constructor(detail: string, details: BackendErrorDetails = {}) {
        super(
            details.status === undefined
                ? detail
                : detail
                  ? `Request failed: ${details.status} — ${detail}`
                  : `Request failed: ${details.status}`,
        );
        this.name = "BackendRequestError";
        this.status = details.status;
        this.code = details.code;
        this.limit = details.limit;
        this.estimatedCells = details.estimatedCells;
        this.actualCells = details.actualCells;
    }
}
