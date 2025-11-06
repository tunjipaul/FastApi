import { useEffect, useState } from "react";
import "./Dashboard.css";

function Dashboard() {
  const [expenses, setExpenses] = useState([]);
  const [title, setTitle] = useState("");
  const [amount, setAmount] = useState("");

  const token = localStorage.getItem("token");

  const fetchExpenses = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/expenses", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch expenses");
      const data = await res.json();
      setExpenses(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchExpenses();
  }, []);

  const addExpense = async () => {
    if (!title || !amount) return alert("Enter title and amount");
    try {
      const res = await fetch("http://127.0.0.1:8000/expenses", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ title, amount: parseFloat(amount) }),
      });
      if (!res.ok) throw new Error("Failed to add expense");
      setTitle("");
      setAmount("");
      fetchExpenses();
    } catch (err) {
      console.error(err);
    }
  };

  const deleteExpense = async (id) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/expenses/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to delete expense");
      fetchExpenses();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="dashboardContainer">
      <h2>Expense Tracker</h2>
      <div className="expenseForm">
        <input
          placeholder="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <input
          placeholder="Amount"
          type="number"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />
        <button onClick={addExpense}>Add Expense</button>
      </div>
      <ul className="expenseList">
        {expenses.map((e) => (
          <li key={e.id}>
            <span>
              {e.title}: ${e.amount}
            </span>
            <button onClick={() => deleteExpense(e.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Dashboard;
