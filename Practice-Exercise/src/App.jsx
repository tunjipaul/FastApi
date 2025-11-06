import { Routes, Route } from "react-router-dom";
import Signup from "./Components/Signup";
import Login from "./Components/Login";
import Dashboard from "./Components/Dashboard";
import "./App.css";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Signup />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/login" element={<Login />} />                                                                                                                                                                                                                                                                                                                                                                                                                                           
      <Route path="/dashboard" element={<Dashboard />} />
    </Routes>
  );
}

export default App;
