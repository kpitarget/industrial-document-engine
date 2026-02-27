import { useState } from "react";

import { QueuePage } from "./pages/QueuePage";
import { RecordDetailPage } from "./pages/RecordDetailPage";

export default function App() {
  const [selectedRecordId, setSelectedRecordId] = useState<string | null>(null);

  return (
    <main className="app-shell">
      <header className="app-header">
        <span className="app-brand-mark">MW SERVICES</span>
        <div>
          <h1>Operations Review Dashboard</h1>
          <p>Employee document reconciliation, approvals, and exception management.</p>
        </div>
      </header>

      <section className="app-grid">
        <QueuePage selectedRecordId={selectedRecordId} onSelectRecord={setSelectedRecordId} />
        <RecordDetailPage recordId={selectedRecordId} onCloseRecord={() => setSelectedRecordId(null)} />
      </section>
    </main>
  );
}
