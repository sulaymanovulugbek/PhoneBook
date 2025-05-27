import React, { useEffect, useState } from "react";
import { Tree } from "antd";
import EmployeesTable from "./EmployeesTable";
import axios from "axios";

// Рекурсивно строит дерево для Ant Design Tree только по OU с сотрудниками
function buildTree(data, path = []) {
  // data: { [ou_name]: { ...sub_ou }, ... , __employees__: [ ... ] }
  return Object.entries(data).map(([key, val]) => {
    if (key === "__employees__") return null; // __employees__ не OU, пропускаем
    const children = buildTree(val, [...path, key]);
    return {
      title: key, // Человеческое название корня/OU
      key: [...path, key].join("/"), // Полный путь (например, "Офис/ISD/...")
      children: children && children.length > 0 ? children : undefined,
    };
  }).filter(Boolean);
}

const DirectoryView = () => {
  const [treeData, setTreeData] = useState([]);
  const [allEmployees, setAllEmployees] = useState([]);
  const [filtered, setFiltered] = useState([]);

  useEffect(() => {
    // Загружаем дерево OU
    axios.get("/api/ou-tree/").then(r => {
      setTreeData(buildTree(r.data));
    });
    // Загружаем всех сотрудников (по умолчанию показываем всех)
    axios.get("/api/employees/").then(r => setAllEmployees(r.data));
  }, []);

  // Обработка выбора ветки дерева OU
  const onSelect = (selectedKeys) => {
    if (!selectedKeys || selectedKeys.length === 0) {
      setFiltered(allEmployees); // Если ничего не выбрано — показываем всех
      return;
    }
    // Фильтрация: показываем только сотрудников из выбранной OU/под-OU
    setFiltered(
      allEmployees.filter(
        emp => emp.ou_path && emp.ou_path.startsWith(selectedKeys[0])
      )
    );
  };

  // Если ничего не выбрано — показываем всех сотрудников
  const displayedEmployees = filtered.length ? filtered : allEmployees;

  return (
    <div style={{ display: "flex", minHeight: "90vh", background: "#f5f6fa" }}>
      <div className="ab-sidebar">
        <h3 style={{ marginBottom: 24 }}>Структура филиалов</h3>
        <Tree
          treeData={treeData}
          onSelect={onSelect}
          defaultExpandAll
        />
      </div>
      <div style={{ flex: 1 }}>
        <EmployeesTable data={displayedEmployees} />
      </div>
    </div>
  );
};

export default DirectoryView;