import type { CompareOperationKind } from "./compare-workspace-store.js";

export interface CompareOperationTicket {
    readonly id: number;
    readonly revision: number;
    readonly kind: CompareOperationKind;
}

export interface CompareOperationCoordinator {
    begin(kind: CompareOperationKind): CompareOperationTicket;
    owns(ticket: CompareOperationTicket): boolean;
    finish(ticket: CompareOperationTicket): boolean;
    cancel(kind: CompareOperationKind): boolean;
    invalidate(): boolean;
    dispose(): void;
}

interface CompareOperationCoordinatorOptions {
    onBusyChange?(busy: boolean): void;
}

/**
 * Owns the visible request bracket independently from transport cancellation.
 * A backend may ignore AbortSignal and settle later; ticket ownership keeps
 * that stale completion from publishing or clearing a newer operation's UI.
 */
export function createCompareOperationCoordinator({
    onBusyChange = () => {},
}: CompareOperationCoordinatorOptions = {}): CompareOperationCoordinator {
    let sequence = 0;
    let revision = 0;
    let active: CompareOperationTicket | null = null;
    let disposed = false;

    function settle(): boolean {
        if (!active) {
            return false;
        }
        active = null;
        onBusyChange(false);
        return true;
    }

    function owns(ticket: CompareOperationTicket): boolean {
        return !disposed && ticket.revision === revision && active?.id === ticket.id;
    }

    return {
        begin(kind): CompareOperationTicket {
            const ticket = { id: ++sequence, revision, kind };
            if (!disposed) {
                active = ticket;
                onBusyChange(true);
            }
            return ticket;
        },
        owns,
        finish(ticket): boolean {
            return owns(ticket) ? settle() : false;
        },
        cancel(kind): boolean {
            return active?.kind === kind ? settle() : false;
        },
        invalidate(): boolean {
            revision += 1;
            return settle();
        },
        dispose(): void {
            if (disposed) {
                return;
            }
            disposed = true;
            revision += 1;
            settle();
        },
    };
}
