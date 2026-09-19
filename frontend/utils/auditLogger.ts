// frontend/utils/auditLogger.ts
export interface EventVerification {
  eventId: string;
  action: string;
  dispatchedAt: number;
  acknowledgedAt?: number;
  success: boolean;
}

class ActionAuditor {
  private pendingActions = new Map<string, (receipt: any) => void>();

  public trackAction(actionName: string, payload: any, wsSend: (data: any) => void): Promise<boolean> {
    const correlationId = `${actionName}-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
    
    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        if (this.pendingActions.has(correlationId)) {
          console.error(`🚨 [AUDIT FAILED] Keine Antwort vom Backend für: ${actionName} (ID: ${correlationId})`);
          this.pendingActions.delete(correlationId);
          resolve(false);
        }
      }, 3000); // 3 Sekunden Timeout

      this.pendingActions.set(correlationId, (receipt) => {
        clearTimeout(timeout);
        console.log(`✅ [AUDIT SUCCESS] ${actionName} erfolgreich registriert:`, receipt);
        resolve(true);
      });

      // Event mit Correlation-ID rausschicken
      wsSend({
        type: "ACTION_DISPATCH",
        correlationId,
        action: actionName,
        payload
      });
    });
  }

  public handleBackendAck(data: { correlationId: string; status: string; result?: any }) {
    if (this.pendingActions.has(data.correlationId)) {
      const callback = this.pendingActions.get(data.correlationId);
      if (callback) callback(data);
      this.pendingActions.delete(data.correlationId);
    }
  }
}

export const auditor = new ActionAuditor();
