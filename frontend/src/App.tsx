import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import Layout from '@/components/Layout';
import HomePage from '@/pages/Home';
import LoginPage from '@/pages/Login';
import RegisterPage from '@/pages/Register';
import ChatPage from '@/pages/Chat';
import DashboardPage from '@/pages/Dashboard';
import ReportsPage from '@/pages/Reports';
import PaymentSuccessPage from '@/pages/PaymentSuccess';

function App() {
  const { isAuthenticated } = useAuthStore();

  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={isAuthenticated ? <Navigate to="/chat" /> : <LoginPage />} />
      <Route path="/register" element={isAuthenticated ? <Navigate to="/chat" /> : <RegisterPage />} />
      <Route path="/payment/success" element={<PaymentSuccessPage />} />
      <Route element={<Layout />}>
        <Route path="/chat" element={isAuthenticated ? <ChatPage /> : <Navigate to="/login" />} />
        <Route path="/dashboard" element={isAuthenticated ? <DashboardPage /> : <Navigate to="/login" />} />
        <Route path="/reports" element={isAuthenticated ? <ReportsPage /> : <Navigate to="/login" />} />
      </Route>
    </Routes>
  );
}

export default App;
