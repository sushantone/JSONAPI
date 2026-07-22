import React, { useState, useEffect } from 'react';
import auth from './msalConfig';

import TodoList from './todoList';
import HeaderBar from './headerBar';
import api from './api';
import './style.css';


function App() {

    const [accessToken, setAccessToken] = useState(null);
    const [account, setAccount] = useState(null);

    useEffect(() => {
        api.runAuthFlow().then((response) => {
            setAccount(response.account);
            setAccessToken(response.token);
        })
    }, []);

    const handleLogin = async () => {
        api.requestLogin();
    };

    return (
        <div className='app-container'>

            {!accessToken ? (
                <div className="main-screen">
                    <h1>Microsoft To Do Client</h1>
                    <button onClick={handleLogin} className='authorize-button'>Authorize</button>
                </div>

            ) : (
                <>
                    <HeaderBar {...account} token={accessToken} />
                    <TodoList token={accessToken} />
                </>
            )}
        </div>
    );
}

export default App;
