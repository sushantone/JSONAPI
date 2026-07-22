import React, { useState } from 'react';
import api from './api';
import { useContext } from 'react';
import AppContext from './appContext';

const DueDate = ({ dueDateTime, taskId, editMode, setEditMode}) => {
  const dueDate = new Date(dueDateTime.dateTime);
  const now = new Date();
  const isOverdue = dueDate < now && dueDate.toDateString() !== now.toDateString();
  const isToday = dueDate.toDateString() === now.toDateString();
  const { allTasks, setRefreshRequest, refreshRequest } = useContext(AppContext);

  if (editMode) {
    return (
      <input type="date" value={dueDate.toISOString().split('T')[0]} onChange={(e) => {
        const newDate = new Date(e.target.value);
        api.setDueDate(taskId, newDate, allTasks).then(() => {
          setRefreshRequest(!refreshRequest);
        });
      }} onBlur={() => setEditMode(false)} />
    );
  }

  return (
    <span className={`due-date ${isOverdue ? 'overdue' : ''} ${isToday ? 'today' : ''}`} title={`Due on ${dueDate.toLocaleDateString()} \nClick to change the due date`} onClick={() => setEditMode(true)}>
      {dueDate.getDate()}
    </span>
  );
};

export default DueDate;
