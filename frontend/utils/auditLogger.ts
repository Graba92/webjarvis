// frontend/utils/auditLogger.ts
export interface EventVerification {
  eventId: string;
  action: string;
  dispatchedAt: number;
  acknowledgedAt?: number;
  success: boolean;
}

interface PendingAction {
  resolve: (success: boolean) => void;
  actionName: string;
  timer: NodeJS.Timeout;
  createdAt: number;
}

class ActionAuditor {
  private pendingActions = new Map<string, PendingAction>();

  public trackAction(
    actionName: string,
    payload: any,
    wsSend: (data: any) => void,
    timeoutMs: number = 10000
  ): Promise<boolean> {
    const correlationId = `${actionName}-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;

    return new Promise((resolve) => {
      const timer = setTimeout(() => {
        if (this.pendingActions.has(correlationId)) {
          console.warn(`⚠️ [AUDIT TIMEOUT] Backend-Quittierung für '${actionName}' verzögert (> ${timeoutMs}ms, ID: ${correlationId}). Live-Sync übernimmt.`);
          this.pendingActions.delete(correlationId);
          resolve(false);
        }
      }, timeoutMs);

      this.pendingActions.set(correlationId, {
        resolve,
        actionName,
        timer,
        createdAt: Date.now()
      });

      // Event mit Correlation-ID rausschicken
      try {
        wsSend({
          type: "ACTION_DISPATCH",
          correlationId,
          action: actionName,
          payload
        });
      } catch (err) {
        clearTimeout(timer);
        this.pendingActions.delete(correlationId);
        console.warn(`⚠️ [AUDIT DISPATCH ERROR] Senden von '${actionName}' fehlgeschlagen:`, err);
        resolve(false);
      }
    });
  }

  public handleBackendAck(data: { correlationId: string; status: string; result?: any }) {
    if (this.pendingActions.has(data.correlationId)) {
      const pending = this.pendingActions.get(data.correlationId)!;
      clearTimeout(pending.timer);
      this.pendingActions.delete(data.correlationId);
      const isSuccess = data.status === "PROCESSED" || data.status === "OK" || data.status === "SUCCESS";
      console.log(`✅ [AUDIT SUCCESS] ${pending.actionName} quittiert (${data.status}):`, data.result);
      pending.resolve(isSuccess);
    } else {
      console.log(`ℹ️ [AUDIT LATE ACK] Nachträgliche Quittierung für ID: ${data.correlationId} empfangen.`);
    }
  }
}

export const auditor = new ActionAuditor();
