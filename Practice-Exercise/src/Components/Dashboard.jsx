import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Dashboard.css";

function Dashboard() {
  const [expenses, setExpenses] = useState([]);
  const [title, setTitle] = useState("");
  const [amount, setAmount] = useState("");
  const [editingId, setEditingId] = useState(null);
  const navigate = useNavigate();

  const token = localStorage.getItem("token");

  const fetchExpenses = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/expenses", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setExpenses(data);
    } catch {
      console.error("Failed to fetch expenses");
    }
  };

  useEffect(() => {
    if (!token) {
      navigate("/login");
      return;
    }
    fetchExpenses();
  }, []);

  const resetForm = () => {
    setTitle("");
    setAmount("");
    setEditingId(null);
  };

  const handleSubmit = async () => {
    if (!title || !amount) return alert("Enter title and amount");

    try {
      if (editingId) {
        const res = await fetch(`http://127.0.0.1:8000/expenses/${editingId}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ title, amount: parseFloat(amount) }),
        });
        if (!res.ok) throw new Error();
      } else {
        const res = await fetch("http://127.0.0.1:8000/expenses", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ title, amount: parseFloat(amount) }),
        });
        if (!res.ok) throw new Error();
      }

      resetForm();
      fetchExpenses();
    } catch {
      console.error("Failed to save expense");
    }
  };

  const editExpense = (exp) => {
    setTitle(exp.title);
    setAmount(exp.amount);
    setEditingId(exp.id);
  };

  const cancelEdit = () => resetForm();

  const deleteExpense = async (id) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/expenses/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error();
      fetchExpenses();
    } catch {
      console.error("Failed to delete expense");
    }
  };

  
  const total = expenses.reduce((sum, exp) => sum + exp.amount, 0);

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
          type="number"
          min="0"
          placeholder="Amount"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />
        <button onClick={handleSubmit}>
          {editingId ? "Update" : "Add Expense"}
        </button>
        {editingId && <button onClick={cancelEdit}>Cancel</button>}
      </div>

      <h3 className="totalExpenses">Total: N{total.toFixed(2)}</h3>

      <ul className="expenseList">
        {expenses.map((exp) => (
          <li key={exp.id}>
            <span>
              {exp.title}: N{exp.amount}
            </span>
            <div>
              <button onClick={() => editExpense(exp)}>Edit</button>
              <button onClick={() => deleteExpense(exp.id)}>Delete</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Dashboard;
