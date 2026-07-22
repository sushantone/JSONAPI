import React, { useEffect, useState, useContext } from 'react';
import api from './api';
import AppContext from './appContext';
import DueDate from './dueDate';
function TodoList({ token }) {

  const [filteredTasks, setFilteredTasks] = useState([]);
  const [allTabs, setAllTabs] = useState([]);
  const { searchText, setSearchText, selectedTab, setSelectedTab, allTasks, setRefreshRequest, refreshRequest } = useContext(AppContext);

  const showTasks = async () => {
    // api.getFilteredTasks(searchText, selectedTab).then(fetchedTasks => {
    //   setFilteredTasks(fetchedTasks||[]);
    // })
    let filtered = [];
    let _allTasks = allTasks || [];
    if (searchText) {
      filtered = _allTasks.flatMap(list => list.tasks).filter(task => task.title.toLowerCase().includes(searchText.toLowerCase()));
    } else if (selectedTab && selectedTab !== "") {
      filtered = _allTasks.find(list => list.listName === selectedTab)?.tasks || [];
    } else {
      filtered = _allTasks.flatMap(list => list.tasks);
    }
    setFilteredTasks(filtered);
  };

  const showTabs = async () => {
    let _allTasks = allTasks || [];
    const tabs = _allTasks.map(list => list.listName);
    setAllTabs(tabs);
  }

  useEffect(() => {
    showTasks();
    showTabs();
  }, [token, searchText, selectedTab, allTasks]);

  const handleTabClick = (tabName) => {
    // Scroll to the corresponding list section
    setSelectedTab(tabName);
    setSearchText('');

  }

  const editTask = (titleElement, taskElement) => {
    if (!titleElement) return;
    titleElement.contentEditable = true;
    // put cursor at the end of the text
    const range = document.createRange();
    range.selectNodeContents(titleElement);
    range.collapse(false);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    titleElement.focus();
    taskElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    const handleBlur = () => {
      titleElement.contentEditable = false;
      titleElement.removeEventListener('blur', handleBlur);
    }
    titleElement.addEventListener('blur', handleBlur);
  }
  const handleKeyDown = (e) => {
    e.preventDefault();
    let titleElement = e.target.querySelector('.task-title');

    if (e.key === 'Enter') {
      editTask(titleElement, e.target);
    }
    if (e.key === 'Escape') {
      titleElement.blur();
    }
    if (e.key === 'Tab' || e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Down' || e.key === 'Up') {
      e.preventDefault();
      const currentIndex = filteredTasks.findIndex(task => task.id === e.target.getAttribute('data-id'));
      const nextIndex = e.key === 'Down' || e.key === 'ArrowDown' || (e.key === 'Tab' && !e.shiftKey) ? currentIndex + 1 : currentIndex - 1;
      const nextTask = filteredTasks[nextIndex];
      if (nextTask) {
        e.target.blur();
        const nextElement = document.querySelector(`div[data-id='${nextTask.id}']`);
        nextElement.focus();
      }
    }
    if (e.key === "Right" || e.key === "Left" || e.key === "ArrowRight" || e.key === "ArrowLeft") {
      e.preventDefault();
      // mark complete if right arrow else set due date to today  
      const currentTask = filteredTasks.find(task => task.id === e.target.getAttribute('data-id'));
      if (currentTask) {
        if (e.key === 'Right' || e.key === 'ArrowRight') {
          api.toggleStatus(currentTask.id, allTasks, currentTask.status).then(() => {
            setRefreshRequest(!refreshRequest);
          });
        } else {
          if (!currentTask.dueDateTime) {
            const today = new Date().toISOString().split('T')[0];
            api.setDueDate(currentTask.id, today, allTasks).then(() => {
              setRefreshRequest(!refreshRequest);
            });
          } else {
            {
              currentTask.editMode = true;
              setFilteredTasks([...filteredTasks]);
            }
          }
        }
      }
    }
  }

  const handleDoubleClick = (e) => {

    let taskElement = e.target.closest('.text-block');
    if (!taskElement) return;
    let titleElement = taskElement.querySelector('.task-title');
    if (!titleElement) return;
    editTask(titleElement, taskElement);
  }

  return (
    <>
      <div style={{ display: 'flex', flexDirection: 'row-reverse', flex: 1 }}>

        <div className='tooo-container' >
          <div className='tooo-container-outer' >
            {filteredTasks.map(task => (
              <>

                <div key={task.id} data-id={task.id} tabIndex="0" style={{ display: 'flex', alignItems: 'center' }} className='text-block' onKeyDown={handleKeyDown} onDoubleClick={handleDoubleClick}>
                  {task.status === 'completed' ? (
                    <img src="images/done.svg" className='img-icon' />
                  ) : (task.dueDateTime ? (
                    <DueDate dueDateTime={task.dueDateTime} taskId={task.id} editMode={task.editMode} setEditMode={delete task.editMode} />
                  ) : <></>)}
                  <div className='task-title'>{task.title}</div>

                  <div className='task-toolbar'>
                    <div title={`Set Due Date\nOnce Left Arrow for today, \nTwice left arrow for custom`} onClick={() => {
                      // Set Due Date
                    }}>
                      <img src="images/today.svg" className='img-icon' />
                    </div>
                    <div title={`Toggle Status\nUse right arrow to toggle betweem completed and not started`} onClick={() => {
                      // Toggle Status
                    }}>
                      <img src="images/mark-done.svg" className='img-icon' />
                    </div>
                  </div>
                </div>
              </>
            ))}
          </div>
        </div>
        <div className='tab-bar'>
          {allTabs.map(tab => (
            <>
              <button className={`tab-item ${selectedTab === tab ? 'active-tab' : ''}`} onClick={() => handleTabClick(tab)}>{tab}</button>
            </>
          ))}
        </div>
      </div>
    </>
  );
}

export default TodoList;
