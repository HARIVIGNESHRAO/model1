import React, { useEffect, useState } from 'react';
import './dashboard.css';
import { Link, useNavigate } from "react-router-dom";
import Cookies from 'js-cookie';

const Dashboard = () => {
    const [username, setUsername] = useState('');
    const [initials, setInitials] = useState('');
    const [isAuthenticated, setIsAuthenticated] = useState(true);
    const [sidebarActive, setSidebarActive] = useState(false); // New state to handle sidebar animation
    const navigate = useNavigate();

    useEffect(() => {
        const storedUsername = localStorage.getItem('username');
        const authToken = Cookies.get('authToken');

        if (!storedUsername || !authToken) {
            setIsAuthenticated(false);
        } else {
            setUsername(storedUsername);
            const initials = storedUsername.slice(0, 2).toUpperCase();
            setInitials(initials);
            setIsAuthenticated(true);
            setSidebarActive(true); // Trigger the sidebar animation
        }
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('username');
        localStorage.removeItem('authToken');
        Cookies.remove('authToken');
        navigate('../login');
    };

    if (!isAuthenticated) {
        return (
            <div className="login-message">
                <h2>Please log in to access the dashboard.</h2>
                <Link to="../login" className="login-link">Go to Login</Link>
            </div>
        );
    }

    return (
        <div className="container-1">
            <aside className={`sidebar ${sidebarActive ? 'active' : ''}`}>
                <div className="profile">
                    <div className="initials">{initials}</div>
                    <h3>Welcome Back, <span>{username}</span></h3>
                </div>
                <ul>
                    <li><Link to="../dashboard">Dashboard</Link></li>
                    <li><Link to="../text">Text to Visuals</Link></li>
                    <li><Link to="../sketch">Sketch to Reality</Link></li>
                    <li><Link to="../black">Monochrome to Color</Link></li>
                </ul>
                <button onClick={handleLogout} className="logout">Logout</button>
            </aside>

            <div className="main-content">
                <header className="dashboard-header">
                    <h2>Dashboard User</h2>
                </header>

                <section className="cards">
                    <Link to="../text" className="card">
                        <h3>From Text to Visuals</h3>
                    </Link>
                    <Link to="../sketch" className="card">
                        <h3>Sketches to Reality</h3>
                    </Link>
                    <Link to="../black" className="card">
                        <h3>From Monochrome to Multicolor</h3>
                    </Link>
                </section>
            </div>
        </div>
    );
};

export default Dashboard;
