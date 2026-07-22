// SearchProvider.js
import React, { useState } from 'react';
import AppContext from './appContext';

const AppContextProvider = ({ children }) => {
  const [searchText, setSearchText] = useState('');
  const [selectedTab, setSelectedTab] = useState('');
  const [allTasks, setAllTasks] = useState([]);
  const [refreshRequest, setRefreshRequest] = useState(false);

  const contextValue = {
      searchText, setSearchText, 
      selectedTab, setSelectedTab, 
      allTasks, setAllTasks,
      refreshRequest, setRefreshRequest,
  };
  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
};

export default AppContextProvider;
