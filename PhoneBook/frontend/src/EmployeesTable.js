import React, { useEffect, useState } from "react";
import { Table, Tag, Input } from "antd";

const columns = [
  { title: "ФИО", dataIndex: "name", key: "name" },
  { title: "Внутренний номер", dataIndex: "phone", key: "phone" },
  { title: "Сотовый номер", dataIndex: "mobile", key: "mobile" },
  { title: "Почта", dataIndex: "email", key: "email" },
  { title: "Должность", dataIndex: "title", key: "title" },
  { title: "Отдел", dataIndex: "department", key: "department" },
  {
    title: "Статус",
    dataIndex: "is_enabled",
    key: "is_enabled",
    render: (is_enabled) =>
      is_enabled ? <Tag color="green">Активен</Tag> : <Tag color="red">Отключен</Tag>,
  },
];

const EmployeesTable = ({ data }) => {
  const [search, setSearch] = useState("");
  const [filtered, setFiltered] = useState(data);

  useEffect(() => {
    setFiltered(data);
  }, [data]);

  useEffect(() => {
    if (!search) {
      setFiltered(data);
      return;
    }
    const q = search.toLowerCase();
    setFiltered(
      data.filter(
        (item) =>
          (item.name && item.name.toLowerCase().includes(q)) ||
          (item.phone && item.phone.toLowerCase().includes(q)) ||
          (item.mobile && item.mobile.toLowerCase().includes(q)) ||
          (item.email && item.email.toLowerCase().includes(q)) ||
          (item.title && item.title.toLowerCase().includes(q)) ||
          (item.department && item.department.toLowerCase().includes(q))
      )
    );
  }, [search, data]);

  return (
    <div>
      <Input
        placeholder="Поиск по всем полям (ФИО, номер, отдел, должность...)"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        style={{ width: 400, marginBottom: 16 }}
        allowClear
      />
      <Table
        columns={columns}
        dataSource={filtered}
        rowKey="email"
        pagination={{ pageSize: 20 }}
      />
    </div>
  );
};

export default EmployeesTable;