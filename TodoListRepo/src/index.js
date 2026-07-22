import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './app';
import AppContextProvider from './contextProivder';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
<AppContextProvider>
<App />
</AppContextProvider>
);
