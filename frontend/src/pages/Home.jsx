// src/pages/Home.jsx
import { useState } from "react";
import TableList from "../components/TableList";
import TableDetail from "../components/TableDetail";
import "./Home.css";

export default function Home() {
  const [selectedTable, setSelectedTable] = useState(null);

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Gold Data Catalog</h1>
        <p className="app-description">
          Explore and manage your data tables and their metadata
        </p>
      </header>

      <div className="app-content">
        <aside className="sidebar">
          <TableList 
            onSelect={setSelectedTable} 
            selectedTable={selectedTable} 
          />
        </aside>

        <main className="main-content">
          <TableDetail tableName={selectedTable} />
        </main>
      </div>

      <footer className="app-footer">
        <p>© {new Date().getFullYear()} Gold Data Catalog</p>
      </footer>
    </div>
  );
}
