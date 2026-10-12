# Agent-Exchange JSON Schema

Jeder Task muss als JSON-Datei atomar (.tmp -> .json) im `inbox/` Ordner abgelegt werden. Dadurch vermeiden wir Datei-Sperren, wenn KIs gleichzeitig schreiben.

```json
{
  "task_id": "eindeutige_id_001",
  "sender": "gemini-cli",
  "receiver": "webjarvis",
  "action": "analyze_log",
  "payload_path": "agent_exchange/payloads/data.txt",
  "status": "pending"
}
```
