import React from "react";
import DirectoryView from "./DirectoryView";
import "./App.css";
import logo from "./logo-cont.png"; // Путь к вашему лого

function App() {
  return (
    <div className="ab-root">
      <header className="ab-header">
        <img src={logo} alt="ApexBank Logo" className="ab-logo" />
        <span className="ab-title">Справочник сотрудников</span>
      </header>
      <main className="ab-main">
        <DirectoryView />
      </main>
      <footer className="ab-footer">
        <span>© {new Date().getFullYear()} ApexBank</span>
      </footer>
    </div>
  );
}

export default App;