// frontend/src/pages/Home.jsx
import { useState } from "react";
import TableList from "../components/TableList";
import TableDetail from "../components/TableDetail";
import "./Home.css";

export default function Home() {
  const [selectedTable, setSelectedTable] = useState(null);

  return (
    <div className="app-container">
      <div className="app-content">
        <aside className="sidebar">
          <TableList 
            onSelect={setSelectedTable} 
            selectedTable={selectedTable} 
          />
        </aside>

        <main className="main-content">
          <TableDetail tableId={selectedTable} />
        </main>
      </div>

      <footer className="app-footer">
        <p> {new Date().getFullYear()} Gold Data Catalog</p>
      </footer>
    </div>
  );
}